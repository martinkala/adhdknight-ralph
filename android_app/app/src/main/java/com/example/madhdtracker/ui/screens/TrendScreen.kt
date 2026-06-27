package com.example.madhdtracker.ui.screens

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.ui.unit.dp
import kotlin.math.roundToInt
import com.example.madhdtracker.data.DailySubIndexRow
import com.example.madhdtracker.ui.TrendViewModel

@Composable
fun TrendScreen(viewModel: TrendViewModel) {
    LaunchedEffect(Unit) {
        viewModel.refresh()
    }

    val series = viewModel.series.value
    val dualSeries = viewModel.dualSeries.value
    val avgText = viewModel.weeklyAverage.value?.let { it.roundToInt().toString() } ?: "—"

    Column(modifier = Modifier.verticalScroll(rememberScrollState()).padding(16.dp)) {
        Text(text = "Týždenný trend", style = MaterialTheme.typography.titleLarge)
        Text(text = "Priemer: $avgText", style = MaterialTheme.typography.titleMedium)
        Spacer(modifier = Modifier.height(12.dp))

        Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)) {
            Column(modifier = Modifier.padding(12.dp)) {
                DualBarChart(dualSeries)
                Spacer(modifier = Modifier.height(8.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(16.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Box(modifier = Modifier.size(10.dp, 10.dp).padding(0.dp), contentAlignment = Alignment.Center) {
                            Canvas(modifier = Modifier.size(10.dp)) {
                                drawCircle(color = Color(0xFF81C784), radius = size.minDimension / 2)
                            }
                        }
                        Spacer(modifier = Modifier.width(4.dp))
                        Text(text = "Pozitívne", style = MaterialTheme.typography.labelSmall)
                    }
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Box(modifier = Modifier.size(10.dp, 10.dp), contentAlignment = Alignment.Center) {
                            Canvas(modifier = Modifier.size(10.dp)) {
                                drawCircle(color = Color(0xFFE57373), radius = size.minDimension / 2)
                            }
                        }
                        Spacer(modifier = Modifier.width(4.dp))
                        Text(text = "Negatívne", style = MaterialTheme.typography.labelSmall)
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(12.dp))
        series.forEach { row ->
            Text(text = "${row.date}: ${row.indexValue.roundToInt()}", style = MaterialTheme.typography.bodyMedium)
        }
    }
}

@Composable
private fun DualBarChart(items: List<DailySubIndexRow>) {
    val maxTotal = (items.map {
        (it.positiveIndex ?: 0.0) + (it.negativeIndex ?: 0.0)
    }.maxOrNull() ?: 100.0).coerceAtLeast(1.0)

    Canvas(
        modifier = Modifier
            .fillMaxWidth()
            .height(160.dp)
    ) {
        if (items.isEmpty()) return@Canvas
        val colWidth = size.width / items.size
        val barWidth = colWidth * 0.72f
        val barX0 = (colWidth - barWidth) / 2f
        val textPaint = android.graphics.Paint().apply {
            isAntiAlias = true
            textAlign = android.graphics.Paint.Align.CENTER
            textSize = (barWidth * 0.34f).coerceIn(24f, 36f)
            isFakeBoldText = true
        }

        items.forEachIndexed { idx, row ->
            val pos = row.positiveIndex ?: 0.0
            val neg = row.negativeIndex ?: 0.0
            val posH = ((pos / maxTotal) * size.height).toFloat()
            val negH = ((neg / maxTotal) * size.height).toFloat()
            val x = idx * colWidth + barX0
            val barCx = x + barWidth / 2f

            if (row.positiveIndex == null && row.negativeIndex == null) {
                // pre-migration day: draw a subtle placeholder column
                val placeholderH = size.height * 0.06f
                drawRect(Color(0xFFDDDDDD), Offset(x, size.height - placeholderH), Size(barWidth, placeholderH))
            } else {
                if (pos > 0) {
                    val top = size.height - posH - negH
                    drawRect(Color(0xFF81C784), Offset(x, top), Size(barWidth, posH))
                    if (posH > textPaint.textSize * 1.4f) {
                        textPaint.color = android.graphics.Color.parseColor("#1B5E20")
                        drawContext.canvas.nativeCanvas.drawText(
                            pos.toInt().toString(), barCx, top + posH / 2f + textPaint.textSize / 3f, textPaint
                        )
                    }
                }
                if (neg > 0) {
                    val top = size.height - negH
                    drawRect(Color(0xFFE57373), Offset(x, top), Size(barWidth, negH))
                    if (negH > textPaint.textSize * 1.4f) {
                        textPaint.color = android.graphics.Color.parseColor("#B71C1C")
                        drawContext.canvas.nativeCanvas.drawText(
                            neg.toInt().toString(), barCx, top + negH / 2f + textPaint.textSize / 3f, textPaint
                        )
                    }
                }
            }
        }
    }
}
