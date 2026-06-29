package com.example.madhdtracker.config

import com.example.madhdtracker.data.AppConfigLoader
import com.example.madhdtracker.data.DefaultWeights
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.ByteArrayInputStream

class AppConfigLoaderTest {

    private fun streamOf(json: String) = ByteArrayInputStream(json.toByteArray())

    // T004 (a): valid JSON → values from JSON
    @Test
    fun `valid full json returns correct AppConfig values`() {
        val json = """
        {
          "weights": { "sleep": 20.0, "overall_feeling": 13.0, "physical_activity": 11.0,
            "stress_work": 13.0, "stress_personal": 13.0, "nutrition_protein": 8.0,
            "caffeine": 6.0, "alcohol": 10.0, "mindfulness": 6.0 },
          "element_classification": { "negative_keys": ["stress_work", "stress_personal"] },
          "adaptation": { "alpha": 0.05, "clamp_min_factor": 0.3, "clamp_max_factor": 3.0,
            "correlation_threshold": 0.15, "min_history_days": 10, "min_series_size": 3 },
          "asrs": { "delta_threshold": 5.0, "consecutive_measurements": 3, "recalibration_alpha": 0.4 },
          "notification": { "quiet_start_hour": 21, "quiet_start_minute": 30,
            "quiet_end_hour": 7, "quiet_end_minute": 0,
            "stress_threshold_scale": 3, "neglected_area_days": 2, "stress_recovery_days": 2 }
        }
        """.trimIndent()
        val config = AppConfigLoader.load(streamOf(json))

        assertEquals(20.0, config.weights["sleep"]!!, 0.001)
        assertEquals(setOf("stress_work", "stress_personal"), config.elementClassification.negativeKeys)
        assertEquals(0.05, config.adaptation.alpha, 0.001)
        assertEquals(0.3, config.adaptation.clampMinFactor, 0.001)
        assertEquals(3.0, config.adaptation.clampMaxFactor, 0.001)
        assertEquals(0.15, config.adaptation.correlationThreshold, 0.001)
        assertEquals(10, config.adaptation.minHistoryDays)
        assertEquals(3, config.adaptation.minSeriesSize)
        assertEquals(5.0, config.asrs.deltaThreshold, 0.001)
        assertEquals(3, config.asrs.consecutiveMeasurements)
        assertEquals(0.4, config.asrs.recalibrationAlpha, 0.001)
        assertEquals(21, config.notification.quietStartHour)
        assertEquals(30, config.notification.quietStartMinute)
        assertEquals(7, config.notification.quietEndHour)
        assertEquals(3, config.notification.stressThresholdScale)
        assertEquals(2, config.notification.neglectedAreaDays)
        assertEquals(2, config.notification.stressRecoveryDays)
    }

    // T004 (b): null stream → all defaults
    @Test
    fun `null stream returns all defaults`() {
        val config = AppConfigLoader.load(null as java.io.InputStream?)

        assertEquals(DefaultWeights.weights["sleep"]!!, config.weights["sleep"]!!, 0.001)
        assertEquals(DefaultWeights.negativeKeys, config.elementClassification.negativeKeys)
        assertEquals(0.2, config.adaptation.alpha, 0.001)
        assertEquals(0.5, config.adaptation.clampMinFactor, 0.001)
        assertEquals(2.0, config.adaptation.clampMaxFactor, 0.001)
        assertEquals(0.1, config.adaptation.correlationThreshold, 0.001)
        assertEquals(15, config.adaptation.minHistoryDays)
        assertEquals(5, config.adaptation.minSeriesSize)
        assertEquals(10.0, config.asrs.deltaThreshold, 0.001)
        assertEquals(2, config.asrs.consecutiveMeasurements)
        assertEquals(0.3, config.asrs.recalibrationAlpha, 0.001)
        assertEquals(22, config.notification.quietStartHour)
        assertEquals(8, config.notification.quietEndHour)
        assertEquals(4, config.notification.stressThresholdScale)
        assertEquals(3, config.notification.neglectedAreaDays)
    }

