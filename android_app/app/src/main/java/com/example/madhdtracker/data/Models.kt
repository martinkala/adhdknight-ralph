package com.example.madhdtracker.data

data class DailyIndexRow(
    val date: String,
    val indexValue: Double
)

data class NotificationDecision(
    val type: String,
    val message: String
)
