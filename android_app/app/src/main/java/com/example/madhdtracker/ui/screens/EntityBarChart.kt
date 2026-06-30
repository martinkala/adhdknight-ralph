package com.example.madhdtracker.ui.screens

import android.graphics.Paint
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
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
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.drawIntoCanvas
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.madhdtracker.data.EventValueEntity
import com.example.madhdtracker.domain.model.EntityConfig

data class BarEntry(
    val key: String,
    val label: String,
    val value: Double,
    val impact: Int,
    val categoryKey: String?,
    val weight: Double
)

data class BarRow(
    val negEntry: BarEntry?,
    val posEntry: BarEntry?,
    val categoryKey: String?
)

private fun buildBarEntries(
    entities: Map<String, EventValueEntity>,
    elementConfig: EntityConfig
): List<BarEntry> {
    return elementConfig.trackableNodes
        .filter { (key, _) -> key != "overall_feeling" }
        .filter { (key, _) ->
            val entity = entities[key]
            entity != null && (entity.valueBinary == 1 || entity.valueScale != null)
        }
        .map { (key, el) ->
            val entity = entities[key]
            val value = radarValue(entity)
            val parentLabel = el.parent?.let { parentKey ->
                elementConfig.nodes[parentKey]?.label
            }
            val label = if (parentLabel != null) "$parentLabel / ${el.label}" else el.label
            BarEntry(
                key = key,
                label = label,
                value = value,
                impact = el.impact ?: 1,
                categoryKey = el.parent,
                weight = el.weight
            )
        }
}

private fun buildBarRows(negEntries: List<BarEntry>, posEntries: List<BarEntry>): List<BarRow> {
    val rows = mutableListOf<BarRow>()

    val negByCategory = negEntries.groupBy { it.categoryKey }
    val posByCategory = posEntries.groupBy { it.categoryKey }
    val allCategories = (negByCategory.keys + posByCategory.keys)
        .distinct()
        .filter { it != null }

    allCategories.forEach { catKey ->
        val negList = negByCategory[catKey] ?: emptyList()
        val posList = posByCategory[catKey] ?: emptyList()
        val maxLen = maxOf(negList.size, posList.size)
        repeat(maxLen) { i ->
            rows.add(BarRow(negList.getOrNull(i), posList.getOrNull(i), catKey))
        }
    }

    val uncategorizedNeg = negEntries.filter { it.categoryKey == null }
    val uncategorizedPos = posEntries.filter { it.categoryKey == null }
    val maxUncategorized = maxOf(uncategorizedNeg.size, uncategorizedPos.size)
    repeat(maxUncategorized) { i ->
        rows.add(BarRow(uncategorizedNeg.getOrNull(i), uncategorizedPos.getOrNull(i), null))
    }

    return rows
}

@Composable
fun PieChart(
    entities: Map<String, EventValueEntity>,
    elementConfig: EntityConfig,
    modifier: Modifier = Modifier
) {
    val activeEntries = elementConfig.trackableNodes
        .filter { (key, _) -> key != "overall_feeling" }
        .mapNotNull { (key, el) ->
            val entity = entities[key] ?: return@mapNotNull null
            val active = entity.valueBinary == 1 || entity.valueScale != null
            if (!active) return@mapNotNull null
            val value = radarValue(entity).coerceAtLeast(0.01)
            Triple(key, el, value)
        }
        .sortedByDescending { it.third }
        .take(6)

    if (activeEntries.isEmpty()) return

    val total = activeEntries.sumOf { it.third }

    Canvas(modifier = modifier.height(200.dp)) {
        val diameter = minOf(size.width, size.height) * 0.85f
        val left = (size.width - diameter) / 2f
        val top = (size.height - diameter) / 2f
        val arcRect = androidx.compose.ui.geometry.Rect(left, top, left + diameter, top + diameter)

        var startAngle = -90f
        activeEntries.forEach { (_, el, value) ->
            val sweep = (value / total * 360.0).toFloat()
            val color = if (el.impact == 1) Color(0xFF81C784) else Color(0xFFE57373)
            drawArc(
                color = color,
                startAngle = startAngle,
                sweepAngle = sweep,
                useCenter = false,
                topLeft = Offset(arcRect.left, arcRect.top),
                size = Size(arcRect.width, arcRect.height),
                style = androidx.compose.ui.graphics.drawscope.Stroke(width = diameter * 0.22f)
            )
            startAngle += sweep
        }
    }
}

