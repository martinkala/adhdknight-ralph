package com.example.madhdtracker.domain.logic

import com.example.madhdtracker.data.EventValueEntity
import com.example.madhdtracker.data.WeightEntity
import com.example.madhdtracker.domain.model.AdaptationConfig
import com.example.madhdtracker.domain.model.ElementConfig
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

    fun computeDailyIndexGrouped(
        values: List<EventValueEntity>,
        elementConfig: ElementConfig,
        activeKeys: Set<String>
    ): Double? {
        if (values.isEmpty()) return null

        val activeValues = values.filter { it.elementKey in activeKeys }
        if (activeValues.isEmpty()) return null

        val valueMap = activeValues.associateBy { it.elementKey }
        var totalContribution = 0.0
        var totalWeight = 0.0

        // Root elements (parent == null) contribute directly
        elementConfig.elements.values
            .filter { it.parent == null && it.key in activeKeys }
            .forEach { element ->
                val v = valueMap[element.key] ?: return@forEach
                val effective = if (element.impact < 0) 1.0 - v.valueEffective else v.valueEffective
                totalContribution += element.weight * effective
                totalWeight += element.weight
            }

        // Category groups: group_avg × category.weight
        val elementsByCategory = elementConfig.elements.values
            .filter { it.parent != null && it.key in activeKeys }
            .groupBy { it.parent!! }

        elementsByCategory.forEach { (categoryKey, elements) ->
            val category = elementConfig.categories[categoryKey] ?: return@forEach
            var groupWeightedSum = 0.0
            var groupWeightSum = 0.0
            elements.forEach elementLoop@{ element ->
                val v = valueMap[element.key] ?: return@elementLoop
                val effective = if (element.impact < 0) 1.0 - v.valueEffective else v.valueEffective
                groupWeightedSum += element.weight * effective
                groupWeightSum += element.weight
            }
            if (groupWeightSum <= 0.0) return@forEach
            val groupAvg = groupWeightedSum / groupWeightSum
            totalContribution += groupAvg * category.weight
            totalWeight += category.weight
        }

        if (totalWeight <= 0.0) return null
        return (totalContribution / totalWeight) * 100.0
    }

    fun adaptWeights(
        defaultWeights: Map<String, Double>,
        currentWeights: Map<String, Double>,
        history: List<Map<String, Double>>,
        adaptation: AdaptationConfig,
        overallKey: String = "overall_feeling"
    ): Map<String, Double> {
        if (history.size < adaptation.minHistoryDays) return currentWeights
        val overallSeries = history.mapNotNull { it[overallKey] }
        if (overallSeries.size < adaptation.minSeriesSize) return currentWeights

        val updated = currentWeights.mapValues { (key, current) ->
            val series = history.mapNotNull { it[key] }
            if (series.size < adaptation.minSeriesSize || series.size != overallSeries.size) return@mapValues current
            val corr = pearson(series, overallSeries)
            if (abs(corr) < adaptation.correlationThreshold) return@mapValues current
            val base = defaultWeights[key] ?: current
            val next = current * (1 + adaptation.alpha * corr)
            clamp(next, adaptation.clampMinFactor * base, adaptation.clampMaxFactor * base)
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