    // T004 (c): invalid JSON → all defaults
    @Test
    fun `invalid json string returns all defaults`() {
        val config = AppConfigLoader.load(streamOf("{ invalid json !!"))

        assertEquals(DefaultWeights.weights["sleep"]!!, config.weights["sleep"]!!, 0.001)
        assertEquals(0.2, config.adaptation.alpha, 0.001)
        assertEquals(22, config.notification.quietStartHour)
    }

    // T004 (d): partial JSON (only adaptation section) → adaptation from JSON, rest defaults
    @Test
    fun `partial json only adaptation uses adaptation from config and rest from defaults`() {
        val json = """{ "adaptation": { "alpha": 0.05 } }"""
        val config = AppConfigLoader.load(streamOf(json))

        assertEquals(0.05, config.adaptation.alpha, 0.001)
        assertEquals(0.5, config.adaptation.clampMinFactor, 0.001)   // default
        assertEquals(DefaultWeights.weights["sleep"]!!, config.weights["sleep"]!!, 0.001)
        assertEquals(DefaultWeights.negativeKeys, config.elementClassification.negativeKeys)
        assertEquals(22, config.notification.quietStartHour)           // default
    }

    // T010 (a): negative weight → default
    @Test
    fun `negative weight is replaced by default`() {
        val json = """{ "weights": { "sleep": -5.0 } }"""
        val config = AppConfigLoader.load(streamOf(json))
        assertEquals(15.0, config.weights["sleep"]!!, 0.001)
    }

    // T010 (b): alpha > 1 → default
    @Test
    fun `alpha greater than 1 is replaced by default`() {
        val json = """{ "adaptation": { "alpha": 2.5 } }"""
        val config = AppConfigLoader.load(streamOf(json))
        assertEquals(0.2, config.adaptation.alpha, 0.001)
    }

    // T010 (c): clamp_min >= clamp_max → both defaults
    @Test
    fun `clamp min ge max both replaced by defaults`() {
        val json = """{ "adaptation": { "clamp_min_factor": 2.0, "clamp_max_factor": 1.0 } }"""
        val config = AppConfigLoader.load(streamOf(json))
        assertEquals(0.5, config.adaptation.clampMinFactor, 0.001)
        assertEquals(2.0, config.adaptation.clampMaxFactor, 0.001)
    }

    // T010 (d): quiet_start_hour = 25 → default 22
    @Test
    fun `quiet start hour out of range uses default`() {
        val json = """{ "notification": { "quiet_start_hour": 25 } }"""
        val config = AppConfigLoader.load(streamOf(json))
        assertEquals(22, config.notification.quietStartHour)
    }

    // T010 (e): weights summing to 120 → normalized so sum ≈ 100
    @Test
    fun `weights with sum 120 are normalized to sum near 100`() {
        val json = """
        {
          "weights": { "sleep": 35.0, "overall_feeling": 13.0, "physical_activity": 11.0,
            "stress_work": 13.0, "stress_personal": 13.0, "nutrition_protein": 8.0,
            "caffeine": 6.0, "alcohol": 10.0, "mindfulness": 11.0 }
        }
        """.trimIndent()
        val config = AppConfigLoader.load(streamOf(json))
        val sum = config.weights.values.sum()
        assertTrue("sum=$sum should be in (95, 105)", sum > 95.0 && sum < 105.0)
    }

    // positiveKeys = allKeys - negativeKeys
    @Test
    fun `positiveKeys is complement of negativeKeys`() {
        val json = """{ "element_classification": { "negative_keys": ["stress_work"] } }"""
        val config = AppConfigLoader.load(streamOf(json))
        assertTrue("stress_work must be in negativeKeys", "stress_work" in config.elementClassification.negativeKeys)
        assertTrue("stress_work must not be in positiveKeys", "stress_work" !in config.elementClassification.positiveKeys)
        assertTrue("sleep must be in positiveKeys", "sleep" in config.elementClassification.positiveKeys)
    }
}
