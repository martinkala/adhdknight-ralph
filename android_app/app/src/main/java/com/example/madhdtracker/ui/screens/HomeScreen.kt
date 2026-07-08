package com.example.madhdtracker.ui.screens

import androidx.compose.foundation.Canvas
import android.util.Log
import androidx.compose.foundation.gestures.detectHorizontalDragGestures
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.IntrinsicSize
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.unit.dp
import java.time.LocalDate
import java.time.format.DateTimeFormatter
import kotlin.math.roundToInt
import com.example.madhdtracker.ui.HomeViewModel

@Composable
private fun PlaceholderBarChart(modifier: Modifier = Modifier) {
    val grayColor = Color(0xFFD0D0D0)
    val negFractions = listOf(0.30f, 0.60f, 0.45f)
    val posFractions = listOf(0.50f, 0.35f, 0.65f)
    val barHeight = 14.dp
    val rowPadding = 4.dp

    Row(modifier = modifier.height(IntrinsicSize.Min)) {
        Column(modifier = Modifier.weight(1f)) {
            negFractions.forEach { fraction ->
                Canvas(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(barHeight)
                        .padding(bottom = rowPadding)
                ) {
                    val barW = size.width * fraction
                    drawRect(grayColor, topLeft = Offset(size.width - barW, 0f), size = Size(barW, size.height))
                }
            }
        }
        Box(modifier = Modifier.width(2.dp).fillMaxHeight())
        Column(modifier = Modifier.weight(1f)) {
            posFractions.forEach { fraction ->
                Canvas(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(barHeight)
                        .padding(bottom = rowPadding)
                ) {
                    val barW = size.width * fraction
                    drawRect(grayColor, topLeft = Offset.Zero, size = Size(barW, size.height))
                }
            }
        }
    }
}

@Composable
private fun AdhdBattery(chargePercent: Int, modifier: Modifier = Modifier) {
    val filled = (chargePercent / 5).coerceIn(0, 20)
    val segmentColor = when {
        chargePercent >= 60 -> Color(0xFF4CAF50)
        chargePercent >= 30 -> Color(0xFFFFC107)
        else -> Color(0xFFF44336)
    }
    val outlineColor = Color(0xFF9E9E9E)

    Column(horizontalAlignment = Alignment.CenterHorizontally, modifier = modifier) {
        Canvas(modifier = Modifier.width(52.dp).height(180.dp)) {
            val stroke = 2.dp.toPx()
            val nubW = size.width * 0.38f
            val nubH = 7.dp.toPx()
            val bodyTop = nubH
            val bodyH = size.height - nubH
            val innerPad = stroke + 2.dp.toPx()
            val innerW = size.width - innerPad * 2
            val innerH = bodyH - innerPad * 2
            val segGap = 1.5.dp.toPx()
            val segH = (innerH - segGap * 19) / 20
            val segLeft = innerPad
            val cornerR = 2.dp.toPx()

            // terminal nub
            drawRoundRect(
                color = outlineColor,
                topLeft = Offset((size.width - nubW) / 2, 0f),
                size = Size(nubW, nubH),
                cornerRadius = CornerRadius(2.dp.toPx())
            )
            // body outline
            drawRoundRect(
                color = outlineColor,
                topLeft = Offset(0f, bodyTop),
                size = Size(size.width, bodyH),
                cornerRadius = CornerRadius(cornerR),
                style = Stroke(width = stroke)
            )
            // segments bottom→top
            for (i in 0 until filled) {
                val top = bodyTop + innerPad + innerH - (i + 1) * segH - i * segGap
                drawRoundRect(
                    color = segmentColor,
                    topLeft = Offset(segLeft, top),
                    size = Size(innerW, segH),
                    cornerRadius = CornerRadius(1.dp.toPx())
                )
            }
        }
        Spacer(modifier = Modifier.height(6.dp))
        Text(
            text = "$chargePercent%",
            style = MaterialTheme.typography.bodyMedium,
            fontWeight = FontWeight.Bold
        )
    }
}

