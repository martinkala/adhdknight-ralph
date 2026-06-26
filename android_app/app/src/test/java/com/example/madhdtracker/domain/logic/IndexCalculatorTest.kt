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
    fun computeDailyIndex_averagesWeightedValues() {
        val values = listOf(
            EventValueEntity(eventDayId = 1, elementKey = "sleep", valueBinary = 1, valueScale = null, valueEffective = 1.0),
            EventValueEntity(eventDayId = 1, elementKey = "stress_work", valueBinary = 0, valueScale = 1, valueEffective = 0.0)
        )
        val weights = mapOf(
            "sleep" to WeightEntity("sleep", 10.0, null, "now"),
            "stress_work" to WeightEntity("stress_work", 10.0, null, "now")
        )
        val index = IndexCalculator.computeDailyIndex(values, weights, setOf("stress_work"))
        assertEquals(50.0, index ?: 0.0, 0.0001)
    }
}
