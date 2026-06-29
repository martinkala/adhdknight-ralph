package com.example.madhdtracker.notifications

import com.example.madhdtracker.data.EventDayEntity
import com.example.madhdtracker.data.EventValueEntity
import com.example.madhdtracker.data.NotificationDecision
import com.example.madhdtracker.domain.model.NotificationConfig
import java.time.LocalTime

class NotificationRules(
    private val config: NotificationConfig,
    private val allElementKeys: Set<String>
) {
    private val quietStart = LocalTime.of(config.quietStartHour, config.quietStartMinute)
    private val quietEnd   = LocalTime.of(config.quietEndHour, config.quietEndMinute)

    fun isQuietWindow(now: LocalTime): Boolean =
        now.isAfter(quietStart) || now.isBefore(quietEnd)

    fun dailyReminderNeeded(todayDay: EventDayEntity?): Boolean = todayDay == null

    fun stressRecoveryNeeded(days: List<EventDayEntity>, valuesByDay: Map<Long, List<EventValueEntity>>): Boolean {
        if (days.size < config.stressRecoveryDays) return false
        return days.takeLast(config.stressRecoveryDays).all { day ->
            val values = valuesByDay[day.id] ?: emptyList()
            val stressHigh = listOf("stress_work", "stress_personal").any { key ->
                values.firstOrNull { it.elementKey == key }
                    ?.valueScale?.let { it >= config.stressThresholdScale } ?: false
            }
            val mindfulnessZero = (values.firstOrNull { it.elementKey == "mindfulness" }?.valueEffective ?: 0.0) == 0.0
            stressHigh && mindfulnessZero
        }
    }

    fun neglectedArea(days: List<EventDayEntity>, valuesByDay: Map<Long, List<EventValueEntity>>): String? {
        if (days.size < config.neglectedAreaDays) return null
        val recentDays = days.takeLast(config.neglectedAreaDays)
        val keys = allElementKeys.filter { it != "overall_feeling" }
        for (key in keys) {
            val allZero = recentDays.all { day ->
                val values = valuesByDay[day.id] ?: emptyList()
                (values.firstOrNull { it.elementKey == key }?.valueEffective ?: 0.0) == 0.0
            }
            if (allZero) return key
        }
        return null
    }

    fun buildDailyDecision() = NotificationDecision(
        type = "daily_reminder",
        message = "Nezabudni na dnesny tracker (1-2 min)."
    )

    fun buildStressDecision() = NotificationDecision(
        type = "stress_recovery",
        message = "Stres je vyssi a relax nizky. Skus dnes 5-10 min mindfulness."
    )

    fun buildNeglectedDecision(key: String) = NotificationDecision(
        type = "neglected_area",
        message = "Zda sa, ze $key bol posledne dni nizko. Skus maly krok."
    )
}
