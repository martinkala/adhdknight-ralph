package com.example.madhdtracker.ui.screens

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import kotlin.math.roundToInt
import com.example.madhdtracker.ui.TrendViewModel

@Composable
fun TrendScreen(viewModel: TrendViewModel) {
    LaunchedEffect(Unit) {
        viewModel.refresh()
    }

    val series = viewModel.series.value
    val avgText = viewModel.weeklyAverage.value?.let { it.roundToInt().toString() } ?: "—"

    Column(modifier = Modifier.verticalScroll(rememberScrollState()).padding(16.dp)) {
        Text(text = "Týždenný trend", style = MaterialTheme.typography.titleLarge)
        Text(text = "Priemer: $avgText", style = MaterialTheme.typography.titleMedium)
        Spacer(modifier = Modifier.height(12.dp))

        Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)) {
            Column(modifier = Modifier.padding(12.dp)) {
                SimpleBarChart(series.map { it.indexValue })
            }
        }

        Spacer(modifier = Modifier.height(12.dp))
        series.forEach { row ->
            Text(text = "${row.date}: ${row.indexValue.roundToInt()}", style = MaterialTheme.typography.bodyMedium)
        }
    }
}

@Composable
private fun SimpleBarChart(values: List<Double>) {
    val maxValue = (values.maxOrNull() ?: 100.0).coerceAtLeast(1.0)
    Canvas(
        modifier = Modifier
            .fillMaxWidth()
            .height(120.dp)
    ) {
        if (values.isEmpty()) return@Canvas
        val barWidth = size.width / values.size
        values.forEachIndexed { index, v ->
            val barHeight = ((v / maxValue) * size.height).toFloat()
            drawRect(
                color = Color(0xFF3A6EA5),
                topLeft = androidx.compose.ui.geometry.Offset(
                    x = index * barWidth,
                    y = size.height - barHeight
                ),
                size = androidx.compose.ui.geometry.Size(
                    width = barWidth * 0.8f,
                    height = barHeight
                )
            )
        }
    }
}
