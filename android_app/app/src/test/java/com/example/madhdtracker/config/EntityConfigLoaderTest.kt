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
        nodes:
          overall_feeling:
            label: "Celkový pocit za deň"
            weight: 13.0
            impact: 1
            active: true
            scale: [1, 2, 3, 4, 5]
          sleep:
            label: "Spánok"
            weight: 15.0
            impact: 1
            active: true
            clickable: true
          physical_activity:
            label: "Fyzická aktivita"
            weight: 11.0
            impact: 1
            active: true
            scale: [1, 2, 3, 4, 5]
            clickable: true
          lifestyle:
            label: "Životný štýl"
            weight: 42.0
          stress_work:
            label: "Pracovný stres"
            weight: 13.0
            impact: -1
            parent: lifestyle
            active: true
            scale: [1, 2, 3, 4, 5]
          stress_personal:
            label: "Osobný stres"
            weight: 13.0
            impact: -1
            parent: lifestyle
            active: true
            scale: [1, 2, 3, 4, 5]
          caffeine:
            label: "Kofeín"
            weight: 6.0
            impact: -1
            parent: food
            active: true
            scale: [1, 2, 3, 4, 5]
          alcohol:
            label: "Alkohol"
            weight: 10.0
            impact: -1
            parent: food
            active: true
            scale: [1, 2, 3, 4, 5]
          food:
            label: "Strava"
            weight: 8.0
          nutrition_protein:
            label: "Príjem bielkovín"
            weight: 8.0
            impact: 1
            parent: food
            active: true
          head:
            label: "Mentálne aktivity"
            weight: 11.0
          mindfulness:
            label: "Mindfulness / meditácia"
            weight: 11.0
            impact: 1
            parent: head
            active: true
    """

    @Test
    fun load_validNodesYaml_returnsCorrectConfig() {
        val config = EntityConfigLoader.load(yamlStream(fullYaml))

        assertEquals(15.0, config.nodes["sleep"]?.weight ?: 0.0, 0.001)
        assertEquals(12, config.nodes.size)
        assertEquals(setOf("stress_work", "stress_personal", "caffeine", "alcohol"), config.negativeKeys)
        assertTrue(config.positiveKeys.contains("sleep"))
        assertTrue(config.positiveKeys.contains("overall_feeling"))
        assertNotNull(config.nodes["physical_activity"]?.scale)
        assertEquals(5, config.nodes["physical_activity"]?.scale?.size)
        assertNull(config.nodes["sleep"]?.scale)
        assertNull(config.nodes["overall_feeling"]?.parent)
        assertNull(config.nodes["lifestyle"]?.impact)
    }

    @Test
    fun load_nullStream_returnsFallback() {
        val config = EntityConfigLoader.load(null as java.io.InputStream?)

        assertEquals(15.0, config.nodes["sleep"]?.weight ?: 0.0, 0.001)
        assertNotNull(config.nodes["overall_feeling"])
        assertTrue(config.trackableNodes.isNotEmpty())
    }

    @Test
    fun load_invalidYaml_returnsFallback() {
        val config = EntityConfigLoader.load(yamlStream("not: valid: yaml: {{{ broken"))

        assertEquals(15.0, config.nodes["sleep"]?.weight ?: 0.0, 0.001)
        assertNotNull(config.nodes["overall_feeling"])
    }

    @Test
    fun load_missingNodesSection_returnsFallback() {
        val yaml = """
            categories:
              sleep:
                label: "Spánok"
                weight: 15.0
        """
        val config = EntityConfigLoader.load(yamlStream(yaml))

        assertNotNull(config.nodes["overall_feeling"])
        assertTrue(config.trackableNodes.isNotEmpty())
    }

    @Test
    fun load_nodeWithNegativeWeight_nodeIgnored() {
        val yaml = """
            nodes:
              overall_feeling:
                label: "Celkový pocit"
                weight: 13.0
                impact: 1
                active: true
                scale: [1, 2, 3, 4, 5]
              bad_node:
                label: "Bad"
                weight: -5.0
                impact: 1
                active: true
        """
        val config = EntityConfigLoader.load(yamlStream(yaml))

        assertFalse(config.nodes.containsKey("bad_node"))
        assertTrue(config.nodes.containsKey("overall_feeling"))
    }

    @Test
    fun load_nodeWithUnknownParent_nodeIgnored() {
        val yaml = """
            nodes:
              overall_feeling:
                label: "Celkový pocit"
                weight: 13.0
                impact: 1
                active: true
                scale: [1, 2, 3, 4, 5]
              orphan:
                label: "Orphan"
                weight: 5.0
                impact: 1
                parent: xyz_nonexistent
                active: true
        """
        val config = EntityConfigLoader.load(yamlStream(yaml))

        assertFalse(config.nodes.containsKey("orphan"))
    }

    @Test
    fun load_nodeWithScaleLessThanTwo_scaleIsNull() {
        val yaml = """
            nodes:
              overall_feeling:
                label: "Celkový pocit"
                weight: 13.0
                impact: 1
                active: true
                scale: [1, 2, 3, 4, 5]
              sleep:
                label: "Spánok"
                weight: 15.0
                impact: 1
                active: true
                scale: [1]
        """
        val config = EntityConfigLoader.load(yamlStream(yaml))

        assertNull(config.nodes["sleep"]?.scale)
    }

    @Test
    fun load_missingOverallFeeling_returnsFallback() {
        val yaml = """
            nodes:
              sleep:
                label: "Spánok"
                weight: 15.0
                impact: 1
                active: true
        """
        val config = EntityConfigLoader.load(yamlStream(yaml))

        assertNotNull(config.nodes["overall_feeling"])
    }

    @Test
    fun load_overallFeelingIsRootTrackableNode() {
        val config = EntityConfigLoader.load(yamlStream(fullYaml))

        val node = config.nodes["overall_feeling"]
        assertNull(node?.parent)
        assertEquals(1, node?.impact)
        assertNotNull(node?.scale)
    }

    @Test
    fun load_groupNodeHasNullImpact() {
        val config = EntityConfigLoader.load(yamlStream(fullYaml))

        assertNull(config.nodes["lifestyle"]?.impact)
        assertTrue(config.groupNodes.containsKey("lifestyle"))
        assertFalse(config.trackableNodes.containsKey("lifestyle"))
    }

    @Test
    fun load_trackableNodesExcludeGroupNodes() {
        val config = EntityConfigLoader.load(yamlStream(fullYaml))

        config.trackableNodes.values.forEach { node ->
            assertNotNull("Trackable node ${node.key} has null impact", node.impact)
        }
        config.groupNodes.values.forEach { node ->
            assertNull("Group node ${node.key} has non-null impact", node.impact)
        }
    }
}
