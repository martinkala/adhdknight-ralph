package com.example.madhdtracker.ui

import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.withStyle

object MarkdownRenderer {
    fun toAnnotated(text: String): AnnotatedString {
        return buildAnnotatedString {
            val lines = text.lines()
            lines.forEachIndexed { index, line ->
                val trimmed = line.trim()
                if (trimmed.startsWith("- ")) {
                    append("• ")
                    appendStyledInline(trimmed.removePrefix("- "))
                } else {
                    appendStyledInline(line)
                }
                if (index != lines.lastIndex) {
                    append("\n")
                }
            }
        }
    }

    private fun AnnotatedString.Builder.appendStyledInline(text: String) {
        var i = 0
        while (i < text.length) {
            when {
                text.startsWith("**", i) -> {
                    val end = text.indexOf("**", i + 2)
                    if (end > i + 2) {
                        withStyle(SpanStyle(fontWeight = FontWeight.Bold)) {
                            append(text.substring(i + 2, end))
                        }
                        i = end + 2
                    } else {
                        append(text[i])
                        i += 1
                    }
                }
                text.startsWith("*", i) -> {
                    val end = text.indexOf("*", i + 1)
                    if (end > i + 1) {
                        withStyle(SpanStyle(fontStyle = FontStyle.Italic)) {
                            append(text.substring(i + 1, end))
                        }
                        i = end + 1
                    } else {
                        append(text[i])
                        i += 1
                    }
                }
                else -> {
                    append(text[i])
                    i += 1
                }
            }
        }
    }
}
