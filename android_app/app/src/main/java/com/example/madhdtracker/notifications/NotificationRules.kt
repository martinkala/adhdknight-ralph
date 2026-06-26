package com.example.madhdtracker.notifications

import com.example.madhdtracker.data.DefaultWeights
import com.example.madhdtracker.data.EventDayEntity
import com.example.madhdtracker.data.EventValueEntity
import com.example.madhdtracker.data.NotificationDecision
import java.time.LocalTime

object NotificationRules {
    private val quietStart = LocalTime.of(22, 0)
    private val quietEnd = LocalTime.of(8, 0)

    fun isQuietWindow(now: LocalTime): Boolean {
        return now.isAfter(quietStart) || now.isBefore(quietEnd)
    }

    fun dailyReminderNeeded(todayDay: EventDayEntity?): Boolean {
        return todayDay == null
    }

    fun stressRecoveryNeeded(days: List<EventDayEntity>, valuesByDay: Map<Long, List<EventValueEntity>>): Boolean {
        if (days.size < 3) return false
        return days.all { day ->
            val values = valuesByDay[day.id] ?: emptyList()
            val stressHigh = listOf("stress_work", "stress_personal").any { key ->
                values.firstOrNull { it.elementKey == key }?.valueScale?.let { it >= 4 } ?: false
            }
            val mindfulnessZero = (values.firstOrNull { it.elementKey == "mindfulness" }?.valueEffective ?: 0.0) == 0.0
            stressHigh && mindfulnessZero
        }
    }

    fun neglectedArea(days: List<EventDayEntity>, valuesByDay: Map<Long, List<EventValueEntity>>): String? {
        if (days.size < 3) return null
        val keys = DefaultWeights.weights.keys.filter { it != "overall_feeling" }
        for (key in keys) {
            val allZero = days.all { day ->
                val values = valuesByDay[day.id] ?: emptyList()
                (values.firstOrNull { it.elementKey == key }?.valueEffective ?: 0.0) == 0.0
            }
            if (allZero) return key
        }
        return null
    }

    fun buildDailyDecision(): NotificationDecision {
        return NotificationDecision(
            type = "daily_reminder",
            message = "Nezabudni na dnesny tracker (1-2 min)."
        )
    }

    fun buildStressDecision(): NotificationDecision {
        return NotificationDecision(
            type = "stress_recovery",
            message = "Stres je vyssi a relax nizky. Skus dnes 5-10 min mindfulness."
        )
    }

    fun buildNeglectedDecision(key: String): NotificationDecision {
        return NotificationDecision(
            type = "neglected_area",
            message = "Zda sa, ze $key bol posledne dni nizko. Skus maly krok."
        )
    }
}
