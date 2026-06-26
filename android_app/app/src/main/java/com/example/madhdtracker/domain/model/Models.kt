package com.example.madhdtracker.domain.model

import java.time.LocalDate

data class ElementValue(
    val elementKey: String,
    val valueBinary: Int,
    val valueScale: Int?,
    val valueEffective: Double
)

data class DayLog(
    val date: LocalDate,
    val values: List<ElementValue>,
    val satisfactionScale: Int
)

data class WeightProfile(
    val elementKey: String,
    val weightDefault: Double,
    val weightPersonal: Double?
)

data class WeeklySummary(
    val weekStart: String,
    val weekEnd: String,
    val averageIndex: Double
)

data class ActivityDescription(
    val elementKey: String,
    val title: String,
    val descriptionMarkdown: String
)
