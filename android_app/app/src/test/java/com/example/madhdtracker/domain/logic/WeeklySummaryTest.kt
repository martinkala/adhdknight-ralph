package com.example.madhdtracker.domain.logic

import com.example.madhdtracker.data.DailyIndexRow
import org.junit.Assert.assertEquals
import org.junit.Test

class WeeklySummaryTest {
    @Test
    fun average_returnsMeanOfSeries() {
        val series = listOf(
            DailyIndexRow("2026-01-01", 20.0),
            DailyIndexRow("2026-01-02", 40.0)
        )
        val avg = WeeklySummaryCalculator.average(series)
        assertEquals(30.0, avg ?: 0.0, 0.0001)
    }
}
