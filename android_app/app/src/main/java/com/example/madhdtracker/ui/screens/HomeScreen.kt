package com.example.madhdtracker.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import java.time.LocalDate
import java.time.format.DateTimeFormatter
import kotlin.math.roundToInt
import com.example.madhdtracker.ui.HomeViewModel

@Composable
fun HomeScreen(viewModel: HomeViewModel, onEditClick: () -> Unit = {}) {
    LaunchedEffect(Unit) {
        viewModel.refresh()
    }

    val today = remember { LocalDate.now().format(DateTimeFormatter.ofPattern("d. M. yyyy")) }
    val indexText = viewModel.indexValue.value?.let { it.roundToInt().toString() } ?: "—"
    val satisfactionText = viewModel.satisfactionValue.value?.toString() ?: "—"
    val completionText = viewModel.completionText.value ?: "—"
    val entities = viewModel.vectorEntities.value
    val hasData = viewModel.indexValue.value != null
    val positiveText = viewModel.positiveIndex.value?.let { it.roundToInt().toString() } ?: "—"
    val negativeText = viewModel.negativeIndex.value?.let { it.roundToInt().toString() } ?: "—"

    Column(
        modifier = Modifier
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Text(text = "Dnešný prehľad – $today", style = MaterialTheme.typography.titleLarge)

        Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)) {
            Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                // Positive/Negative section — prominentné (displaySmall) + skratkové tlačidlo
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
                    Button(onClick = onEditClick) {
                        Text(text = "Upraviť")
                    }
                }

                // US5: kompaktné metriky — tri na jednej úrovni
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

        if (!hasData) {
            Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.secondary.copy(alpha = 0.12f))) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(text = "Zatiaľ bez dát", style = MaterialTheme.typography.titleMedium)
                    Spacer(modifier = Modifier.height(6.dp))
                    Text(text = "Vyplň dnešný tracker a zobrazí sa index.", style = MaterialTheme.typography.bodyMedium)
                }
            }
        }

        // US1: EntityDoubleBarChart namiesto RadarChart
        Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)) {
            Column(modifier = Modifier.padding(12.dp)) {
                Text(text = "Denný prehľad entít", style = MaterialTheme.typography.labelMedium)
                Spacer(modifier = Modifier.height(8.dp))
                EntityDoubleBarChart(
                    entities = entities,
                    elementConfig = viewModel.elementConfig,
                    modifier = Modifier.fillMaxWidth()
                )
            }
        }
        // US6: "Tip dňa" karta bola odstránená
    }
}
