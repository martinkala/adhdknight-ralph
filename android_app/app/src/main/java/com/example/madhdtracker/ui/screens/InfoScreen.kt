package com.example.madhdtracker.ui.screens

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.mutableStateMapOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.example.madhdtracker.data.TrackerRepository
import com.example.madhdtracker.domain.model.EntityNode
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

@Composable
fun InfoScreen(repository: TrackerRepository) {
    val entityConfig = repository.elementConfig
    val weights = remember { mutableStateMapOf<String, Double>() }
    val loaded = remember { mutableStateOf(false) }

    LaunchedEffect(Unit) {
        val w = withContext(Dispatchers.IO) { repository.getAllWeights() }
        weights.putAll(w)
        loaded.value = true
    }

    val groupNodes = entityConfig.groupNodes
    val trackableNodes = entityConfig.trackableNodes

    val grouped: Map<String?, List<EntityNode>> = trackableNodes.values
        .filter { it.key != "overall_feeling" }
        .groupBy { it.parent }

    LazyColumn(modifier = Modifier.padding(16.dp)) {
        item {
            Text(text = "Info — entity a váhy", style = MaterialTheme.typography.titleLarge)
            Spacer(modifier = Modifier.height(12.dp))
        }

        val categoryOrder = groupNodes.keys.toList() + listOf(null)
        categoryOrder.forEach { catKey ->
            val catElements = grouped[catKey] ?: return@forEach
            val catLabel = catKey?.let { groupNodes[it]?.label } ?: "Ostatné"

            item {
                Text(
                    text = catLabel,
                    style = MaterialTheme.typography.titleSmall,
                    color = MaterialTheme.colorScheme.primary,
                    modifier = Modifier.padding(top = 12.dp, bottom = 4.dp)
                )
            }

            items(catElements, key = { it.key }) { el ->
                val weight = weights[el.key] ?: el.weight
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(bottom = 6.dp),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
                ) {
                    Column(modifier = Modifier.padding(10.dp)) {
                        Text(text = el.label, style = MaterialTheme.typography.bodyMedium)
                        Text(
                            text = "Váha: ${weight.toInt()} | Dopad: ${if (el.impact == 1) "pozitívny" else "negatívny"}",
                            style = MaterialTheme.typography.labelSmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }
        }
    }
}
