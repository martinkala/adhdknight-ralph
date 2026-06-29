package com.example.madhdtracker.domain.model

data class AppConfig(
    val weights: Map<String, Double>,
    val elementClassification: ElementClassification,
    val adaptation: AdaptationConfig,
    val asrs: AsrsConfig,
    val notification: NotificationConfig
)

data class ElementClassification(
    val negativeKeys: Set<String>,
    val positiveKeys: Set<String>
)

data class AdaptationConfig(
    val alpha: Double,
    val clampMinFactor: Double,
    val clampMaxFactor: Double,
    val correlationThreshold: Double,
    val minHistoryDays: Int,
    val minSeriesSize: Int
)

data class AsrsConfig(
    val deltaThreshold: Double,
    val consecutiveMeasurements: Int,
    val recalibrationAlpha: Double
)

data class NotificationConfig(
    val quietStartHour: Int,
    val quietStartMinute: Int,
    val quietEndHour: Int,
    val quietEndMinute: Int,
    val stressThresholdScale: Int,
    val neglectedAreaDays: Int,
    val stressRecoveryDays: Int
)