@Composable
fun HomeScreen(viewModel: HomeViewModel, onEditClick: () -> Unit = {}) {
    val formatter = DateTimeFormatter.ofPattern("d. M. yyyy")

    LaunchedEffect(Unit) {
        viewModel.loadForDate()
    }

    val displayedDate = viewModel.displayedDate.value
    val today = LocalDate.now()
    val isToday = displayedDate == today
    val dateFormatted = displayedDate.format(formatter)
    val titleText = if (isToday) "Dnešný prehľad – $dateFormatted" else "Historické dáta – $dateFormatted"

    val indexText = viewModel.indexValue.value?.let { it.roundToInt().toString() } ?: "—"
    val satisfactionText = viewModel.satisfactionValue.value?.toString() ?: "—"
    val completionText = viewModel.completionText.value ?: "—"
    val entities = viewModel.vectorEntities.value
    val hasTodayData = viewModel.hasTodayData.value
    val hasDisplayedData = viewModel.indexValue.value != null
    val positiveText = viewModel.positiveIndex.value?.let { it.roundToInt().toString() } ?: "—"
    val negativeText = viewModel.negativeIndex.value?.let { it.roundToInt().toString() } ?: "—"

    Box(
        modifier = Modifier.pointerInput(Unit) {
            var totalDrag = 0f
            detectHorizontalDragGestures(
                onDragStart = { totalDrag = 0f },
                onDragEnd = {
                    Log.d("HomeSwipe", "onDragEnd totalDrag=$totalDrag")
                    if (totalDrag < -60f) viewModel.loadPreviousDay()
                    else if (totalDrag > 60f) viewModel.loadNextDay()
                    totalDrag = 0f
                },
                onDragCancel = { totalDrag = 0f }
            ) { _, dragAmount ->
                totalDrag += dragAmount
            }
        }
    ) {
    Column(
        modifier = Modifier
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Text(text = titleText, style = MaterialTheme.typography.titleLarge)

        Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)) {
            Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        Column {
                            Text(text = "Pozitívne ↑", style = MaterialTheme.typography.labelSmall, color = Color(0xFF388E3C))
                            Text(text = positiveText, style = MaterialTheme.typography.displaySmall, color = Color(0xFF81C784))
                        }
                        Column {
                            Text(text = "Negatívne ↓", style = MaterialTheme.typography.labelSmall, color = Color(0xFFC62828))
                            Text(text = negativeText, style = MaterialTheme.typography.displaySmall, color = Color(0xFFE57373))
                        }
                    }
                    if (isToday) {
                        Button(onClick = onEditClick) {
                            Text(text = "Upraviť")
                        }
                    }
                }

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceEvenly
                ) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(text = "ADHD index", style = MaterialTheme.typography.labelMedium)
                        Text(text = indexText, style = MaterialTheme.typography.titleMedium)
                    }
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(text = "Spokojnosť", style = MaterialTheme.typography.labelMedium)
                        Text(text = satisfactionText, style = MaterialTheme.typography.titleMedium)
                    }
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(text = "Vyplnené", style = MaterialTheme.typography.labelMedium)
                        Text(text = completionText, style = MaterialTheme.typography.titleMedium)
                    }
                }
            }
        }

        if (isToday && !hasTodayData) {
            Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.secondary.copy(alpha = 0.12f))) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(text = "Zatiaľ bez dát", style = MaterialTheme.typography.titleMedium)
                    Spacer(modifier = Modifier.height(6.dp))
                    Text(text = "Vyplň dnešný tracker a zobrazí sa index.", style = MaterialTheme.typography.bodyMedium)
                }
            }
        }

        Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)) {
            Column(
                modifier = Modifier.padding(12.dp).fillMaxWidth(),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Text(text = "Stav tvojej batérie", style = MaterialTheme.typography.labelMedium)
                Spacer(modifier = Modifier.height(12.dp))
                val chargePercent = viewModel.indexValue.value?.toInt()?.coerceIn(0, 100) ?: 0
                AdhdBattery(chargePercent = chargePercent)
            }
        }

        Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)) {
            Column(modifier = Modifier.padding(12.dp)) {
                Text(text = "Denný prehľad entít", style = MaterialTheme.typography.labelMedium)
                Spacer(modifier = Modifier.height(8.dp))
                if (hasDisplayedData) {
                    EntityDoubleBarChart(
                        entities = entities,
                        elementConfig = viewModel.elementConfig,
                        modifier = Modifier.fillMaxWidth()
                    )
                } else {
                    PlaceholderBarChart(modifier = Modifier.fillMaxWidth())
                }
            }
        }
    }
    }
}
