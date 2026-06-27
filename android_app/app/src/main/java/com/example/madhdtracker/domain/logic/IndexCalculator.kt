package com.example.madhdtracker.domain.logic

import com.example.madhdtracker.data.EventValueEntity
import com.example.madhdtracker.data.WeightEntity
import kotlin.math.abs
import kotlin.math.max
import kotlin.math.min

object IndexCalculator {
    fun valueEffective(valueBinary: Int, valueScale: Int?): Double {
        return valueScale?.let { (it - 1) / 4.0 } ?: valueBinary.toDouble()
    }

    fun computeDailyIndex(
        values: List<EventValueEntity>,
        weights: Map<String, WeightEntity>,
        negativeKeys: Set<String>
    ): Double? {
        if (values.isEmpty() || weights.isEmpty()) return null
        var weightedSum = 0.0
        var weightSum = 0.0
        values.forEach { v ->
            val weight = weights[v.elementKey]?.weightPersonal ?: weights[v.elementKey]?.weightDefault
            if (weight != null) {
                val effective = if (v.elementKey in negativeKeys) 1.0 - v.valueEffective else v.valueEffective
                weightedSum += weight * effective
                weightSum += weight
            }
        }
        if (weightSum <= 0.0) return null
        return (weightedSum / weightSum) * 100.0
    }

    fun adaptWeights(
        defaultWeights: Map<String, Double>,
        currentWeights: Map<String, Double>,
        history: List<Map<String, Double>>,
        overallKey: String = "overall_feeling",
        alpha: Double = 0.2
    ): Map<String, Double> {
        if (history.size < 15) return currentWeights
        val overallSeries = history.mapNotNull { it[overallKey] }
        if (overallSeries.size < 5) return currentWeights

        val updated = currentWeights.mapValues { (key, current) ->
            val series = history.mapNotNull { it[key] }
            if (series.size < 5 || series.size != overallSeries.size) return@mapValues current
            val corr = pearson(series, overallSeries)
            if (abs(corr) < 0.1) return@mapValues current
            val base = defaultWeights[key] ?: current
            val next = current * (1 + alpha * corr)
            clamp(next, 0.5 * base, 2.0 * base)
        }

        val defaultSum = defaultWeights.values.sum().takeIf { it > 0 } ?: return updated
        val updatedSum = updated.values.sum().takeIf { it > 0 } ?: return updated
        val scale = defaultSum / updatedSum
        return updated.mapValues { (_, value) -> value * scale }
    }

    fun computePositiveIndex(
        values: List<EventValueEntity>,
        weights: Map<String, WeightEntity>,
        positiveKeys: Set<String>
    ): Double? {
        val filtered = values.filter { it.elementKey in positiveKeys }
        if (filtered.isEmpty()) return null
        var weightedSum = 0.0
        var weightSum = 0.0
        filtered.forEach { v ->
            val weight = weights[v.elementKey]?.weightPersonal ?: weights[v.elementKey]?.weightDefault
            if (weight != null) {
                weightedSum += weight * v.valueEffective
                weightSum += weight
            }
        }
        if (weightSum <= 0.0) return null
        return (weightedSum / weightSum) * 100.0
    }

    fun computeNegativeIndex(
        values: List<EventValueEntity>,
        weights: Map<String, WeightEntity>,
        negativeKeys: Set<String>
    ): Double? {
        val filtered = values.filter { it.elementKey in negativeKeys }
        if (filtered.isEmpty()) return null
        var weightedSum = 0.0
        var weightSum = 0.0
        filtered.forEach { v ->
            val weight = weights[v.elementKey]?.weightPersonal ?: weights[v.elementKey]?.weightDefault
            if (weight != null) {
                weightedSum += weight * v.valueEffective
                weightSum += weight
            }
        }
        if (weightSum <= 0.0) return null
        return (weightedSum / weightSum) * 100.0
    }

    private fun clamp(value: Double, minValue: Double, maxValue: Double): Double {
        return max(minValue, min(maxValue, value))
    }

    private fun pearson(xs: List<Double>, ys: List<Double>): Double {
        val n = min(xs.size, ys.size)
        if (n == 0) return 0.0
        val x = xs.take(n)
        val y = ys.take(n)
        val meanX = x.average()
        val meanY = y.average()
        var num = 0.0
        var denomX = 0.0
        var denomY = 0.0
        for (i in 0 until n) {
            val dx = x[i] - meanX
            val dy = y[i] - meanY
            num += dx * dy
            denomX += dx * dx
            denomY += dy * dy
        }
        val denom = kotlin.math.sqrt(denomX * denomY)
        return if (denom == 0.0) 0.0 else num / denom
    }
}
