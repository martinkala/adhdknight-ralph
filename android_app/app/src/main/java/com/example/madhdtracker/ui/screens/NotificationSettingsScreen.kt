package com.example.madhdtracker.ui.screens

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.example.madhdtracker.data.repository.PreferencesRepository
import com.example.madhdtracker.notifications.NotificationScheduler
import androidx.compose.ui.platform.LocalContext

@Composable
fun NotificationSettingsScreen() {
    val context = LocalContext.current
    val repo = remember { PreferencesRepository(context) }
    val enabled = remember { mutableStateOf(repo.areNotificationsEnabled()) }

    Column(modifier = Modifier.padding(16.dp)) {
        Text(text = "Notifikacie", style = MaterialTheme.typography.titleLarge)
        Spacer(modifier = Modifier.height(12.dp))

        Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)) {
            Column(modifier = Modifier.padding(12.dp)) {
                Text(text = "Povolit notifikacie", style = MaterialTheme.typography.titleMedium)
                Text(
                    text = "Jemne pripomenutia max 1x denne, s tichym oknom 22:00-08:00.",
                    style = MaterialTheme.typography.bodyMedium
                )
                Spacer(modifier = Modifier.height(6.dp))
                Switch(
                    checked = enabled.value,
                    onCheckedChange = {
                        enabled.value = it
                        repo.setNotificationsEnabled(it)
                        if (it) {
                            NotificationScheduler.scheduleDaily(context)
                        } else {
                            NotificationScheduler.cancelDaily(context)
                        }
                    },
                    modifier = Modifier.fillMaxWidth()
                )
            }
        }
    }
}
