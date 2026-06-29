package com.example.madhdtracker.domain.logic

import com.example.madhdtracker.domain.model.AsrsConfig

object AsrsRecalibrator {
    fun shouldRecalibrate(asrsScores: List<Int>, indexAverages: List<Double>, config: AsrsConfig): Boolean {
        val n = config.consecutiveMeasurements
        if (asrsScores.size < n || indexAverages.size < n) return false
        val latestAsrs = asrsScores.takeLast(n)
        val latestIndex = indexAverages.takeLast(n)
        val deltas = latestAsrs.zip(latestIndex).map { (asrs, idx) ->
            kotlin.math.abs(asrs - idx)
        }
        return deltas.all { it > config.deltaThreshold }
    }

    fun alphaForRecalibration(config: AsrsConfig): Double =
        config.recalibrationAlpha.coerceAtLeast(config.recalibrationAlpha)
}
