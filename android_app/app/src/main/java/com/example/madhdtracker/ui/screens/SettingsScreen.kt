package com.example.madhdtracker.ui.screens

import android.widget.Toast
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.example.madhdtracker.data.TrackerRepository
import com.example.madhdtracker.ui.ExportHelper
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

@Composable
fun SettingsScreen(repository: TrackerRepository) {
    val context = LocalContext.current
    val detailed = remember { mutableStateOf(true) }

    Column(modifier = Modifier.padding(16.dp)) {
        Text(text = "Nastavenia", style = MaterialTheme.typography.titleLarge)
        Spacer(modifier = Modifier.height(12.dp))

        Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)) {
            Column(modifier = Modifier.padding(12.dp)) {
                Text(text = "Detailný režim 1–5", style = MaterialTheme.typography.titleMedium)
                Text(text = "Zapne detailné hodnotenie namiesto 0/1.", style = MaterialTheme.typography.bodyMedium)
                Spacer(modifier = Modifier.height(6.dp))
                Switch(checked = detailed.value, onCheckedChange = { detailed.value = it })
            }
        }

        Spacer(modifier = Modifier.height(16.dp))
        Button(
            onClick = {
                CoroutineScope(Dispatchers.Main).launch {
                    val file = ExportHelper.exportCsv(context, repository)
                    Toast.makeText(context, "Exportované: ${file.name}", Toast.LENGTH_SHORT).show()
                }
            },
            modifier = Modifier.fillMaxWidth()
        ) {
            Text(text = "Export CSV")
        }

        Spacer(modifier = Modifier.height(8.dp))
        Button(
            onClick = {
                CoroutineScope(Dispatchers.Main).launch {
                    val file = ExportHelper.exportJson(context, repository)
                    Toast.makeText(context, "Exportované: ${file.name}", Toast.LENGTH_SHORT).show()
                }
            },
            modifier = Modifier.fillMaxWidth()
        ) {
            Text(text = "Export JSON")
        }
    }
}
