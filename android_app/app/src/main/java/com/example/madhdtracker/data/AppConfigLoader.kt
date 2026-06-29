package com.example.madhdtracker.data

import android.content.res.AssetManager
import android.util.Log
import com.example.madhdtracker.domain.model.AdaptationConfig
import com.example.madhdtracker.domain.model.AppConfig
import com.example.madhdtracker.domain.model.AsrsConfig
import com.example.madhdtracker.domain.model.ElementClassification
import com.example.madhdtracker.domain.model.NotificationConfig
import org.json.JSONObject
import java.io.InputStream

private const val TAG = "AppConfig"

object AppConfigLoader {

    fun load(assetManager: AssetManager): AppConfig =
        load(runCatching { assetManager.open("app_config.json") }.getOrNull())

    fun load(stream: InputStream?): AppConfig {
        if (stream == null) {
            Log.d(TAG, "config not found, using defaults")
            return defaults()
        }
        val json = runCatching {
            JSONObject(stream.bufferedReader().use { it.readText() })
        }.getOrElse { e ->
            Log.d(TAG, "config parse error: ${e.message}, using defaults")
            return defaults()
        }
        Log.d(TAG, "config loaded successfully")
        return buildConfig(json)
    }

    private fun buildConfig(json: JSONObject): AppConfig {
        val weights = parseWeights(json.optJSONObject("weights"))
        val classification = parseClassification(json.optJSONObject("element_classification"), weights.keys)
        val adaptation = parseAdaptation(json.optJSONObject("adaptation"))
        val asrs = parseAsrs(json.optJSONObject("asrs"))
        val notification = parseNotification(json.optJSONObject("notification"))
        return AppConfig(weights, classification, adaptation, asrs, notification)
    }

    private fun parseWeights(obj: JSONObject?): Map<String, Double> {
        val result = DefaultWeights.weights.toMutableMap()
        if (obj == null) {
            result.forEach { (k, v) -> Log.d(TAG, "using default for weights.$k: $v") }
            return result
        }
        DefaultWeights.weights.keys.forEach { key ->
            if (obj.has(key)) {
                val value = obj.getDouble(key)
                if (value > 0) {
                    result[key] = value
                    Log.d(TAG, "loaded from config: weights.$key=$value")
                } else {
                    Log.d(TAG, "invalid value for weights.$key ($value), using default ${DefaultWeights.weights[key]}")
                }
            } else {
                Log.d(TAG, "using default for weights.$key: ${DefaultWeights.weights[key]}")
            }
        }
        val sum = result.values.sum()
        if (sum < 95.0 || sum > 105.0) {
            Log.d(TAG, "weights sum=$sum outside (95,105), normalizing")
            val scale = DefaultWeights.weights.values.sum() / sum
            result.replaceAll { _, v -> v * scale }
        }
        return result
    }

    private fun parseClassification(obj: JSONObject?, allKeys: Set<String>): ElementClassification {
        val defaultNeg = DefaultWeights.negativeKeys
        val negativeKeys: Set<String> = if (obj != null && obj.has("negative_keys")) {
            val arr = obj.getJSONArray("negative_keys")
            val parsed = (0 until arr.length()).map { arr.getString(it) }.filter { it in allKeys }.toSet()
            Log.d(TAG, "loaded from config: negative_keys=$parsed")
            parsed
        } else {
            Log.d(TAG, "using default for negative_keys: $defaultNeg")
            defaultNeg
        }
        return ElementClassification(
            negativeKeys = negativeKeys,
            positiveKeys = allKeys - negativeKeys
        )
    }

    private fun parseAdaptation(obj: JSONObject?): AdaptationConfig {
        val d = defaultAdaptation()
        if (obj == null) {
            Log.d(TAG, "using default for adaptation (section missing)")
            return d
        }
        val alpha = obj.optDoubleOrNull("alpha").let {
            if (it != null && it > 0.0 && it <= 1.0) { Log.d(TAG, "loaded from config: alpha=$it"); it }
            else { Log.d(TAG, "invalid/missing alpha, using default ${d.alpha}"); d.alpha }
        }
        val clampMin = obj.optDoubleOrNull("clamp_min_factor") ?: run {
            Log.d(TAG, "using default for clamp_min_factor: ${d.clampMinFactor}"); d.clampMinFactor
        }
        val clampMax = obj.optDoubleOrNull("clamp_max_factor") ?: run {
            Log.d(TAG, "using default for clamp_max_factor: ${d.clampMaxFactor}"); d.clampMaxFactor
        }
        val (resolvedMin, resolvedMax) = if (clampMin >= clampMax) {
            Log.d(TAG, "clamp_min_factor >= clamp_max_factor, using defaults")
            d.clampMinFactor to d.clampMaxFactor
        } else {
            if (obj.has("clamp_min_factor")) Log.d(TAG, "loaded from config: clamp_min_factor=$clampMin")
            if (obj.has("clamp_max_factor")) Log.d(TAG, "loaded from config: clamp_max_factor=$clampMax")
            clampMin to clampMax
        }
        val corrThresh = obj.optDoubleOrNull("correlation_threshold").let {
            if (it != null && it > 0.0) { Log.d(TAG, "loaded from config: correlation_threshold=$it"); it }
            else { Log.d(TAG, "invalid/missing correlation_threshold, using default ${d.correlationThreshold}"); d.correlationThreshold }
        }
        val minHist = obj.optIntOrNull("min_history_days").let {
            if (it != null && it >= 1) { Log.d(TAG, "loaded from config: min_history_days=$it"); it }
            else { Log.d(TAG, "invalid/missing min_history_days, using default ${d.minHistoryDays}"); d.minHistoryDays }
        }
        val minSeries = obj.optIntOrNull("min_series_size").let {
            if (it != null && it >= 1) { Log.d(TAG, "loaded from config: min_series_size=$it"); it }
            else { Log.d(TAG, "invalid/missing min_series_size, using default ${d.minSeriesSize}"); d.minSeriesSize }
        }
        return AdaptationConfig(alpha, resolvedMin, resolvedMax, corrThresh, minHist, minSeries)
    }

