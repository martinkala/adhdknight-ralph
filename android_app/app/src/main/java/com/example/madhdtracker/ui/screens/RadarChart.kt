package com.example.madhdtracker.ui.screens

import androidx.compose.foundation.Canvas
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.ui.graphics.toArgb
import com.example.madhdtracker.data.DefaultWeights
import com.example.madhdtracker.data.EventValueEntity
import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.min
import kotlin.math.sin

val RADAR_AXES = listOf(
    "sleep"             to "Spánok",
    "physical_activity" to "Aktivita",
    "nutrition_protein" to "Proteíny",
    "mindfulness"       to "Mindful.",
    "caffeine"          to "Kofeín",
    "alcohol"           to "Alkohol",
    "stress_personal"   to "Stres os.",
    "stress_work"       to "Stres pr."
)

fun radarValue(entity: EventValueEntity?): Double = when {
    entity == null -> 0.0
    entity.valueScale != null -> entity.valueScale / 5.0
    entity.valueBinary == 1 -> 3.0 / 5.0
    else -> 0.0
}

@Composable
fun RadarChart(
    values: List<Double>,
    labels: List<String>,
    modifier: Modifier = Modifier
) {
    val gridColor   = Color(0xFFCCCCCC)
    val axisColor   = Color(0xFFAAAAAA)
    val labelColor  = Color(0xFF222222)

    Canvas(modifier = modifier) {
        val n = values.size
        if (n < 3) return@Canvas

        val cx = size.width / 2f
        val cy = size.height / 2f
        val radius = min(cx, cy) * 0.62f
        val labelPad = min(cx, cy) * 0.32f

        fun axisAngle(i: Int) = (2 * PI * i / n - PI / 2).toFloat()
        fun pointOnAxis(i: Int, r: Float) = Offset(
            cx + r * cos(axisAngle(i)),
            cy + r * sin(axisAngle(i))
        )

        for (ring in 1..5) {
            val r = radius * ring / 5f
            val gridPath = Path()
            for (i in 0 until n) {
                val p = pointOnAxis(i, r)
                if (i == 0) gridPath.moveTo(p.x, p.y) else gridPath.lineTo(p.x, p.y)
            }
            gridPath.close()
            val strokeW = if (ring == 3) 2.5f else 1.5f
            val color = if (ring == 3) gridColor.copy(alpha = 0.7f) else gridColor
            drawPath(gridPath, color = color, style = Stroke(width = strokeW))
        }

        for (i in 0 until n) {
            drawLine(axisColor, Offset(cx, cy), pointOnAxis(i, radius), strokeWidth = 1.5f)
        }

        val positiveColor = Color(0xFF81C784)
        val positiveStroke = Color(0xFF4CAF50)
        val negativeColor = Color(0xFFE57373)
        val negativeStroke = Color(0xFFF44336)

        val positivePath = Path()
        val negativePath = Path()
        var firstPositive = true
        var firstNegative = true
        values.forEachIndexed { i, v ->
            val key = RADAR_AXES[i].first
            val r = (v.coerceIn(0.0, 1.0) * radius).toFloat()
            val p = pointOnAxis(i, r)
            if (key in DefaultWeights.negativeKeys) {
                if (firstNegative) { negativePath.moveTo(p.x, p.y); firstNegative = false }
                else negativePath.lineTo(p.x, p.y)
            } else {
                if (firstPositive) { positivePath.moveTo(p.x, p.y); firstPositive = false }
                else positivePath.lineTo(p.x, p.y)
            }
        }
        positivePath.close()
        negativePath.close()

        drawPath(positivePath, color = positiveColor.copy(alpha = 0.25f))
        drawPath(negativePath, color = negativeColor.copy(alpha = 0.25f))
        drawPath(positivePath, color = positiveStroke, style = Stroke(width = 2.5f))
        drawPath(negativePath, color = negativeStroke, style = Stroke(width = 2.5f))

        values.forEachIndexed { i, v ->
            val key = RADAR_AXES[i].first
            val dotColor = if (key in DefaultWeights.negativeKeys) negativeStroke else positiveStroke
            val r = (v.coerceIn(0.0, 1.0) * radius).toFloat()
            val p = pointOnAxis(i, r)
            drawCircle(color = dotColor, radius = 6f, center = p)
            drawCircle(color = Color.White, radius = 3f, center = p)
        }

        val paint = android.graphics.Paint().apply {
            color = labelColor.toArgb()
            textSize = 28f
            isAntiAlias = true
            textAlign = android.graphics.Paint.Align.CENTER
        }
        for (i in 0 until n) {
            val p = pointOnAxis(i, radius + labelPad)
            drawContext.canvas.nativeCanvas.drawText(labels[i], p.x, p.y + paint.textSize / 3f, paint)
        }
    }
}
