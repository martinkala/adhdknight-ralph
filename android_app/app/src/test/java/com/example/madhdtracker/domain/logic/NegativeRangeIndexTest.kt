package com.example.madhdtracker.domain.logic

import com.example.madhdtracker.data.EventValueEntity
import com.example.madhdtracker.data.WeightEntity
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test

class NegativeRangeIndexTest {

    private fun ev(key: String, effective: Double) =
        EventValueEntity(eventDayId = 1, elementKey = key, valueBinary = 1, valueScale = null, valueEffective = effective)

    private fun w(key: String, weight: Double) = WeightEntity(key, weight, null, "now")

    @Test
    fun allElementsAtScaleMin_negativeRange_indexIsZero() {
        // sleep at -2 (scaleMin) → valueEffective = 0.0
        val effective = IndexCalculator.valueEffective(0, -2, -2, 2)
        assertEquals(0.0, effective, 0.0001)

        val values = listOf(ev("sleep", 0.0))
        val weights = mapOf("sleep" to w("sleep", 15.0))
        val index = IndexCalculator.computePositiveIndex(values, weights, emptySet())
        assertEquals(0.0, index ?: 0.0, 0.0001)
    }

    @Test
    fun allElementsAtScaleMax_indexIs100() {
        val effective = IndexCalculator.valueEffective(0, 2, -2, 2)
        assertEquals(1.0, effective, 0.0001)

        val values = listOf(ev("sleep", 1.0))
        val weights = mapOf("sleep" to w("sleep", 15.0))
        val index = IndexCalculator.computePositiveIndex(values, weights, emptySet())
        assertEquals(100.0, index ?: 0.0, 0.0001)
    }

    @Test
    fun mixedNegativeAndPositive_indexInValidRange() {
        val sleepEffective = IndexCalculator.valueEffective(0, -1, -2, 2)  // 0.25
        val moodEffective = IndexCalculator.valueEffective(0, 1, -2, 2)    // 0.75

        val values = listOf(ev("sleep", sleepEffective), ev("overall_feeling", moodEffective))
        val weights = mapOf(
            "sleep" to w("sleep", 15.0),
            "overall_feeling" to w("overall_feeling", 13.0)
        )
        val index = IndexCalculator.computePositiveIndex(values, weights, emptySet())
        assertNotNull(index)
        assertTrue("index should be between 0 and 100, was $index", index!! in 0.0..100.0)
    }

    @Test
    fun negativeImpactElementAtNegativeValue_effectiveIsZero() {
        // stress_work at scaleMin=-2 → valueEffective=0.0 (minimum stress = no negative contribution)
        val effective = IndexCalculator.valueEffective(0, -2, -2, 2)
        assertEquals(0.0, effective, 0.0001)

        val values = listOf(ev("stress_work", 0.0))
        val weights = mapOf("stress_work" to w("stress_work", 13.0))
        val negIndex = IndexCalculator.computeNegativeIndex(values, weights, setOf("stress_work"))
        assertEquals(0.0, negIndex ?: 0.0, 0.0001)
    }

    @Test
    fun negativeImpactElementAtPositiveValue_effectiveIsOne() {
        // stress_work at scaleMax=2 → valueEffective=1.0 (maximum stress = full negative weight)
        val effective = IndexCalculator.valueEffective(0, 2, -2, 2)
        assertEquals(1.0, effective, 0.0001)

        val values = listOf(ev("stress_work", 1.0))
        val weights = mapOf("stress_work" to w("stress_work", 13.0))
        val negIndex = IndexCalculator.computeNegativeIndex(values, weights, setOf("stress_work"))
        assertEquals(100.0, negIndex ?: 0.0, 0.0001)
    }

    @Test
    fun overallFeelingAlwaysScale1to5_unchanged() {
        // Constitution Principle IV invariant
        assertEquals(0.5, IndexCalculator.valueEffective(0, 3, 1, 5), 0.0001)
        assertEquals(0.0, IndexCalculator.valueEffective(0, 1, 1, 5), 0.0001)
        assertEquals(1.0, IndexCalculator.valueEffective(0, 5, 1, 5), 0.0001)
    }
}
