package com.example.madhdtracker.domain.logic

import com.example.madhdtracker.data.EventValueEntity
import com.example.madhdtracker.data.WeightEntity
import com.example.madhdtracker.domain.model.AdaptationConfig
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Test

class IndexCalculatorTest {
    @Test
    fun valueEffective_usesScaleWhenPresent() {
        val effective = IndexCalculator.valueEffective(0, 5)
        assertEquals(1.0, effective, 0.0001)
    }

    // T006 — failing tests for new scaleMin/scaleMax signature
    @Test
    fun valueEffective_negativeScaleMin_returnsZeroAtMin() {
        assertEquals(0.0, IndexCalculator.valueEffective(0, -2, -2, 2), 0.0001)
    }

    @Test
    fun valueEffective_negativeScaleMin_returnsMidpointAtZero() {
        assertEquals(0.5, IndexCalculator.valueEffective(0, 0, -2, 2), 0.0001)
    }

    @Test
    fun valueEffective_negativeScaleMin_returnsOneAtMax() {
        assertEquals(1.0, IndexCalculator.valueEffective(0, 2, -2, 2), 0.0001)
    }

    @Test
    fun valueEffective_backwardCompat_scaleOneToFiveMidpoint() {
        assertEquals(0.5, IndexCalculator.valueEffective(0, 3, 1, 5), 0.0001)
    }

    @Test
    fun valueEffective_backwardCompat_scaleOneToFiveMax() {
        assertEquals(1.0, IndexCalculator.valueEffective(0, 5, 1, 5), 0.0001)
    }

    @Test
    fun computePositiveIndex_onlyPositiveKeysContribute() {
        val values = listOf(
            EventValueEntity(eventDayId = 1, elementKey = "sleep", valueBinary = 1, valueScale = null, valueEffective = 1.0),
            EventValueEntity(eventDayId = 1, elementKey = "stress_work", valueBinary = 1, valueScale = null, valueEffective = 1.0)
        )
        val weights = mapOf(
            "sleep" to WeightEntity("sleep", 10.0, null, "now"),
            "stress_work" to WeightEntity("stress_work", 10.0, null, "now")
        )
        val result = IndexCalculator.computePositiveIndex(values, weights, setOf("sleep"))
        assertEquals(100.0, result ?: 0.0, 0.0001)
    }

    @Test
    fun computePositiveIndex_returnsNullWhenNoMatchingKeys() {
        val values = listOf(
            EventValueEntity(eventDayId = 1, elementKey = "stress_work", valueBinary = 1, valueScale = null, valueEffective = 1.0)
        )
        val weights = mapOf("stress_work" to WeightEntity("stress_work", 10.0, null, "now"))
        val result = IndexCalculator.computePositiveIndex(values, weights, setOf("sleep"))
        assertEquals(null, result)
    }

    @Test
    fun computeNegativeIndex_onlyNegativeKeysContribute() {
        val values = listOf(
            EventValueEntity(eventDayId = 1, elementKey = "sleep", valueBinary = 1, valueScale = null, valueEffective = 1.0),
            EventValueEntity(eventDayId = 1, elementKey = "alcohol", valueBinary = 1, valueScale = null, valueEffective = 0.5)
        )
        val weights = mapOf(
            "sleep" to WeightEntity("sleep", 10.0, null, "now"),
            "alcohol" to WeightEntity("alcohol", 10.0, null, "now")
        )
        val result = IndexCalculator.computeNegativeIndex(values, weights, setOf("alcohol"))
        assertEquals(50.0, result ?: 0.0, 0.0001)
    }

    @Test
    fun computeNegativeIndex_returnsNullWhenEmpty() {
        val result = IndexCalculator.computeNegativeIndex(emptyList(), emptyMap(), setOf("alcohol"))
        assertEquals(null, result)
    }

    @Test
    fun computeNegativeIndex_noInversion_higherValueMeansWorse() {
        val values = listOf(
            EventValueEntity(eventDayId = 1, elementKey = "stress_work", valueBinary = 1, valueScale = 5, valueEffective = 1.0)
        )
        val weights = mapOf("stress_work" to WeightEntity("stress_work", 10.0, null, "now"))
        val result = IndexCalculator.computeNegativeIndex(values, weights, setOf("stress_work"))
        // valueEffective = 1.0 → negativeIndex = 100.0 (maximum negatívneho správania)
        assertEquals(100.0, result ?: 0.0, 0.0001)
    }

