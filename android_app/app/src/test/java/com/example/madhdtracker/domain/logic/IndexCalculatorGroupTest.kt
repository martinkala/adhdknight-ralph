package com.example.madhdtracker.domain.logic

import com.example.madhdtracker.data.EventValueEntity
import com.example.madhdtracker.domain.model.Category
import com.example.madhdtracker.domain.model.Element
import com.example.madhdtracker.domain.model.ElementConfig
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class IndexCalculatorGroupTest {

    private fun makeConfig(
        categories: Map<String, Category> = emptyMap(),
        elements: Map<String, Element> = emptyMap()
    ) = ElementConfig(categories, elements)

    private fun makeValue(key: String, effective: Double, dayId: Long = 1): EventValueEntity =
        EventValueEntity(id = 0, eventDayId = dayId, elementKey = key, valueBinary = if (effective > 0) 1 else 0, valueScale = null, valueEffective = effective)

    private fun makeCategory(key: String, weight: Double) =
        Category(key, key, true, weight)

    private fun makeElement(key: String, weight: Double, impact: Int = 1, parent: String? = null) =
        Element(key, weight, impact, parent, key, true, null)

    @Test
    fun groupedIndex_oneElementVsThreeElementsSameTotal_sameIndex() {
        // Category A: 1 element, weight=11.0, done=1.0
        val config1 = makeConfig(
            categories = mapOf("cat_a" to makeCategory("cat_a", 11.0)),
            elements = mapOf("e1" to makeElement("e1", 11.0, parent = "cat_a"))
        )
        val values1 = listOf(makeValue("e1", 1.0))
        val result1 = IndexCalculator.computeDailyIndexGrouped(values1, config1, setOf("e1"))

        // Category A: 3 elements, weight=5.5 each, all done=1.0
        val config2 = makeConfig(
            categories = mapOf("cat_a" to makeCategory("cat_a", 11.0)),
            elements = mapOf(
                "e1" to makeElement("e1", 5.5, parent = "cat_a"),
                "e2" to makeElement("e2", 5.5, parent = "cat_a"),
                "e3" to makeElement("e3", 5.5, parent = "cat_a")
            )
        )
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
        // Category: 3 sub-entities, only 1 done
        val config = makeConfig(
            categories = mapOf("cat" to makeCategory("cat", 15.0)),
            elements = mapOf(
                "e1" to makeElement("e1", 5.0, parent = "cat"),
                "e2" to makeElement("e2", 5.0, parent = "cat"),
                "e3" to makeElement("e3", 5.0, parent = "cat")
            )
        )
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
        val config = makeConfig(
            categories = mapOf("cat" to makeCategory("cat", 11.0)),
            elements = mapOf("e1" to makeElement("e1", 11.0, parent = "cat"))
        )
        val values = listOf(makeValue("e1", 1.0))
        val result = IndexCalculator.computeDailyIndexGrouped(values, config, emptySet())

        assertNull(result)
    }

    @Test
    fun groupedIndex_rootElementContributesDirectly() {
        // Root element (parent=null) contributes with its own weight, no category normalization
        val config = makeConfig(
            categories = emptyMap(),
            elements = mapOf("root" to makeElement("root", 20.0, impact = 1, parent = null))
        )
        val values = listOf(makeValue("root", 1.0))
        val result = IndexCalculator.computeDailyIndexGrouped(values, config, setOf("root"))

        assertEquals(100.0, result ?: 0.0, 0.001)
    }

    @Test
    fun groupedIndex_negativeElementInverted() {
        // Negative element: done=1.0 should be bad, so effective = 1.0 - 1.0 = 0.0
        val config = makeConfig(
            categories = mapOf("cat" to makeCategory("cat", 10.0)),
            elements = mapOf("stress" to makeElement("stress", 10.0, impact = -1, parent = "cat"))
        )
        val values = listOf(makeValue("stress", 1.0))
        val result = IndexCalculator.computeDailyIndexGrouped(values, config, setOf("stress"))

        assertEquals(0.0, result ?: -1.0, 0.001)
    }

    @Test
    fun groupedIndex_emptyValues_returnsNull() {
        val config = makeConfig(
            categories = mapOf("cat" to makeCategory("cat", 10.0)),
            elements = mapOf("e1" to makeElement("e1", 10.0, parent = "cat"))
        )
        val result = IndexCalculator.computeDailyIndexGrouped(emptyList(), config, setOf("e1"))

        assertNull(result)
    }

    @Test
    fun groupedIndex_mixedRootAndCategory_combinedCorrectly() {
        // Root element (weight=10, done) + category (weight=10, 1 element done)
        // Expected: (10*1.0 + 1.0*10.0) / (10+10) * 100 = 100
        val config = makeConfig(
            categories = mapOf("cat" to makeCategory("cat", 10.0)),
            elements = mapOf(
                "root" to makeElement("root", 10.0, impact = 1, parent = null),
                "cat_e" to makeElement("cat_e", 10.0, impact = 1, parent = "cat")
            )
        )
        val values = listOf(makeValue("root", 1.0), makeValue("cat_e", 1.0))
        val result = IndexCalculator.computeDailyIndexGrouped(values, config, setOf("root", "cat_e"))

        assertEquals(100.0, result ?: 0.0, 0.001)
    }
}
