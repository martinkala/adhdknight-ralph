package com.example.madhdtracker.data

data class DailyIndexRow(
    val date: String,
    val indexValue: Double
)

data class NotificationDecision(
    val type: String,
    val message: String
)

data class DailySubIndexRow(
    val date: String,
    val positiveIndex: Double?,
    val negativeIndex: Double?
)