    @Test
    fun adaptWeights_usesAlphaFromAdaptationConfig() {
        // sleep correlates positively, stress correlates negatively with overall_feeling.
        // This creates net weight divergence that survives normalization.
        val defaults = mapOf("sleep" to 15.0, "stress" to 13.0, "overall_feeling" to 13.0)
        val current  = mapOf("sleep" to 15.0, "stress" to 13.0, "overall_feeling" to 13.0)
        val history = (1..20).map { i ->
            val v = if (i % 2 == 0) 1.0 else 0.0
            mapOf("sleep" to v, "stress" to (1.0 - v), "overall_feeling" to v)
        }

        val configHighAlpha = AdaptationConfig(alpha = 0.5, clampMinFactor = 0.5, clampMaxFactor = 2.0,
            correlationThreshold = 0.1, minHistoryDays = 15, minSeriesSize = 5)
        val configLowAlpha = AdaptationConfig(alpha = 0.01, clampMinFactor = 0.5, clampMaxFactor = 2.0,
            correlationThreshold = 0.1, minHistoryDays = 15, minSeriesSize = 5)

        val resultHigh = IndexCalculator.adaptWeights(defaults, current, history, configHighAlpha)
        val resultLow  = IndexCalculator.adaptWeights(defaults, current, history, configLowAlpha)

        val rawSleep = 15.0
        val deltaHigh = kotlin.math.abs((resultHigh["sleep"] ?: rawSleep) - rawSleep)
        val deltaLow  = kotlin.math.abs((resultLow["sleep"]  ?: rawSleep) - rawSleep)
        assert(deltaHigh > deltaLow) { "high alpha delta ($deltaHigh) should exceed low alpha delta ($deltaLow)" }
        assert(deltaHigh > 0.0) { "high alpha should produce non-zero weight change, got $deltaHigh" }
    }

    @Test
    fun adaptWeights_respectsMinHistoryDays() {
        val defaults = mapOf("sleep" to 15.0, "overall_feeling" to 13.0)
        val current  = mapOf("sleep" to 15.0, "overall_feeling" to 13.0)
        val shortHistory = (1..5).map { mapOf("sleep" to 1.0, "overall_feeling" to 1.0) }

        val config = AdaptationConfig(alpha = 0.2, clampMinFactor = 0.5, clampMaxFactor = 2.0,
            correlationThreshold = 0.1, minHistoryDays = 10, minSeriesSize = 5)

        val result = IndexCalculator.adaptWeights(defaults, current, shortHistory, config)
        assertEquals("should return currentWeights unchanged when history < minHistoryDays",
            current["sleep"]!!, result["sleep"]!!, 0.001)
    }

    @Test
    fun computeDailyIndexGrouped_mixedEntityConfig_staysIn0to100() {
        val sleepEffective = IndexCalculator.valueEffective(0, -1, -2, 2)       // 0.25
        val feelingEffective = IndexCalculator.valueEffective(0, 3, 1, 5)       // 0.5
        val stressEffective = IndexCalculator.valueEffective(0, 4, 1, 5)        // 0.75

        val values = listOf(
            EventValueEntity(1, "sleep", 1, -1, sleepEffective),
            EventValueEntity(1, "overall_feeling", 1, 3, feelingEffective),
            EventValueEntity(1, "stress_work", 1, 4, stressEffective)
        )
        val weights = mapOf(
            "sleep" to WeightEntity("sleep", 15.0, null, "now"),
            "overall_feeling" to WeightEntity("overall_feeling", 13.0, null, "now"),
            "stress_work" to WeightEntity("stress_work", 13.0, null, "now")
        )
        val index = IndexCalculator.computeDailyIndex(values, weights, setOf("stress_work"))
        assertNotEquals(null, index)
        assert(index!! in 0.0..100.0) { "index $index out of 0..100 range" }
    }

    @Test
    fun computeDailyIndex_averagesWeightedValues() {
        val values = listOf(
            EventValueEntity(eventDayId = 1, elementKey = "sleep", valueBinary = 1, valueScale = null, valueEffective = 1.0),
            EventValueEntity(eventDayId = 1, elementKey = "stress_work", valueBinary = 1, valueScale = null, valueEffective = 1.0)
        )
        val weights = mapOf(
            "sleep" to WeightEntity("sleep", 10.0, null, "now"),
            "stress_work" to WeightEntity("stress_work", 10.0, null, "now")
        )
        val index = IndexCalculator.computeDailyIndex(values, weights, setOf("stress_work"))
        assertEquals(50.0, index ?: 0.0, 0.0001)
    }
}
