package com.example.madhdtracker.domain.logic

import com.example.madhdtracker.data.EventValueEntity
import com.example.madhdtracker.domain.model.EntityConfig
import com.example.madhdtracker.domain.model.EntityNode
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class IndexCalculatorGroupTest {

    private fun makeEntityNode(
        key: String,
        weight: Double,
        impact: Int?,
        parent: String? = null
    ) = EntityNode(key = key, weight = weight, impact = impact, parent = parent, label = key, active = true, scale = null, clickable = false)

    private fun makeConfig(nodes: Map<String, EntityNode>) = EntityConfig(nodes)

    private fun makeValue(key: String, effective: Double, dayId: Long = 1): EventValueEntity =
        EventValueEntity(id = 0, eventDayId = dayId, elementKey = key, valueBinary = if (effective > 0) 1 else 0, valueScale = null, valueEffective = effective)

    @Test
    fun groupedIndex_oneElementVsThreeElementsSameTotal_sameIndex() {
        // Category A: 1 element, weight=11.0, done=1.0
        val config1 = makeConfig(mapOf(
            "cat_a" to makeEntityNode("cat_a", 11.0, null),
            "e1" to makeEntityNode("e1", 11.0, 1, "cat_a")
        ))
        val values1 = listOf(makeValue("e1", 1.0))
        val result1 = IndexCalculator.computeDailyIndexGrouped(values1, config1, setOf("e1"))

        // Category A: 3 elements, weight=5.5 each, all done=1.0
        val config2 = makeConfig(mapOf(
            "cat_a" to makeEntityNode("cat_a", 11.0, null),
            "e1" to makeEntityNode("e1", 5.5, 1, "cat_a"),
            "e2" to makeEntityNode("e2", 5.5, 1, "cat_a"),
            "e3" to makeEntityNode("e3", 5.5, 1, "cat_a")
        ))
        val values2 = listOf(makeValue("e1", 1.0), makeValue("e2", 1.0), makeValue("e3", 1.0))
        val result2 = IndexCalculator.computeDailyIndexGrouped(values2, config2, setOf("e1", "e2", "e3"))

        assertNull("result1 should not be null", null.takeIf { result1 != null })
        assertNull("result2 should not be null", null.takeIf { result2 != null })
        assertEquals("1-element and 3-element categories should produce same index when all done",
            result1!!, result2!!, 0.001)
        assertEquals(100.0, result1, 0.001)
    }

    @Test
    fun groupedIndex_oneOfThreeActiveSubEntitiesDone_proportionalContribution() {
        val config = makeConfig(mapOf(
            "cat" to makeEntityNode("cat", 15.0, null),
            "e1" to makeEntityNode("e1", 5.0, 1, "cat"),
            "e2" to makeEntityNode("e2", 5.0, 1, "cat"),
            "e3" to makeEntityNode("e3", 5.0, 1, "cat")
        ))
        // e1 done, e2 and e3 not done
        val values = listOf(makeValue("e1", 1.0), makeValue("e2", 0.0), makeValue("e3", 0.0))
        val activeKeys = setOf("e1", "e2", "e3")
        val resultPartial = IndexCalculator.computeDailyIndexGrouped(values, config, activeKeys)

        // All done
        val valuesAll = listOf(makeValue("e1", 1.0), makeValue("e2", 1.0), makeValue("e3", 1.0))
        val resultAll = IndexCalculator.computeDailyIndexGrouped(valuesAll, config, activeKeys)

        val partial = resultPartial ?: error("partial should not be null")
        val all = resultAll ?: error("all should not be null")

        // 1/3 done → index should be ~1/3 of all-done index
        assertEquals(all / 3.0, partial, 0.001)
    }

    @Test
    fun groupedIndex_allElementsInactive_returnsNull() {
        val config = makeConfig(mapOf(
            "cat" to makeEntityNode("cat", 11.0, null),
            "e1" to makeEntityNode("e1", 11.0, 1, "cat")
        ))
        val values = listOf(makeValue("e1", 1.0))
        val result = IndexCalculator.computeDailyIndexGrouped(values, config, emptySet())

        assertNull(result)
    }

    @Test
    fun groupedIndex_rootElementContributesDirectly() {
        val config = makeConfig(mapOf(
            "root" to makeEntityNode("root", 20.0, 1, null)
        ))
        val values = listOf(makeValue("root", 1.0))
        val result = IndexCalculator.computeDailyIndexGrouped(values, config, setOf("root"))

        assertEquals(100.0, result ?: 0.0, 0.001)
    }

    @Test
    fun groupedIndex_negativeElementInverted() {
        val config = makeConfig(mapOf(
            "cat" to makeEntityNode("cat", 10.0, null),
            "stress" to makeEntityNode("stress", 10.0, -1, "cat")
        ))
        val values = listOf(makeValue("stress", 1.0))
        val result = IndexCalculator.computeDailyIndexGrouped(values, config, setOf("stress"))

        assertEquals(0.0, result ?: -1.0, 0.001)
    }

    @Test
    fun groupedIndex_emptyValues_returnsNull() {
        val config = makeConfig(mapOf(
            "cat" to makeEntityNode("cat", 10.0, null),
            "e1" to makeEntityNode("e1", 10.0, 1, "cat")
        ))
        val result = IndexCalculator.computeDailyIndexGrouped(emptyList(), config, setOf("e1"))

        assertNull(result)
    }

    @Test
    fun groupedIndex_mixedRootAndCategory_combinedCorrectly() {
        // Root element (weight=10, done) + category (weight=10, 1 element done)
        // Expected: (10*1.0 + 1.0*10.0) / (10+10) * 100 = 100
        val config = makeConfig(mapOf(
            "cat" to makeEntityNode("cat", 10.0, null),
            "root" to makeEntityNode("root", 10.0, 1, null),
            "cat_e" to makeEntityNode("cat_e", 10.0, 1, "cat")
        ))
        val values = listOf(makeValue("root", 1.0), makeValue("cat_e", 1.0))
        val result = IndexCalculator.computeDailyIndexGrouped(values, config, setOf("root", "cat_e"))

        assertEquals(100.0, result ?: 0.0, 0.001)
    }

    // T015: Trackable parent logic tests

    @Test
    fun groupedIndex_trackableParentWithActiveChild_usesGroupAvg() {
        // Trackable root with one active child → group avg × root weight, not direct
        val config = makeConfig(mapOf(
            "sleep" to makeEntityNode("sleep", 15.0, 1, null),
            "sleep_quality" to makeEntityNode("sleep_quality", 5.0, 1, "sleep")
        ))
        val values = listOf(makeValue("sleep_quality", 1.0))
        val result = IndexCalculator.computeDailyIndexGrouped(values, config, setOf("sleep_quality"))

        // group_avg(sleep_quality=1.0) × sleep.weight=15.0 / totalWeight=15.0 × 100 = 100
        assertEquals(100.0, result ?: 0.0, 0.001)
    }

    @Test
    fun groupedIndex_trackableParentNoActiveChild_contributesDirect() {
        // Trackable root with no active children → direct contribution
        val config = makeConfig(mapOf(
            "sleep" to makeEntityNode("sleep", 15.0, 1, null),
            "sleep_quality" to makeEntityNode("sleep_quality", 5.0, 1, "sleep")
        ))
        val values = listOf(makeValue("sleep", 0.5))
        val result = IndexCalculator.computeDailyIndexGrouped(values, config, setOf("sleep"))

        // sleep contributes directly: 15.0 * 0.5 / 15.0 * 100 = 50
        assertEquals(50.0, result ?: 0.0, 0.001)
    }

    @Test
    fun groupedIndex_trackableParentNegativeWithActiveChild_childInverted() {
        // Trackable root (negative) with one active child → child effective inverted
        val config = makeConfig(mapOf(
            "stress_parent" to makeEntityNode("stress_parent", 10.0, -1, null),
            "stress_child" to makeEntityNode("stress_child", 5.0, -1, "stress_parent")
        ))
        val values = listOf(makeValue("stress_child", 1.0))
        val result = IndexCalculator.computeDailyIndexGrouped(values, config, setOf("stress_child"))

        // effective = 1.0 - 1.0 = 0.0; groupAvg = 0.0; contribution = 0.0 * 10.0 = 0.0
        assertEquals(0.0, result ?: -1.0, 0.001)
    }
}
