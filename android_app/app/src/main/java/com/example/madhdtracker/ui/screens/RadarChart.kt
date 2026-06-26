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
    val fillColor   = Color(0xFF3A6EA5)
    val gridColor   = Color(0xFFCCCCCC)
    val axisColor   = Color(0xFFAAAAAA)
    val strokeColor = Color(0xFF1A4A80)
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

        val dataPath = Path()
        values.forEachIndexed { i, v ->
            val r = (v.coerceIn(0.0, 1.0) * radius).toFloat()
            val p = pointOnAxis(i, r)
            if (i == 0) dataPath.moveTo(p.x, p.y) else dataPath.lineTo(p.x, p.y)
        }
        dataPath.close()
        drawPath(dataPath, color = fillColor.copy(alpha = 0.35f))
        drawPath(dataPath, color = strokeColor, style = Stroke(width = 3f))

        values.forEachIndexed { i, v ->
            val r = (v.coerceIn(0.0, 1.0) * radius).toFloat()
            val p = pointOnAxis(i, r)
            drawCircle(color = strokeColor, radius = 6f, center = p)
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
