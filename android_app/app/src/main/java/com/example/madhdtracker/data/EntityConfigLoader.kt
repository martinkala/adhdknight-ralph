package com.example.madhdtracker.data

import android.content.Context
import android.content.res.AssetManager
import android.util.Log
import com.example.madhdtracker.domain.model.EntityConfig
import com.example.madhdtracker.domain.model.EntityNode
import org.yaml.snakeyaml.Yaml
import java.io.File
import java.io.InputStream

object EntityConfigLoader {

    const val OVERRIDE_FILE_NAME = "entities_override.yaml"

    // Server-downloaded config (see EntitiesConfigRepository) takes precedence over the
    // bundled asset once present — this is what makes the server the source of truth while
    // still letting the app work offline from first launch on the bundled copy.
    fun load(context: Context): EntityConfig {
        val overrideFile = File(context.filesDir, OVERRIDE_FILE_NAME)
        if (overrideFile.exists()) {
            try {
                return load(overrideFile.inputStream())
            } catch (e: Exception) {
                Log.d("EntityConfig", "override file unreadable, falling back to bundled asset: ${e.message}")
            }
        }
        return load(context.assets)
    }

    // Persists a server-downloaded entities.yaml as the override — caller is expected to
    // have already validated it parses (e.g. via load(text.byteInputStream())) before
    // calling this, so a malformed remote response can never brick the local config.
    fun saveOverride(context: Context, yamlText: String) {
        File(context.filesDir, OVERRIDE_FILE_NAME).writeText(yamlText)
    }

    // Semver-style comparison ("1.10" > "1.9"), tolerant of non-numeric segments (treated as 0).
    fun isNewerVersion(remoteVersion: String, localVersion: String): Boolean {
        fun parts(v: String) = v.trim().split(".").map { it.takeWhile(Char::isDigit).toIntOrNull() ?: 0 }
        val remoteParts = parts(remoteVersion)
        val localParts = parts(localVersion)
        for (i in 0 until maxOf(remoteParts.size, localParts.size)) {
            val r = remoteParts.getOrElse(i) { 0 }
            val l = localParts.getOrElse(i) { 0 }
            if (r != l) return r > l
        }
        return false
    }

    fun load(assetManager: AssetManager): EntityConfig =
        try {
            load(assetManager.open("entities.yaml"))
        } catch (e: Exception) {
            Log.d("EntityConfig", "entities.yaml not found, using defaults")
            buildFallback()
        }