@Composable
fun EntityDoubleBarChart(
    entities: Map<String, EventValueEntity>,
    elementConfig: EntityConfig,
    modifier: Modifier = Modifier
) {
    val allEntries = buildBarEntries(entities, elementConfig)
    val negEntries = allEntries.filter { it.impact == -1 }
    val posEntries = allEntries.filter { it.impact == 1 }

    if (allEntries.isEmpty()) return

    val rows = buildBarRows(negEntries, posEntries)
    val maxVal = (allEntries.maxOfOrNull { it.value } ?: 1.0).coerceAtLeast(0.01)
    val barHeight = 18.dp
    val rowPadding = 3.dp
    val negColor = Color(0xFFE57373)
    val posColor = Color(0xFF81C784)
    val labelSize = 9.sp

    Row(modifier = modifier.height(IntrinsicSize.Min)) {

        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = "Negatívne",
                style = MaterialTheme.typography.labelSmall,
                color = negColor,
                textAlign = TextAlign.Center,
                modifier = Modifier.fillMaxWidth().padding(bottom = 4.dp)
            )
            if (negEntries.isEmpty()) {
                Text(
                    text = "–",
                    style = MaterialTheme.typography.labelSmall,
                    textAlign = TextAlign.Center,
                    modifier = Modifier.fillMaxWidth().padding(vertical = 8.dp)
                )
            }
            rows.forEach { row ->
                val entry = row.negEntry
                if (entry != null) {
                    val fraction = (entry.value / maxVal).toFloat().coerceIn(0.01f, 1f)
                    Column(modifier = Modifier.fillMaxWidth().padding(bottom = rowPadding)) {
                        Canvas(modifier = Modifier.fillMaxWidth().height(barHeight)) {
                            val barW = size.width * fraction
                            drawRect(
                                color = negColor,
                                topLeft = Offset(size.width - barW, 0f),
                                size = Size(barW, size.height)
                            )
                            if (fraction > 0.2f) {
                                drawIntoCanvas { canvas ->
                                    val paint = Paint().apply {
                                        color = android.graphics.Color.WHITE
                                        textSize = size.height * 0.6f
                                        textAlign = Paint.Align.CENTER
                                        isAntiAlias = true
                                    }
                                    val weightText = entry.weight.toInt().toString()
                                    val textX = size.width - barW / 2f
                                    val textY = size.height / 2f - (paint.descent() + paint.ascent()) / 2f
                                    canvas.nativeCanvas.drawText(weightText, textX, textY, paint)
                                }
                            }
                        }
                        Text(
                            text = entry.label,
                            fontSize = labelSize,
                            textAlign = TextAlign.End,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis,
                            style = MaterialTheme.typography.labelSmall,
                            modifier = Modifier.fillMaxWidth()
                        )
                    }
                } else {
                    Spacer(modifier = Modifier.height(barHeight + rowPadding))
                }
            }
        }

        Box(
            modifier = Modifier
                .width(2.dp)
                .fillMaxHeight()
                .background(Color(0xFFBBBBBB))
        )

        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = "Pozitívne",
                style = MaterialTheme.typography.labelSmall,
                color = posColor,
                textAlign = TextAlign.Center,
                modifier = Modifier.fillMaxWidth().padding(bottom = 4.dp)
            )
            if (posEntries.isEmpty()) {
                Text(
                    text = "–",
                    style = MaterialTheme.typography.labelSmall,
                    textAlign = TextAlign.Center,
                    modifier = Modifier.fillMaxWidth().padding(vertical = 8.dp)
                )
            }
            rows.forEach { row ->
                val entry = row.posEntry
                if (entry != null) {
                    val fraction = (entry.value / maxVal).toFloat().coerceIn(0.01f, 1f)
                    Column(modifier = Modifier.fillMaxWidth().padding(bottom = rowPadding)) {
                        Canvas(modifier = Modifier.fillMaxWidth().height(barHeight)) {
                            val barW = size.width * fraction
                            drawRect(
                                color = posColor,
                                topLeft = Offset.Zero,
                                size = Size(barW, size.height)
                            )
                            if (fraction > 0.2f) {
                                drawIntoCanvas { canvas ->
                                    val paint = Paint().apply {
                                        color = android.graphics.Color.WHITE
                                        textSize = size.height * 0.6f
                                        textAlign = Paint.Align.CENTER
                                        isAntiAlias = true
                                    }
                                    val weightText = entry.weight.toInt().toString()
                                    val textX = barW / 2f
                                    val textY = size.height / 2f - (paint.descent() + paint.ascent()) / 2f
                                    canvas.nativeCanvas.drawText(weightText, textX, textY, paint)
                                }
                            }
                        }
                        Text(
                            text = entry.label,
                            fontSize = labelSize,
                            textAlign = TextAlign.Start,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis,
                            style = MaterialTheme.typography.labelSmall,
                            modifier = Modifier.fillMaxWidth()
                        )
                    }
                } else {
                    Spacer(modifier = Modifier.height(barHeight + rowPadding))
                }
            }
        }
    }
}
