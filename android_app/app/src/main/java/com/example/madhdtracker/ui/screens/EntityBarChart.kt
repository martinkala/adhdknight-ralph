package com.example.madhdtracker.ui.screens

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.IntrinsicSize
import androidx.compose.foundation.layout.Row
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
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.madhdtracker.data.EventValueEntity
import com.example.madhdtracker.domain.model.ElementConfig

data class BarEntry(
    val key: String,
    val label: String,
    val value: Double,
    val impact: Int
)

private fun buildBarEntries(
    entities: Map<String, EventValueEntity>,
    elementConfig: ElementConfig
): List<BarEntry> {
    return elementConfig.elements
        .filter { (key, _) -> key != "overall_feeling" }
        .map { (key, el) ->
            val entity = entities[key]
            val value = radarValue(entity)
            val parentLabel = el.parent?.let { parentKey ->
                elementConfig.categories[parentKey]?.label
            }
            val label = if (parentLabel != null) "$parentLabel / ${el.description}" else el.description
            BarEntry(key = key, label = label, value = value, impact = el.impact)
        }
}

/**
 * Horizontálny bidirectional bar chart:
 * - ľavá strana: záporné entity (červené), pruhy rastú od stredu doľava
 * - pravá strana: pozitívne entity (zelené), pruhy rastú od stredu doprava
 */
@Composable
fun EntityDoubleBarChart(
    entities: Map<String, EventValueEntity>,
    elementConfig: ElementConfig,
    modifier: Modifier = Modifier
) {
    val allEntries = buildBarEntries(entities, elementConfig)
    val negEntries = allEntries.filter { it.impact == -1 }
    val posEntries = allEntries.filter { it.impact == 1 }

    if (allEntries.isEmpty()) return

    val maxVal = (allEntries.maxOfOrNull { it.value } ?: 1.0).coerceAtLeast(0.01)
    val barHeight = 18.dp
    val rowPadding = 3.dp
    val negColor = Color(0xFFE57373)
    val posColor = Color(0xFF81C784)
    val labelSize = 9.sp

    Row(modifier = modifier.height(IntrinsicSize.Min)) {

        // Ľavá strana — záporné entity; pruhy sú ukotvené vpravo (pri stredovej osi) a rastú doľava
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = "Negatívne",
                style = MaterialTheme.typography.labelSmall,
                color = negColor,
                textAlign = TextAlign.Center,
                modifier = Modifier.fillMaxWidth().padding(bottom = 4.dp)
            )
            negEntries.forEach { entry ->
                val fraction = (entry.value / maxVal).toFloat().coerceIn(0.01f, 1f)
                Column(modifier = Modifier.fillMaxWidth().padding(bottom = rowPadding)) {
                    Canvas(modifier = Modifier.fillMaxWidth().height(barHeight)) {
                        val barW = size.width * fraction
                        // Bar ukotvený pri pravom (stredovom) okraji — rastie doľava
                        drawRect(
                            color = negColor,
                            topLeft = Offset(size.width - barW, 0f),
                            size = Size(barW, size.height)
                        )
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
            }
        }

        // Stredová os
        Box(
            modifier = Modifier
                .width(2.dp)
                .fillMaxHeight()
                .background(Color(0xFFBBBBBB))
        )

        // Pravá strana — pozitívne entity; pruhy sú ukotvené vľavo (pri stredovej osi) a rastú doprava
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = "Pozitívne",
                style = MaterialTheme.typography.labelSmall,
                color = posColor,
                textAlign = TextAlign.Center,
                modifier = Modifier.fillMaxWidth().padding(bottom = 4.dp)
            )
            posEntries.forEach { entry ->
                val fraction = (entry.value / maxVal).toFloat().coerceIn(0.01f, 1f)
                Column(modifier = Modifier.fillMaxWidth().padding(bottom = rowPadding)) {
                    Canvas(modifier = Modifier.fillMaxWidth().height(barHeight)) {
                        val barW = size.width * fraction
                        // Bar ukotvený pri ľavom (stredovom) okraji — rastie doprava
                        drawRect(
                            color = posColor,
                            topLeft = Offset.Zero,
                            size = Size(barW, size.height)
                        )
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
            }
        }
    }
}
