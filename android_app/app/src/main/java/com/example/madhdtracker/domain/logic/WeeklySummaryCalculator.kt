package com.example.madhdtracker.domain.logic

import com.example.madhdtracker.data.DailyIndexRow

object WeeklySummaryCalculator {
    fun average(series: List<DailyIndexRow>): Double? {
        if (series.isEmpty()) return null
        return series.map { it.indexValue }.average()
    }

    fun weekStart(series: List<DailyIndexRow>): String? {
        return series.lastOrNull()?.date
    }

    fun weekEnd(series: List<DailyIndexRow>): String? {
        return series.firstOrNull()?.date
    }
}