    fun load(stream: InputStream?): EntityConfig {
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

    private fun parse(data: Map<String, Any?>): EntityConfig {
        @Suppress("UNCHECKED_CAST")
        val nodeMap = data["nodes"] as? Map<String, Any?>
        if (nodeMap == null) {
            Log.d("EntityConfig", "no 'nodes:' section found, using defaults")
            return buildFallback()
        }

        @Suppress("UNCHECKED_CAST")
        val metadata = data["metadata"] as? Map<String, Any?>
        val version = metadata?.get("version")?.toString() ?: "0"

        val parsedNodes = mutableMapOf<String, EntityNode>()

        // Nodes may nest their subcategories under `children:` (tree form) and/or declare
        // `parent:` directly (flat form, kept for backward compatibility). Both are merged
        // into the same flat `parsedNodes` map that the rest of the app operates on.
        fun parseNode(key: String, props: Map<String, Any?>, inheritedParent: String?) {
            val weight = (props["weight"] as? Number)?.toDouble()
            if (weight == null || weight <= 0.0) {
                Log.d("EntityConfig", "invalid weight for node: $key")
                return
            }
            val impact = (props["impact"] as? Number)?.toInt()
            if (impact != null && impact != 1 && impact != -1) {
                Log.d("EntityConfig", "invalid impact for node: $key")
                return
            }
            val parent = (props["parent"] as? String) ?: inheritedParent
            val label = (props["label"] as? String) ?: key
            val active = (props["active"] as? Boolean) ?: true
            val clickable = (props["clickable"] as? Boolean) ?: false
            @Suppress("UNCHECKED_CAST")
            val scaleRaw = props["scale"] as? List<*>
            val scale = scaleRaw?.mapNotNull { (it as? Number)?.toInt() }?.takeIf { it.size >= 2 }
            val scaleMin = (props["scale_min"] as? Number)?.toInt()
                ?: scale?.minOrNull()
                ?: 1
            val scaleMax = (props["scale_max"] as? Number)?.toInt()
                ?: scale?.maxOrNull()
                ?: 5
            parsedNodes[key] = EntityNode(
                key = key,
                weight = weight,
                impact = impact,
                parent = parent,
                label = label,
                active = active,
                scale = scale,
                clickable = clickable,
                scaleMin = scaleMin,
                scaleMax = scaleMax
            )

            @Suppress("UNCHECKED_CAST")
            val children = props["children"] as? Map<String, Any?>
            children?.forEach { (childKey, childValue) ->
                val childProps = childValue as? Map<String, Any?> ?: return@forEach
                parseNode(childKey, childProps, key)
            }
        }

        nodeMap.forEach { (key, value) ->
            @Suppress("UNCHECKED_CAST")
            val props = value as? Map<String, Any?> ?: return@forEach
            parseNode(key, props, null)
        }

        // Validate: parent references exist
        parsedNodes.forEach { (key, node) ->
            if (node.parent != null && !parsedNodes.containsKey(node.parent)) {
                Log.d("EntityConfig", "unknown parent '${node.parent}' for node: $key — removing")
                parsedNodes.remove(key)
            }
        }

        // Validate: overall_feeling must be present
        if (!parsedNodes.containsKey("overall_feeling")) {
            Log.d("EntityConfig", "overall_feeling missing — using fallback")
            return buildFallback()
        }

        if (parsedNodes.isEmpty()) return buildFallback()

        Log.d("EntityConfig", "config loaded: ${parsedNodes.size} nodes, version=$version")
        return EntityConfig(parsedNodes, version)
    }

    internal fun buildFallback(): EntityConfig {
        val nodes = mapOf(
            "overall_feeling" to EntityNode("overall_feeling", 13.0, 1, null, "Celkový pocit za deň", true, listOf(1, 2, 3, 4, 5), false),
            "sleep" to EntityNode("sleep", 15.0, 1, null, "Spánok", true, listOf(-2, -1, 0, 1, 2), true, scaleMin = -2, scaleMax = 2),
            "physical_activity" to EntityNode("physical_activity", 11.0, 1, null, "Fyzická aktivita", true, listOf(1, 2, 3, 4, 5), true),
            "lifestyle" to EntityNode("lifestyle", 42.0, null, null, "Životný štýl", true, null, false),
            "stress_work" to EntityNode("stress_work", 13.0, -1, "lifestyle", "Pracovný stres", true, listOf(1, 2, 3, 4, 5), false),
            "stress_personal" to EntityNode("stress_personal", 13.0, -1, "lifestyle", "Osobný stres", true, listOf(1, 2, 3, 4, 5), false),
            "caffeine" to EntityNode("caffeine", 6.0, -1, "lifestyle", "Kofeín", true, listOf(1, 2, 3, 4, 5), false),
            "alcohol" to EntityNode("alcohol", 10.0, -1, "lifestyle", "Alkohol", true, listOf(1, 2, 3, 4, 5), false),
            "food" to EntityNode("food", 8.0, null, null, "Strava", true, null, false),
            "nutrition_protein" to EntityNode("nutrition_protein", 8.0, 1, "food", "Príjem bielkovín", true, null, false),
            "head" to EntityNode("head", 11.0, null, null, "Mentálne aktivity", true, null, false),
            "mindfulness" to EntityNode("mindfulness", 11.0, 1, "head", "Mindfulness / meditácia", true, null, false)
        )
        return EntityConfig(nodes)
    }
}
