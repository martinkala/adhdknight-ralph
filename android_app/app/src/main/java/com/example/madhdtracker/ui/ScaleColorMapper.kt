package com.example.madhdtracker.ui

import androidx.compose.ui.graphics.Color

object ScaleColorMapper {
    /**
     * Maps a scale value to a background color.
     * Intensity level = abs(value) — same absolute value always yields the same shade,
     * regardless of the range. Sign (or impact for positive-only ranges) picks hue.
     */
    fun scaleCardColor(
        value: Int,
        scaleMin: Int,
        scaleMax: Int,
        impact: Int,
        isActive: Boolean
    ): Color {
        if (!isActive) {
            return when {
                impact > 0 -> AppColors.inactiveGreen
                impact < 0 -> AppColors.inactiveRed
                else -> Color.Transparent
            }
        }
        val level = kotlin.math.abs(value)
        return if (scaleMin < 0) {
            when {
                value < 0 -> AppColors.redAt(level)
                value > 0 -> AppColors.greenAt(level)
                else -> Color.Transparent
            }
        } else {
            if (impact >= 0) AppColors.greenAt(level) else AppColors.redAt(level)
        }
    }
}
