package com.example.madhdtracker.data

import com.example.madhdtracker.domain.logic.IndexCalculator
import com.example.madhdtracker.domain.logic.WeeklySummaryCalculator
import com.example.madhdtracker.notifications.NotificationRules
import java.time.LocalDate
import java.time.OffsetDateTime
import java.util.Locale

class TrackerRepository(
    private val db: AppDatabase
) {
    suspend fun seedDefaultWeightsIfEmpty() {
        val existing = db.weightsDao().getAll()
        if (existing.isNotEmpty()) return

        val now = OffsetDateTime.now().toString()
        val weights = DefaultWeights.weights.map { (key, value) ->
            WeightEntity(
                elementKey = key,
                weightDefault = value,
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

    suspend fun computeAndSaveDailyIndex(dayId: Long) {
        val values = db.eventValueDao().getByDay(dayId)
        val weights = db.weightsDao().getAll().associateBy { it.elementKey }
        if (values.isEmpty() || weights.isEmpty()) return

        val indexValue = IndexCalculator.computeDailyIndex(values, weights, DefaultWeights.negativeKeys)
            ?: return
        db.indexDao().insertDaily(IndexDailyEntity(eventDayId = dayId, indexValue = indexValue))
    }

    suspend fun getLatestDailyIndex(): Double? {
        return db.indexDao().getLatestDaily()?.indexValue
    }

    suspend fun getLatestSatisfaction(): Int? {
        return db.satisfactionDao().getLatest()?.valueScale
    }

    suspend fun getLatestCompletionCounts(): Pair<Int, Int>? {
        val day = db.eventDayDao().getLatest() ?: return null
        val values = db.eventValueDao().getByDay(day.id)
        if (values.isEmpty()) return null
        val filtered = values.filter { it.elementKey != "overall_feeling" }
        val completed = filtered.count { it.valueEffective > 0.0 }
        return completed to filtered.size
    }

    suspend fun getLatestDailySeries(limit: Int): List<DailyIndexRow> {
        return db.indexDao().getLatestDailyWithDate(limit)
    }

    suspend fun computeAndSaveWeeklyIndex() {
        val recent = db.indexDao().getLatestDailyWithDate(7)
        if (recent.isEmpty()) return
        val avg = WeeklySummaryCalculator.average(recent) ?: return
        val weekStart = WeeklySummaryCalculator.weekStart(recent) ?: return
        val weekEnd = WeeklySummaryCalculator.weekEnd(recent) ?: return
        db.indexDao().insertWeekly(IndexWeeklyEntity(weekStart = weekStart, weekEnd = weekEnd, indexValue = avg))
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

        val todayDay = db.eventDayDao().getByDate(today)
        if (NotificationRules.dailyReminderNeeded(todayDay)) {
            return NotificationRules.buildDailyDecision()
        }

        val days = db.eventDayDao().getLatestDays(3)
        if (days.size < 3) return null
        val valuesByDay = days.associate { day -> day.id to db.eventValueDao().getByDay(day.id) }

        if (NotificationRules.stressRecoveryNeeded(days, valuesByDay)) {
            return NotificationRules.buildStressDecision()
        }

        val neglectedKey = NotificationRules.neglectedArea(days, valuesByDay)
        if (neglectedKey != null) {
            return NotificationRules.buildNeglectedDecision(neglectedKey)
        }

        return null
    }

    suspend fun logNotification(type: String, eventDayId: Long? = null) {
        val now = OffsetDateTime.now().toString()
        db.notificationLogDao().insert(
            NotificationLogEntity(eventDayId = eventDayId, type = type, sentAt = now)
        )
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
}
