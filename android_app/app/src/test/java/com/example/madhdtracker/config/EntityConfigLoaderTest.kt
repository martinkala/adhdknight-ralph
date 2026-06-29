package com.example.madhdtracker.config

import com.example.madhdtracker.data.EntityConfigLoader
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class EntityConfigLoaderTest {

    private fun yamlStream(content: String) = content.trimIndent().byteInputStream()

    private val fullYaml = """
        categories:
          sleep:
            label: "Spánok"
            clickable: true
            weight: 15.0
          physical_activity:
            label: "Fyzická aktivita"
            clickable: true
            weight: 11.0
          lifestyle:
            label: "Životný štýl"
            clickable: false
            weight: 42.0
          head:
            label: "Mentálne aktivity"
            clickable: false
            weight: 11.0
          food:
            label: "Strava"
            clickable: false
            weight: 8.0
        elements:
          overall_feeling:
            weight: 13.0
            impact: 1
            parent: null
            description: "Celkový pocit za deň"
            active: true
            scale: [1, 2, 3, 4, 5]
          sleep:
            weight: 15.0
            impact: 1
            parent: sleep
            description: "Kvalitný spánok"
            active: true
          physical_activity:
            weight: 11.0
            impact: 1
            parent: physical_activity
            description: "Fyzická aktivita"
            active: true
            scale: [1, 2, 3, 4, 5]
          stress_work:
            weight: 13.0
            impact: -1
            parent: lifestyle
            description: "Pracovný stres"
            active: true
            scale: [1, 2, 3, 4, 5]
          stress_personal:
            weight: 13.0
            impact: -1
            parent: lifestyle
            description: "Osobný stres"
            active: true
            scale: [1, 2, 3, 4, 5]
          caffeine:
            weight: 6.0
            impact: -1
            parent: lifestyle
            description: "Kofeín"
            active: true
            scale: [1, 2, 3, 4, 5]
          alcohol:
            weight: 10.0
            impact: -1
            parent: lifestyle
            description: "Alkohol"
            active: true
            scale: [1, 2, 3, 4, 5]
          nutrition_protein:
            weight: 8.0
            impact: 1
            parent: food
            description: "Príjem bielkovín"
            active: true
          mindfulness:
            weight: 11.0
            impact: 1
            parent: head
            description: "Mindfulness / meditácia"
            active: true
    """

    @Test
    fun load_validFullYaml_returnsCorrectConfig() {
        val config = EntityConfigLoader.load(yamlStream(fullYaml))

        assertEquals(15.0, config.elements["sleep"]?.weight ?: 0.0, 0.001)
        assertEquals(5, config.categories.size)
        assertEquals(9, config.elements.size)
        assertEquals(setOf("stress_work", "stress_personal", "caffeine", "alcohol"), config.negativeKeys)
        assertTrue(config.positiveKeys.contains("sleep"))
        assertTrue(config.positiveKeys.contains("overall_feeling"))
        assertNotNull(config.elements["physical_activity"]?.scale)
        assertEquals(5, config.elements["physical_activity"]?.scale?.size)
        assertNull(config.elements["sleep"]?.scale)
        assertNull(config.elements["overall_feeling"]?.parent)
    }

    @Test
    fun load_nullStream_returnsFallback() {
        val config = EntityConfigLoader.load(null as java.io.InputStream?)

        assertEquals(15.0, config.elements["sleep"]?.weight ?: 0.0, 0.001)
        assertEquals(9, config.elements.size)
        assertNotNull(config.elements["overall_feeling"])
    }

    @Test
    fun load_invalidYaml_returnsFallback() {
        val config = EntityConfigLoader.load(yamlStream("not: valid: yaml: {{{ broken"))

        assertEquals(9, config.elements.size)
        assertEquals(15.0, config.elements["sleep"]?.weight ?: 0.0, 0.001)
    }

    @Test
    fun load_singleElementYaml_mergesWithFallback() {
        val yaml = """
            categories:
              sleep:
                label: "Spánok"
                clickable: true
                weight: 15.0
            elements:
              sleep:
                weight: 20.0
                impact: 1
                parent: sleep
                description: "Spánok test"
                active: true
        """
        val config = EntityConfigLoader.load(yamlStream(yaml))

        assertEquals(20.0, config.elements["sleep"]?.weight ?: 0.0, 0.001)
        // other elements come from fallback
        assertEquals(13.0, config.elements["stress_work"]?.weight ?: 0.0, 0.001)
        assertEquals(9, config.elements.size)
    }

    @Test
    fun load_elementWithNegativeWeight_elementIgnored() {
        val yaml = """
            categories:
              sleep:
                label: "Spánok"
                clickable: true
                weight: 15.0
            elements:
              bad_element:
                weight: -5.0
                impact: 1
                parent: sleep
                description: "Bad"
                active: true
        """
        val config = EntityConfigLoader.load(yamlStream(yaml))

        assertFalse(config.elements.containsKey("bad_element"))
    }

    @Test
    fun load_elementWithUnknownParent_elementIgnored() {
        val yaml = """
            categories:
              sleep:
                label: "Spánok"
                clickable: true
                weight: 15.0
            elements:
              orphan:
                weight: 5.0
                impact: 1
                parent: xyz_nonexistent
                description: "Orphan"
                active: true
        """
        val config = EntityConfigLoader.load(yamlStream(yaml))

        assertFalse(config.elements.containsKey("orphan"))
    }

    @Test
    fun load_elementWithScaleLessThanTwo_scaleIsNull() {
        val yaml = """
            categories:
              sleep:
                label: "Spánok"
                clickable: true
                weight: 15.0
            elements:
              sleep:
                weight: 15.0
                impact: 1
                parent: sleep
                description: "Spánok"
                active: true
                scale: [1]
        """
        val config = EntityConfigLoader.load(yamlStream(yaml))

        assertNull(config.elements["sleep"]?.scale)
    }

    @Test
    fun load_overallFeelingIsRootElement() {
        val config = EntityConfigLoader.load(yamlStream(fullYaml))

        assertNull(config.elements["overall_feeling"]?.parent)
        assertEquals(1, config.elements["overall_feeling"]?.impact)
        assertNotNull(config.elements["overall_feeling"]?.scale)
    }
}
