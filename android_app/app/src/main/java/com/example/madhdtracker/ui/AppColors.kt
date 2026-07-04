package com.example.madhdtracker.ui

import androidx.compose.ui.graphics.Color

/**
 * Global color palette for scale visualization.
 * Intensity level = abs(value), sign determines hue (green / red).
 * Level 0 = neutral/transparent, levels 1-5 = increasing intensity.
 */
object AppColors {
    private val greenBase = Color(0xFF4CAF50) // Material Green 500
    private val redBase   = Color(0xFFF44336) // Material Red 500

    val inactiveGreen = greenBase.copy(alpha = 0.05f)
    val inactiveRed   = redBase.copy(alpha = 0.05f)

    /** Index = abs(value). green[0] = transparent, green[1..5] = light → saturated. */
    val green = listOf(
        Color.Transparent,
        greenBase.copy(alpha = 0.14f),
        greenBase.copy(alpha = 0.26f),
        greenBase.copy(alpha = 0.38f),
        greenBase.copy(alpha = 0.50f),
        greenBase.copy(alpha = 0.62f),
    )

    /** Index = abs(value). red[0] = transparent, red[1..5] = light → saturated. */
    val red = listOf(
        Color.Transparent,
        redBase.copy(alpha = 0.14f),
        redBase.copy(alpha = 0.26f),
        redBase.copy(alpha = 0.38f),
        redBase.copy(alpha = 0.50f),
        redBase.copy(alpha = 0.62f),
    )

    /** Safe lookup — clamps index to valid range. */
    fun greenAt(level: Int): Color = green.getOrElse(level.coerceIn(0, green.lastIndex)) { green.last() }
    fun redAt(level: Int): Color   = red.getOrElse(level.coerceIn(0, red.lastIndex)) { red.last() }
}
