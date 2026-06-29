package com.example.madhdtracker.ui.screens

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.example.madhdtracker.ui.VectorViewModel

@Composable
fun VectorScreen(viewModel: VectorViewModel, date: String? = null) {
    LaunchedEffect(date) {
        if (date != null) viewModel.loadForDate(date) else viewModel.refresh()
    }

    val entities = viewModel.entities.value
    // US7: premenovanie titulku z "Radar" na "Denný detail"
    val title = if (date != null) "Denný detail – $date" else "Denný detail – detail"

    Column(
        modifier = Modifier
            .verticalScroll(rememberScrollState())
            .padding(16.dp)
    ) {
        Text(text = title, style = MaterialTheme.typography.titleLarge)
        Spacer(modifier = Modifier.height(16.dp))

        // US1: EntityDoubleBarChart namiesto RadarChart
        EntityDoubleBarChart(
            entities = entities,
            elementConfig = viewModel.elementConfig,
            modifier = Modifier.fillMaxWidth()
        )

        Spacer(modifier = Modifier.height(16.dp))
        RADAR_AXES.forEach { (key, label) ->
            val entity = entities[key]
            val display = when {
                entity == null -> "—"
                entity.valueScale != null -> "${entity.valueScale}/5"
                entity.valueBinary == 1 -> "✓ (default 3/5)"
                else -> "0"
            }
            Text(
                text = "$label: $display",
                style = MaterialTheme.typography.bodyMedium,
                modifier = Modifier.padding(vertical = 2.dp)
            )
        }
    }
}
