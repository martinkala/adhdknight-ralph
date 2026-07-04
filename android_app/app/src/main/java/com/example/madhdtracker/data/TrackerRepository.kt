package com.example.madhdtracker.data

import com.example.madhdtracker.domain.logic.AsrsRecalibrator
import com.example.madhdtracker.domain.logic.IndexCalculator
import com.example.madhdtracker.domain.logic.WeeklySummaryCalculator
import com.example.madhdtracker.domain.model.AppConfig
import com.example.madhdtracker.domain.model.EntityConfig
import com.example.madhdtracker.domain.model.EntityNode
import com.example.madhdtracker.notifications.NotificationRules
import java.time.LocalDate
import java.time.OffsetDateTime
import java.util.Locale

class TrackerRepository(
    private val db: AppDatabase,
    private val appConfig: AppConfig,
    val elementConfig: EntityConfig
) {
    suspend fun seedDefaultWeightsIfEmpty() {
        val existing = db.weightsDao().getAll()
        if (existing.isNotEmpty()) return

        val now = OffsetDateTime.now().toString()
        val weights = elementConfig.trackableNodes.map { (key, node) ->
            WeightEntity(
                elementKey = key,
                weightDefault = node.weight,
                weightPersonal = null,
                updatedAt = now
            )
        }
        db.weightsDao().upsertAll(weights)
    }

    suspend fun getOrCreateDay(date: String): EventDayEntity {
        val existing = db.eventDayDao().getByDate(date)
        if (existing != null) return existing
        val now = OffsetDateTime.now().toString()
        val id = db.eventDayDao().upsert(
            EventDayEntity(date = date, createdAt = now, updatedAt = now)
        )
        return EventDayEntity(id = id, date = date, createdAt = now, updatedAt = now)
    }

    suspend fun saveDay(
        dayId: Long,
        date: String,
        updatedAt: String,
        values: List<EventValueEntity>,
        satisfaction: SatisfactionEntity
    ) {
        val existing = db.eventDayDao().getByDate(date)
        val createdAt = existing?.createdAt ?: updatedAt
        db.eventDayDao().upsert(
            EventDayEntity(id = dayId, date = date, createdAt = createdAt, updatedAt = updatedAt)
        )
        db.eventValueDao().deleteByDay(dayId)
        db.eventValueDao().upsertAll(values)
        db.satisfactionDao().upsert(satisfaction)
    }

    suspend fun getActiveElementKeys(): Set<String> {
        val overrides = db.userElementOverrideDao().getAll()
        val userElements = db.userElementDao().getAll().filter { it.isActive }
        val userKeys = userElements.map { it.key }.toSet()
        return computeActiveKeys(elementConfig, overrides) + userKeys
    }

    suspend fun setElementActive(key: String, active: Boolean) {
        db.userElementOverrideDao().upsert(UserElementOverrideEntity(elementKey = key, isActive = active))
    }

    suspend fun computeAndSaveDailyIndex(dayId: Long) {
        val values = db.eventValueDao().getByDay(dayId)
        val weights = db.weightsDao().getAll().associateBy { it.elementKey }
        if (values.isEmpty()) return

        val activeKeys = getActiveElementKeys()
        val activeValues = values.filter { it.elementKey in activeKeys }
        if (activeValues.isEmpty()) return

        val effectiveConfig = getEffectiveEntityConfig()
        val indexValue = IndexCalculator.computeDailyIndexGrouped(activeValues, effectiveConfig, activeKeys) ?: return
        val positiveIndex = IndexCalculator.computePositiveIndex(activeValues, weights, effectiveConfig.positiveKeys)
        val negativeIndex = IndexCalculator.computeNegativeIndex(activeValues, weights, effectiveConfig.negativeKeys)
        db.indexDao().deleteByDayId(dayId)
        db.indexDao().insertDaily(
            IndexDailyEntity(
                eventDayId = dayId,
                indexValue = indexValue,
                positiveIndex = positiveIndex,
                negativeIndex = negativeIndex
            )
        )
    }

    suspend fun getLatestSubIndices(): Pair<Double?, Double?> {
        val latest = db.indexDao().getLatestDaily() ?: return Pair(null, null)
        return Pair(latest.positiveIndex, latest.negativeIndex)
    }

    suspend fun getLatestDualIndexSeries(limit: Int): List<DailySubIndexRow> =
        db.indexDao().getLatestDualWithDate(limit)

    suspend fun getLatestDailyIndex(): Double? = db.indexDao().getLatestDaily()?.indexValue

    suspend fun getLatestSatisfaction(): Int? = db.satisfactionDao().getLatest()?.valueScale

    suspend fun getLatestCompletionCounts(): Pair<Int, Int>? {
        val day = db.eventDayDao().getLatest() ?: return null
        val values = db.eventValueDao().getByDay(day.id)
        if (values.isEmpty()) return null
        val filtered = values.filter { it.elementKey != "overall_feeling" }
        val completed = filtered.count { it.valueEffective > 0.0 }
        return completed to filtered.size
    }

    suspend fun getLatestDailySeries(limit: Int): List<DailyIndexRow> =
        db.indexDao().getLatestDailyWithDate(limit)

    suspend fun computeAndSaveWeeklyIndex() {
        val recent = db.indexDao().getLatestDailyWithDate(7)
        if (recent.isEmpty()) return
        val avg = WeeklySummaryCalculator.average(recent) ?: return
        val weekStart = WeeklySummaryCalculator.weekStart(recent) ?: return
        val weekEnd = WeeklySummaryCalculator.weekEnd(recent) ?: return
        db.indexDao().insertWeekly(IndexWeeklyEntity(weekStart = weekStart, weekEnd = weekEnd, indexValue = avg))
    }

    suspend fun evaluateAsrsRecalibration(): Double {
        val checkins = db.asrsDao().getRecent(appConfig.asrs.consecutiveMeasurements)
        val recent14 = db.indexDao().getLatestDailyWithDate(14)
        if (checkins.isEmpty() || recent14.isEmpty()) return appConfig.adaptation.alpha
        val asrsScores = checkins.map { it.scoreNormalized.toInt() }
        val indexAverages = recent14.map { it.indexValue }
        return if (AsrsRecalibrator.shouldRecalibrate(asrsScores, indexAverages, appConfig.asrs)) {
            AsrsRecalibrator.alphaForRecalibration(appConfig.asrs)
        } else {
            appConfig.adaptation.alpha
        }
    }

    suspend fun getValuesForDate(date: String): Map<String, EventValueEntity> {
        val day = db.eventDayDao().getByDate(date) ?: return emptyMap()
        return db.eventValueDao().getByDay(day.id).associateBy { it.elementKey }
    }

    suspend fun getLatestVectorValues(): Map<String, Double> {
        val day = db.eventDayDao().getLatest() ?: return emptyMap()
        return db.eventValueDao().getByDay(day.id).associate { it.elementKey to it.valueEffective }
    }

    suspend fun getLatestVectorEntities(): Map<String, EventValueEntity> {
        val day = db.eventDayDao().getLatest() ?: return emptyMap()
        return db.eventValueDao().getByDay(day.id).associateBy { it.elementKey }
    }

    suspend fun evaluateNotification(): NotificationDecision? {
        val today = LocalDate.now().toString()
        val last = db.notificationLogDao().getLatest()
        if (last != null && last.sentAt.startsWith(today)) return null

        val rules = NotificationRules(appConfig.notification, elementConfig.trackableKeys)

        val todayDay = db.eventDayDao().getByDate(today)
        if (rules.dailyReminderNeeded(todayDay)) return rules.buildDailyDecision()

        val days = db.eventDayDao().getLatestDays(appConfig.notification.stressRecoveryDays)
        if (days.size < appConfig.notification.stressRecoveryDays) return null
        val valuesByDay = days.associate { day -> day.id to db.eventValueDao().getByDay(day.id) }

        if (rules.stressRecoveryNeeded(days, valuesByDay)) return rules.buildStressDecision()

        val neglectedKey = rules.neglectedArea(days, valuesByDay)
        if (neglectedKey != null) return rules.buildNeglectedDecision(neglectedKey)

        return null
    }

    suspend fun logNotification(type: String, eventDayId: Long? = null) {
        val now = OffsetDateTime.now().toString()
        db.notificationLogDao().insert(
            NotificationLogEntity(eventDayId = eventDayId, type = type, sentAt = now)
        )
    }

    suspend fun addUserElement(
        key: String,
        weight: Double,
        impact: Int,
        parentCategory: String,
        description: String?,
        scale: List<Int>?
    ): Boolean {
        if (elementConfig.nodes.containsKey(key)) return false
        val existing = db.userElementDao().getAll().any { it.key == key }
        if (existing) return false
        val scaleStr = scale?.joinToString(",")
        db.userElementDao().insert(
            UserElementEntity(
                key = key,
                weight = weight,
                impact = impact,
                parentCategory = parentCategory,
                description = description,
                scale = scaleStr,
                isActive = true
            )
        )
        return true
    }

    suspend fun getUserElements(): List<UserElementEntity> = db.userElementDao().getAll()

    suspend fun getIndexForDate(date: String): Double? {
        val day = db.eventDayDao().getByDate(date) ?: return null
        return db.indexDao().getByDayId(day.id)?.indexValue
    }

    suspend fun getSatisfactionForDate(date: String): Int? {
        val day = db.eventDayDao().getByDate(date) ?: return null
        return db.satisfactionDao().getByDay(day.id)?.valueScale
    }

    suspend fun getSubIndicesForDate(date: String): Pair<Double?, Double?> {
        val day = db.eventDayDao().getByDate(date) ?: return Pair(null, null)
        val index = db.indexDao().getByDayId(day.id) ?: return Pair(null, null)
        return Pair(index.positiveIndex, index.negativeIndex)
    }

    suspend fun getCompletionCountsForDate(date: String): Pair<Int, Int>? {
        val day = db.eventDayDao().getByDate(date) ?: return null
        val values = db.eventValueDao().getByDay(day.id)
        if (values.isEmpty()) return null
        val filtered = values.filter { it.elementKey != "overall_feeling" }
        val completed = filtered.count { it.valueEffective > 0.0 }
        return completed to filtered.size
    }

    suspend fun getDayByDate(date: String): EventDayEntity? = db.eventDayDao().getByDate(date)

    suspend fun deleteDay(dayId: Long) = db.eventDayDao().deleteById(dayId)

    suspend fun getAllEventDates(): List<String> = db.eventDayDao().getAllDates()

    suspend fun getAllWeights(): Map<String, Double> =
        db.weightsDao().getAll().associate { it.elementKey to (it.weightPersonal ?: it.weightDefault) }

    suspend fun removeUserElement(key: String) {
        val elements = db.userElementDao().getAll().filter { it.key == key }
        elements.forEach { db.userElementDao().delete(it) }
    }

    suspend fun exportAll(): String {
        val days = db.eventDayDao().getLatestDays(365)
        val rows = mutableListOf<String>()
        rows.add("date,element_key,value_binary,value_scale,value_effective")
        days.forEach { day ->
            val values = db.eventValueDao().getByDay(day.id)
            values.forEach { v ->
                rows.add("${day.date},${v.elementKey},${v.valueBinary},${v.valueScale ?: ""},${String.format(Locale.US, "%.2f", v.valueEffective)}")
            }
        }
        return rows.joinToString("\n")
    }

    suspend fun exportJson(): String {
        val days = db.eventDayDao().getLatestDays(365)
        val items = days.map { day ->
            val values = db.eventValueDao().getByDay(day.id)
            val satisfaction = db.satisfactionDao().getByDay(day.id)
            val valuesJson = values.joinToString(",") { v ->
                """{"element":"${v.elementKey}","binary":${v.valueBinary},"scale":${v.valueScale ?: "null"},"effective":${String.format(Locale.US, "%.2f", v.valueEffective)}}"""
            }
            val satisfactionJson = satisfaction?.let {
                ""","satisfaction":{"scale":${it.valueScale},"effective":${String.format(Locale.US, "%.2f", it.valueEffective)}}"""
            } ?: ""
            """{"date":"${day.date}","values":[${valuesJson}]${satisfactionJson}}"""
        }
        return "[${items.joinToString(",")}]"
    }

    private suspend fun getEffectiveEntityConfig(): EntityConfig {
        val userElements = db.userElementDao().getAll().filter { it.isActive }
        if (userElements.isEmpty()) return elementConfig
        val extraNodes = userElements.associate { entity ->
            val scale = entity.scale?.split(",")?.mapNotNull { it.trim().toIntOrNull() }?.takeIf { it.size >= 2 }
            entity.key to EntityNode(
                key = entity.key,
                weight = entity.weight,
                impact = entity.impact,
                parent = entity.parentCategory.ifBlank { null },
                label = entity.description ?: entity.key,
                active = entity.isActive,
                scale = scale,
                clickable = false
            )
        }
        return EntityConfig(nodes = elementConfig.nodes + extraNodes)
    }

    companion object {
        internal fun computeActiveKeys(
            entityConfig: EntityConfig,
            overrides: List<UserElementOverrideEntity>
        ): Set<String> {
            val overrideMap = overrides.associateBy { it.elementKey }
            return entityConfig.trackableKeys.filter { key ->
                val override = overrideMap[key]
                override?.isActive ?: (entityConfig.nodes[key]?.active ?: true)
            }.toSet()
        }
    }
}
