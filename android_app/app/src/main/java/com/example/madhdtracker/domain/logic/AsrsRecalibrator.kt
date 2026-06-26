package com.example.madhdtracker.domain.logic

object AsrsRecalibrator {
    fun shouldRecalibrate(asrsScores: List<Int>, indexAverages: List<Double>): Boolean {
        if (asrsScores.size < 2 || indexAverages.size < 2) return false
        val latestAsrs = asrsScores.takeLast(2)
        val latestIndex = indexAverages.takeLast(2)
        val deltas = latestAsrs.zip(latestIndex).map { (asrs, idx) ->
            kotlin.math.abs(asrs - idx)
        }
        return deltas.all { it > 10.0 }
    }

    fun alphaForRecalibration(defaultAlpha: Double = 0.2): Double {
        return 0.3.coerceAtLeast(defaultAlpha)
    }
}
