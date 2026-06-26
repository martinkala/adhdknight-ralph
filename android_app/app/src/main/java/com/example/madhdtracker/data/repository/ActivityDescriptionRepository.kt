package com.example.madhdtracker.data.repository

import android.content.Context
import com.example.madhdtracker.R
import java.util.concurrent.ConcurrentHashMap

class ActivityDescriptionRepository(
    private val context: Context
) {
    private val cache = ConcurrentHashMap<String, String>()
    private var loaded = false

    fun getDescription(key: String): String? {
        ensureLoaded()
        return cache[key]
    }

    fun getAll(): Map<String, String> {
        ensureLoaded()
        return cache.toMap()
    }

    private fun ensureLoaded() {
        if (loaded) return
        val text = context.resources.openRawResource(R.raw.activity_descriptions)
            .bufferedReader()
            .use { it.readText() }
        parseMarkdownSections(text).forEach { (key, value) ->
            cache[key] = value.trim()
        }
        loaded = true
    }

    private fun parseMarkdownSections(text: String): Map<String, String> {
        val result = LinkedHashMap<String, String>()
        var currentKey: String? = null
        val buffer = StringBuilder()

        fun flush() {
            val key = currentKey ?: return
            result[key] = buffer.toString().trim()
            buffer.setLength(0)
        }

        text.lineSequence().forEach { line ->
            val trimmed = line.trim()
            if (trimmed.startsWith("## ")) {
                flush()
                currentKey = trimmed.removePrefix("## ").trim()
            } else if (currentKey != null) {
                buffer.appendLine(line)
            }
        }
        flush()
        return result
    }
}
