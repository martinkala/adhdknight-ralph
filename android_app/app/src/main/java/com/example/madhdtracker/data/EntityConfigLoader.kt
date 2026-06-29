package com.example.madhdtracker.data

import android.content.res.AssetManager
import android.util.Log
import com.example.madhdtracker.domain.model.Category
import com.example.madhdtracker.domain.model.Element
import com.example.madhdtracker.domain.model.ElementConfig
import org.yaml.snakeyaml.Yaml
import java.io.InputStream

object EntityConfigLoader {

    fun load(assetManager: AssetManager): ElementConfig =
        try {
            load(assetManager.open("entities.yaml"))
        } catch (e: Exception) {
            Log.d("EntityConfig", "entities.yaml not found, using defaults")
            buildFallback()
        }

    fun load(stream: InputStream?): ElementConfig {
        if (stream == null) {
            Log.d("EntityConfig", "entities.yaml not found, using defaults")
            return buildFallback()
        }
        return try {
            val data: Map<String, Any?> = Yaml().load(stream) ?: emptyMap<String, Any?>()
            parse(data)
        } catch (e: Exception) {
            Log.d("EntityConfig", "entities.yaml parse error: ${e.message}")
            buildFallback()
        }
    }

    private fun parse(data: Map<String, Any?>): ElementConfig {
        val fallback = buildFallback()

        @Suppress("UNCHECKED_CAST")
        val categoryMap = data["categories"] as? Map<String, Any?> ?: emptyMap()
        @Suppress("UNCHECKED_CAST")
        val elementMap = data["elements"] as? Map<String, Any?> ?: emptyMap()

        val parsedCategories = mutableMapOf<String, Category>()
        categoryMap.forEach { (key, value) ->
            @Suppress("UNCHECKED_CAST")
            val props = value as? Map<String, Any?> ?: return@forEach
            val label = props["label"] as? String ?: return@forEach
            val clickable = props["clickable"] as? Boolean ?: false
            val weight = (props["weight"] as? Number)?.toDouble() ?: return@forEach
            if (weight <= 0.0) { Log.d("EntityConfig", "invalid weight for category: $key"); return@forEach }
            parsedCategories[key] = Category(key, label, clickable, weight)
        }

        val mergedCategories = fallback.categories + parsedCategories
        if (mergedCategories.isEmpty()) return fallback

        val parsedElements = mutableMapOf<String, Element>()
        elementMap.forEach { (key, value) ->
            @Suppress("UNCHECKED_CAST")
            val props = value as? Map<String, Any?> ?: return@forEach
            val weight = (props["weight"] as? Number)?.toDouble()
            if (weight == null || weight <= 0.0) {
                Log.d("EntityConfig", "invalid weight for: $key")
                return@forEach
            }
            val impact = (props["impact"] as? Number)?.toInt() ?: return@forEach
            if (impact != 1 && impact != -1) {
                Log.d("EntityConfig", "invalid impact for: $key")
                return@forEach
            }
            val parent = props["parent"] as? String
            if (parent != null && !mergedCategories.containsKey(parent)) {
                Log.d("EntityConfig", "unknown parent: $key")
                return@forEach
            }
            val description = (props["description"] as? String) ?: key
            val active = (props["active"] as? Boolean) ?: true
            @Suppress("UNCHECKED_CAST")
            val scaleRaw = props["scale"] as? List<*>
            val scale = scaleRaw?.mapNotNull { (it as? Number)?.toInt() }?.takeIf { it.size >= 2 }
            Log.d("EntityConfig", "loaded: $key weight=$weight impact=$impact parent=$parent")
            parsedElements[key] = Element(key, weight, impact, parent, description, active, scale)
        }

        val mergedElements = fallback.elements.toMutableMap()
        parsedElements.forEach { (key, element) ->
            if (element.parent == null || mergedCategories.containsKey(element.parent)) {
                mergedElements[key] = element
            }
        }

        if (mergedElements.isEmpty()) return fallback

        val result = ElementConfig(mergedCategories, mergedElements)
        Log.d("EntityConfig", "config loaded: ${result.elements.size} elements, ${result.categories.size} categories")
        return result
    }

    internal fun buildFallback(): ElementConfig {
        val categories = mapOf(
            "sleep" to Category("sleep", "Spánok", true, 15.0),
            "physical_activity" to Category("physical_activity", "Fyzická aktivita", true, 11.0),
            "lifestyle" to Category("lifestyle", "Životný štýl", false, 42.0),
            "head" to Category("head", "Mentálne aktivity", false, 11.0),
            "food" to Category("food", "Strava", false, 8.0)
        )
        val elements = mapOf(
            "overall_feeling" to Element("overall_feeling", DefaultWeights.weights["overall_feeling"] ?: 13.0, 1, null, "Celkový pocit za deň", true, listOf(1, 2, 3, 4, 5)),
            "sleep" to Element("sleep", DefaultWeights.weights["sleep"] ?: 15.0, 1, "sleep", "Kvalitný spánok", true, null),
            "physical_activity" to Element("physical_activity", DefaultWeights.weights["physical_activity"] ?: 11.0, 1, "physical_activity", "Fyzická aktivita", true, listOf(1, 2, 3, 4, 5)),
            "stress_work" to Element("stress_work", DefaultWeights.weights["stress_work"] ?: 13.0, -1, "lifestyle", "Pracovný stres", true, listOf(1, 2, 3, 4, 5)),
            "stress_personal" to Element("stress_personal", DefaultWeights.weights["stress_personal"] ?: 13.0, -1, "lifestyle", "Osobný stres", true, listOf(1, 2, 3, 4, 5)),
            "caffeine" to Element("caffeine", DefaultWeights.weights["caffeine"] ?: 6.0, -1, "lifestyle", "Kofeín", true, listOf(1, 2, 3, 4, 5)),
            "alcohol" to Element("alcohol", DefaultWeights.weights["alcohol"] ?: 10.0, -1, "lifestyle", "Alkohol", true, listOf(1, 2, 3, 4, 5)),
            "nutrition_protein" to Element("nutrition_protein", DefaultWeights.weights["nutrition_protein"] ?: 8.0, 1, "food", "Príjem bielkovín", true, null),
            "mindfulness" to Element("mindfulness", DefaultWeights.weights["mindfulness"] ?: 11.0, 1, "head", "Mindfulness / meditácia", true, null)
        )
        return ElementConfig(categories, elements)
    }
}