    private fun parseAsrs(obj: JSONObject?): AsrsConfig {
        val d = defaultAsrs()
        if (obj == null) {
            Log.d(TAG, "using default for asrs (section missing)")
            return d
        }
        val delta = obj.optDoubleOrNull("delta_threshold").let {
            if (it != null && it > 0.0) { Log.d(TAG, "loaded from config: delta_threshold=$it"); it }
            else { Log.d(TAG, "invalid/missing delta_threshold, using default ${d.deltaThreshold}"); d.deltaThreshold }
        }
        val consec = obj.optIntOrNull("consecutive_measurements").let {
            if (it != null && it >= 1) { Log.d(TAG, "loaded from config: consecutive_measurements=$it"); it }
            else { Log.d(TAG, "invalid/missing consecutive_measurements, using default ${d.consecutiveMeasurements}"); d.consecutiveMeasurements }
        }
        val recalAlpha = obj.optDoubleOrNull("recalibration_alpha").let {
            if (it != null && it > 0.0 && it <= 1.0) { Log.d(TAG, "loaded from config: recalibration_alpha=$it"); it }
            else { Log.d(TAG, "invalid/missing recalibration_alpha, using default ${d.recalibrationAlpha}"); d.recalibrationAlpha }
        }
        return AsrsConfig(delta, consec, recalAlpha)
    }

    private fun parseNotification(obj: JSONObject?): NotificationConfig {
        val d = defaultNotification()
        if (obj == null) {
            Log.d(TAG, "using default for notification (section missing)")
            return d
        }
        fun hour(key: String, default: Int): Int {
            val v = obj.optIntOrNull(key)
            return if (v != null && v in 0..23) { Log.d(TAG, "loaded from config: $key=$v"); v }
            else { Log.d(TAG, "invalid/missing $key, using default $default"); default }
        }
        fun minute(key: String, default: Int): Int {
            val v = obj.optIntOrNull(key)
            return if (v != null && v in 0..59) { Log.d(TAG, "loaded from config: $key=$v"); v }
            else { Log.d(TAG, "invalid/missing $key, using default $default"); default }
        }
        fun scale(key: String, default: Int): Int {
            val v = obj.optIntOrNull(key)
            return if (v != null && v in 1..5) { Log.d(TAG, "loaded from config: $key=$v"); v }
            else { Log.d(TAG, "invalid/missing $key, using default $default"); default }
        }
        fun days(key: String, default: Int): Int {
            val v = obj.optIntOrNull(key)
            return if (v != null && v >= 1) { Log.d(TAG, "loaded from config: $key=$v"); v }
            else { Log.d(TAG, "invalid/missing $key, using default $default"); default }
        }
        return NotificationConfig(
            quietStartHour   = hour("quiet_start_hour", d.quietStartHour),
            quietStartMinute = minute("quiet_start_minute", d.quietStartMinute),
            quietEndHour     = hour("quiet_end_hour", d.quietEndHour),
            quietEndMinute   = minute("quiet_end_minute", d.quietEndMinute),
            stressThresholdScale = scale("stress_threshold_scale", d.stressThresholdScale),
            neglectedAreaDays    = days("neglected_area_days", d.neglectedAreaDays),
            stressRecoveryDays   = days("stress_recovery_days", d.stressRecoveryDays)
        )
    }

    private fun defaults() = AppConfig(
        weights = DefaultWeights.weights,
        elementClassification = ElementClassification(
            negativeKeys = DefaultWeights.negativeKeys,
            positiveKeys = DefaultWeights.weights.keys - DefaultWeights.negativeKeys
        ),
        adaptation = defaultAdaptation(),
        asrs = defaultAsrs(),
        notification = defaultNotification()
    )

    private fun defaultAdaptation() = AdaptationConfig(
        alpha = 0.2, clampMinFactor = 0.5, clampMaxFactor = 2.0,
        correlationThreshold = 0.1, minHistoryDays = 15, minSeriesSize = 5
    )

    private fun defaultAsrs() = AsrsConfig(
        deltaThreshold = 10.0, consecutiveMeasurements = 2, recalibrationAlpha = 0.3
    )

    private fun defaultNotification() = NotificationConfig(
        quietStartHour = 22, quietStartMinute = 0,
        quietEndHour = 8, quietEndMinute = 0,
        stressThresholdScale = 4, neglectedAreaDays = 3, stressRecoveryDays = 3
    )

    private fun JSONObject.optDoubleOrNull(key: String): Double? =
        if (has(key)) runCatching { getDouble(key) }.getOrNull() else null

    private fun JSONObject.optIntOrNull(key: String): Int? =
        if (has(key)) runCatching { getInt(key) }.getOrNull() else null
}
