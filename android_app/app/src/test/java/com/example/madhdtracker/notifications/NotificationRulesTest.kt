package com.example.madhdtracker.notifications

import com.example.madhdtracker.data.EventDayEntity
import com.example.madhdtracker.data.EventValueEntity
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import java.time.LocalTime

class NotificationRulesTest {
    @Test
    fun quietWindow_blocksLateHours() {
        assertTrue(NotificationRules.isQuietWindow(LocalTime.of(23, 0)))
        assertTrue(NotificationRules.isQuietWindow(LocalTime.of(7, 30)))
        assertFalse(NotificationRules.isQuietWindow(LocalTime.of(12, 0)))
    }

    @Test
    fun dailyReminderNeeded_whenNoDay() {
        assertTrue(NotificationRules.dailyReminderNeeded(null))
    }

    @Test
    fun stressRecoveryNeeded_whenThreeDaysHighStressAndNoMindfulness() {
        val days = listOf(
            EventDayEntity(id = 1, date = "2026-01-01", createdAt = "", updatedAt = ""),
            EventDayEntity(id = 2, date = "2026-01-02", createdAt = "", updatedAt = ""),
            EventDayEntity(id = 3, date = "2026-01-03", createdAt = "", updatedAt = "")
        )
        val values = mapOf(
            1L to listOf(
                EventValueEntity(1, 1, "stress_work", 0, 4, 0.75),
                EventValueEntity(2, 1, "mindfulness", 0, null, 0.0)
            ),
            2L to listOf(
                EventValueEntity(3, 2, "stress_personal", 0, 4, 0.75),
                EventValueEntity(4, 2, "mindfulness", 0, null, 0.0)
            ),
            3L to listOf(
                EventValueEntity(5, 3, "stress_work", 0, 5, 1.0),
                EventValueEntity(6, 3, "mindfulness", 0, null, 0.0)
            )
        )
        assertTrue(NotificationRules.stressRecoveryNeeded(days, values))
    }
}
