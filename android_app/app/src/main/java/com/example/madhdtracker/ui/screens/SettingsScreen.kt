package com.example.madhdtracker.ui.screens

import android.content.Intent
import androidx.compose.foundation.layout.Column
import androidx.core.content.FileProvider
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.TextButton
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.example.madhdtracker.data.TrackerRepository
import com.example.madhdtracker.data.repository.PreferencesRepository
import com.example.madhdtracker.data.repository.UserRepository
import com.example.madhdtracker.ui.ExportHelper
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

@Composable
fun SettingsScreen(
    repository: TrackerRepository,
    onOpenNotifications: () -> Unit = {},
    onOpenEntities: () -> Unit = {}
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val syncEnabled = remember { mutableStateOf(false) }
    val prefsRepo = remember { PreferencesRepository(context) }
    val userRepository = remember { UserRepository(context) }
    val serverUrl = remember { mutableStateOf(prefsRepo.getServerUrl()) }
    val urlError = remember { mutableStateOf("") }
    val connectionStatus = remember { mutableStateOf<Boolean?>(null) }
    val checkingConnection = remember { mutableStateOf(false) }

    fun validateUrl(url: String): String {
        if (url.isBlank()) return ""
        return if (!url.startsWith("http://") && !url.startsWith("https://")) {
            "URL musí začínať http:// alebo https://"
        } else ""
    }

    Column(modifier = Modifier.padding(16.dp)) {
        Text(text = "Nastavenia", style = MaterialTheme.typography.titleLarge)
        Spacer(modifier = Modifier.height(12.dp))

        Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)) {
            Column(modifier = Modifier.padding(12.dp)) {
                Text(text = "Server", style = MaterialTheme.typography.titleMedium)
                Text(
                    text = "URL FastAPI servera (napr. http://192.168.1.10:8095)",
                    style = MaterialTheme.typography.bodySmall
                )
                Spacer(modifier = Modifier.height(8.dp))
                OutlinedTextField(
                    value = serverUrl.value,
                    onValueChange = {
                        serverUrl.value = it
                        urlError.value = validateUrl(it)
                        connectionStatus.value = null
                    },
                    label = { Text("URL servera") },
                    placeholder = { Text("http://192.168.1.10:8095") },
                    isError = urlError.value.isNotEmpty(),
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth()
                )
                if (urlError.value.isNotEmpty()) {
                    Text(
                        text = urlError.value,
                        color = MaterialTheme.colorScheme.error,
                        style = MaterialTheme.typography.bodySmall
                    )
                }
                Spacer(modifier = Modifier.height(8.dp))
                Button(
                    onClick = {
                        val err = validateUrl(serverUrl.value)
                        urlError.value = err
                        if (err.isEmpty()) {
                            prefsRepo.setServerUrl(serverUrl.value)
                            connectionStatus.value = null
                        }
                    },
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("Uložiť URL")
                }
                TextButton(
                    onClick = {
                        val err = validateUrl(serverUrl.value)
                        urlError.value = err
                        if (err.isEmpty() && serverUrl.value.isNotBlank()) {
                            prefsRepo.setServerUrl(serverUrl.value)
                            checkingConnection.value = true
                            connectionStatus.value = null
                            scope.launch {
                                connectionStatus.value = userRepository.checkServerReachable()
                                checkingConnection.value = false
                            }
                        }
                    },
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text(if (checkingConnection.value) "Testujem…" else "Test spojenia")
                }
                connectionStatus.value?.let { reachable ->
                    Text(
                        text = if (reachable) "✓ Pripojený" else "✗ Server nedostupný",
                        color = if (reachable) Color(0xFF388E3C) else MaterialTheme.colorScheme.error,
                        style = MaterialTheme.typography.bodySmall
                    )
                }
            }
        }
        Spacer(modifier = Modifier.height(12.dp))

        Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)) {
            Column(modifier = Modifier.padding(12.dp)) {
                Text(text = "Notifikacie", style = MaterialTheme.typography.titleMedium)
                Text(text = "Nastav jemne pripomenutia a tiche okno.", style = MaterialTheme.typography.bodyMedium)
                Spacer(modifier = Modifier.height(6.dp))
                TextButton(onClick = onOpenNotifications) { Text("Otvorit nastavenia") }
            }
        }
        Spacer(modifier = Modifier.height(12.dp))
        Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)) {
            Column(modifier = Modifier.padding(12.dp)) {
                Text(text = "Entity", style = MaterialTheme.typography.titleMedium)
                Text(text = "Spravuj aktívne entity a pridaj vlastné.", style = MaterialTheme.typography.bodyMedium)
                Spacer(modifier = Modifier.height(6.dp))
                TextButton(onClick = onOpenEntities) { Text("Spravovať entity") }
            }
        }

        Spacer(modifier = Modifier.height(16.dp))
        Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)) {
            Column(modifier = Modifier.padding(12.dp)) {
                Text(text = "Sync", style = MaterialTheme.typography.titleMedium)
                Text(text = "Sync je v MVP len stub bez efektu.", style = MaterialTheme.typography.bodyMedium)
                Spacer(modifier = Modifier.height(6.dp))
                Switch(checked = syncEnabled.value, onCheckedChange = { syncEnabled.value = it })
            }
        }

        Spacer(modifier = Modifier.height(16.dp))
        Button(
            onClick = {
                CoroutineScope(Dispatchers.Main).launch {
                    val file = ExportHelper.exportCsv(context, repository)
                    val uri = FileProvider.getUriForFile(context, "${context.packageName}.fileprovider", file)
                    val intent = Intent(Intent.ACTION_SEND).apply {
                        type = "text/csv"
                        putExtra(Intent.EXTRA_STREAM, uri)
                        addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                    }
                    context.startActivity(Intent.createChooser(intent, "Zdieľať CSV"))
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
                    val uri = FileProvider.getUriForFile(context, "${context.packageName}.fileprovider", file)
                    val intent = Intent(Intent.ACTION_SEND).apply {
                        type = "application/json"
                        putExtra(Intent.EXTRA_STREAM, uri)
                        addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                    }
                    context.startActivity(Intent.createChooser(intent, "Zdieľať JSON"))
                }
            },
            modifier = Modifier.fillMaxWidth()
        ) {
            Text(text = "Export JSON")
        }
    }
}
