package com.example.madhdtracker.notifications

import com.example.madhdtracker.data.EventDayEntity
import com.example.madhdtracker.data.EventValueEntity
import com.example.madhdtracker.domain.model.NotificationConfig
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.time.LocalTime

class NotificationRulesTest {

    private fun defaultConfig() = NotificationConfig(
        quietStartHour = 22, quietStartMinute = 0,
        quietEndHour = 8, quietEndMinute = 0,
        stressThresholdScale = 4, neglectedAreaDays = 3, stressRecoveryDays = 3
    )

    private fun defaultRules() = NotificationRules(defaultConfig(), defaultElementKeys())

    private fun defaultElementKeys() = setOf(
        "overall_feeling", "sleep", "physical_activity",
        "stress_work", "stress_personal", "nutrition_protein",
        "caffeine", "alcohol", "mindfulness"
    )

    @Test
    fun quietWindow_blocksLateHours() {
        val rules = defaultRules()
        assertTrue(rules.isQuietWindow(LocalTime.of(23, 0)))
        assertTrue(rules.isQuietWindow(LocalTime.of(7, 30)))
        assertFalse(rules.isQuietWindow(LocalTime.of(12, 0)))
    }

    @Test
    fun dailyReminderNeeded_whenNoDay() {
        assertTrue(defaultRules().dailyReminderNeeded(null))
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
        assertTrue(defaultRules().stressRecoveryNeeded(days, values))
    }

    // T011 (a): custom quietStartHour=20 → isQuietWindow(21:00) = true
    @Test
    fun quietWindow_usesCustomQuietStartHourFromConfig() {
        val config = defaultConfig().copy(quietStartHour = 20, quietStartMinute = 0)
        val rules = NotificationRules(config, defaultElementKeys())
        assertTrue("21:00 should be in quiet window when quietStart=20:00",
            rules.isQuietWindow(LocalTime.of(21, 0)))
        assertFalse("14:00 should NOT be in quiet window when quietStart=20:00",
            rules.isQuietWindow(LocalTime.of(14, 0)))
    }

    // T011 (b): stressThresholdScale=3 → triggers when valueScale=3
    @Test
    fun stressRecovery_usesCustomStressThresholdFromConfig() {
        val config = defaultConfig().copy(stressThresholdScale = 3)
        val rules = NotificationRules(config, defaultElementKeys())
        val days = listOf(
            EventDayEntity(id = 1, date = "2026-01-01", createdAt = "", updatedAt = ""),
            EventDayEntity(id = 2, date = "2026-01-02", createdAt = "", updatedAt = ""),
            EventDayEntity(id = 3, date = "2026-01-03", createdAt = "", updatedAt = "")
        )
        val values = mapOf(
            1L to listOf(EventValueEntity(1, 1, "stress_work", 0, 3, 0.5),
                         EventValueEntity(2, 1, "mindfulness", 0, null, 0.0)),
            2L to listOf(EventValueEntity(3, 2, "stress_work", 0, 3, 0.5),
                         EventValueEntity(4, 2, "mindfulness", 0, null, 0.0)),
            3L to listOf(EventValueEntity(5, 3, "stress_work", 0, 3, 0.5),
                         EventValueEntity(6, 3, "mindfulness", 0, null, 0.0))
        )
        assertTrue("stressThresholdScale=3 should trigger at valueScale=3", rules.stressRecoveryNeeded(days, values))

        // With default threshold=4, scale=3 should NOT trigger
        assertFalse("default stressThresholdScale=4 should NOT trigger at valueScale=3",
            defaultRules().stressRecoveryNeeded(days, values))
    }

    // T011 (c): neglectedAreaDays=2 → triggers after 2 days
    @Test
    fun neglectedArea_usesCustomDaysFromConfig() {
        val config = defaultConfig().copy(neglectedAreaDays = 2)
        val rules = NotificationRules(config, defaultElementKeys())
        val days = listOf(
            EventDayEntity(id = 1, date = "2026-01-01", createdAt = "", updatedAt = ""),
            EventDayEntity(id = 2, date = "2026-01-02", createdAt = "", updatedAt = "")
        )
        val values = mapOf(
            1L to listOf(EventValueEntity(1, 1, "sleep", 0, null, 0.0)),
            2L to listOf(EventValueEntity(2, 2, "sleep", 0, null, 0.0))
        )
        assertNotNull("neglectedAreaDays=2 should trigger after 2 days of zero sleep",
            rules.neglectedArea(days, values))

        // With default=3, only 2 days → should return null
        assertNull("default neglectedAreaDays=3 should NOT trigger with only 2 days",
            defaultRules().neglectedArea(days, values))
    }
}
