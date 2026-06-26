package com.example.madhdtracker.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.example.madhdtracker.data.repository.ActivityDescriptionRepository
import com.example.madhdtracker.ui.MarkdownRenderer

@Composable
fun ActivityDetailScreen(
    activityKey: String,
    title: String
) {
    val context = LocalContext.current
    val repository = remember { ActivityDescriptionRepository(context) }
    val description = repository.getDescription(activityKey)
        ?: "Popis pre tuto aktivitu zatial nie je dostupny."

    Column(
        modifier = Modifier
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Text(text = title, style = MaterialTheme.typography.titleLarge)

        Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text(
                    text = MarkdownRenderer.toAnnotated(description),
                    style = MaterialTheme.typography.bodyMedium,
                    modifier = Modifier.fillMaxWidth()
                )
            }
        }

        Spacer(modifier = Modifier.height(8.dp))
        Text(
            text = "Informacie su read-only a sluzia len ako pomocne vysvetlenie.",
            style = MaterialTheme.typography.labelMedium
        )
    }
}
