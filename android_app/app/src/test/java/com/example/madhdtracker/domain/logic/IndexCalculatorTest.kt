package com.example.madhdtracker.domain.logic

import com.example.madhdtracker.data.EventValueEntity
import com.example.madhdtracker.data.WeightEntity
import org.junit.Assert.assertEquals
import org.junit.Test

class IndexCalculatorTest {
    @Test
    fun valueEffective_usesScaleWhenPresent() {
        val effective = IndexCalculator.valueEffective(0, 5)
        assertEquals(1.0, effective, 0.0001)
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
