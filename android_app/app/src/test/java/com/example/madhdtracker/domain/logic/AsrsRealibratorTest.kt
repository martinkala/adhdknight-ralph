package com.example.madhdtracker.domain.logic

import com.example.madhdtracker.domain.model.AsrsConfig
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class AsrsRealibratorTest {

    private fun config(delta: Double = 10.0, consec: Int = 2, recalAlpha: Double = 0.3) =
        AsrsConfig(deltaThreshold = delta, consecutiveMeasurements = consec, recalibrationAlpha = recalAlpha)

    @Test
    fun `shouldRecalibrate returns false when not enough measurements`() {
        assertFalse(AsrsRecalibrator.shouldRecalibrate(listOf(80), listOf(60.0), config()))
    }

    @Test
    fun `shouldRecalibrate returns true when delta exceeds threshold for consecutive measurements`() {
        // |80 - 60| = 20 > 10, |85 - 65| = 20 > 10 → recalibrate
        assertTrue(AsrsRecalibrator.shouldRecalibrate(listOf(80, 85), listOf(60.0, 65.0), config()))
    }

    @Test
    fun `shouldRecalibrate returns false when delta below threshold`() {
        // |55 - 50| = 5 < 10 → no recalibration
        assertFalse(AsrsRecalibrator.shouldRecalibrate(listOf(55, 60), listOf(50.0, 55.0), config()))
    }

    @Test
    fun `shouldRecalibrate uses custom deltaThreshold from config`() {
        val lowThresholdConfig = config(delta = 5.0)
        // |57 - 50| = 7 > 5 → should trigger with delta=5
        assertTrue(AsrsRecalibrator.shouldRecalibrate(listOf(57, 57), listOf(50.0, 50.0), lowThresholdConfig))
    }

    @Test
    fun `shouldRecalibrate uses consecutiveMeasurements from config`() {
        val config3 = config(consec = 3)
        // Only 2 measurements provided → not enough for consec=3
        assertFalse(AsrsRecalibrator.shouldRecalibrate(listOf(80, 85), listOf(60.0, 65.0), config3))
        // 3 measurements → sufficient
        assertTrue(AsrsRecalibrator.shouldRecalibrate(listOf(80, 85, 90), listOf(60.0, 65.0, 70.0), config3))
    }

    @Test
    fun `alphaForRecalibration returns recalibrationAlpha from config`() {
        val cfg = config(recalAlpha = 0.4)
        assertEquals(0.4, AsrsRecalibrator.alphaForRecalibration(cfg), 0.001)
    }
}
