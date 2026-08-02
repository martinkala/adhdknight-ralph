package com.example.madhdtracker.ui.screens

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Divider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.foundation.layout.size
import com.example.madhdtracker.ui.AccountUiState
import com.example.madhdtracker.ui.AccountViewModel
import com.example.madhdtracker.ui.SyncUiState

// Matches the server's RegisterRequest.password_min_length validator (schemas/auth.py)
private const val MIN_PASSWORD_LENGTH = 8

@Composable
fun AccountScreen(viewModel: AccountViewModel) {
    val state by viewModel.uiState.collectAsState()
    val syncState by viewModel.syncState.collectAsState()
    val lastSyncAt by viewModel.lastSyncAt.collectAsState()

    Column(modifier = Modifier.padding(16.dp)) {
        Text("Účet", style = MaterialTheme.typography.titleLarge)
        Spacer(modifier = Modifier.height(16.dp))

        when (state) {
            is AccountUiState.LoggedOut -> LoginForm(
                onLogin = { email, password -> viewModel.login(email, password) },
                onRegister = { email, password -> viewModel.register(email, password) },
                errorMessage = null
            )

            is AccountUiState.Error -> LoginForm(
                onLogin = { email, password -> viewModel.login(email, password) },
                onRegister = { email, password -> viewModel.register(email, password) },
                errorMessage = (state as AccountUiState.Error).message
            )

            AccountUiState.Loading -> {
                Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator()
                }
            }

            is AccountUiState.LoggedIn -> {
                val info = state as AccountUiState.LoggedIn
                UserInfoCard(
                    email = info.email,
                    totalDays = info.totalDays,
                    createdAt = info.createdAt,
                    syncState = syncState,
                    lastSyncAt = lastSyncAt,
                    onSync = { viewModel.sync() },
                    onLogout = { viewModel.logout() }
                )
            }
        }
    }
}

@Composable
private fun LoginForm(
    onLogin: (String, String) -> Unit,
    onRegister: (String, String) -> Unit,
    errorMessage: String?
) {
    val email = remember { mutableStateOf("") }
    val password = remember { mutableStateOf("") }

    Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(
                "Stav: Neprihlásený",
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text("Prihlásenie", style = MaterialTheme.typography.titleMedium)
            Spacer(modifier = Modifier.height(12.dp))

            OutlinedTextField(
                value = email.value,
                onValueChange = { email.value = it },
                label = { Text("E-mail") },
                singleLine = true,
                modifier = Modifier.fillMaxWidth()
            )
            Spacer(modifier = Modifier.height(8.dp))
            OutlinedTextField(
                value = password.value,
                onValueChange = { password.value = it },
                label = { Text("Heslo") },
                singleLine = true,
                visualTransformation = PasswordVisualTransformation(),
                modifier = Modifier.fillMaxWidth()
            )

            if (errorMessage != null) {
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = errorMessage,
                    color = MaterialTheme.colorScheme.error,
                    style = MaterialTheme.typography.bodySmall
                )
            }

            Spacer(modifier = Modifier.height(12.dp))
            Button(
                onClick = { onLogin(email.value, password.value) },
                modifier = Modifier.fillMaxWidth(),
                enabled = email.value.isNotBlank() && password.value.isNotBlank()
            ) {
                Text("Prihlásiť sa")
            }
            Spacer(modifier = Modifier.height(4.dp))
            TextButton(
                onClick = { onRegister(email.value, password.value) },
                modifier = Modifier.fillMaxWidth(),
                enabled = email.value.isNotBlank() && password.value.length >= MIN_PASSWORD_LENGTH
            ) {
                Text("Registrovať sa")
            }
            if (password.value.isNotEmpty() && password.value.length < MIN_PASSWORD_LENGTH) {
                Text(
                    text = "Heslo musí mať aspoň $MIN_PASSWORD_LENGTH znakov",
                    color = MaterialTheme.colorScheme.error,
                    style = MaterialTheme.typography.bodySmall
                )
            }
        }
    }
}

@Composable
private fun UserInfoCard(
    email: String,
    totalDays: Int,
    createdAt: String,
    syncState: SyncUiState,
    lastSyncAt: String?,
    onSync: () -> Unit,
    onLogout: () -> Unit,
) {
    Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text("Prihlásený", style = MaterialTheme.typography.titleMedium)
            Spacer(modifier = Modifier.height(12.dp))
            Divider()
            Spacer(modifier = Modifier.height(8.dp))
            InfoRow("E-mail", email)
            if (totalDays > 0) InfoRow("Sledovaných dní", totalDays.toString())
            if (createdAt.isNotBlank()) InfoRow("Registrovaný", createdAt.take(10))
            InfoRow("Posledná synchronizácia", lastSyncAt?.replace("T", " ")?.take(16) ?: "Zatiaľ nikdy")
            Spacer(modifier = Modifier.height(16.dp))

            Button(
                onClick = onSync,
                modifier = Modifier.fillMaxWidth(),
                enabled = syncState !is SyncUiState.Syncing,
            ) {
                if (syncState is SyncUiState.Syncing) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(16.dp).padding(end = 4.dp),
                        strokeWidth = 2.dp,
                    )
                }
                Text(if (syncState is SyncUiState.Syncing) "Synchronizujem..." else "Synchronizovať dáta")
            }

            when (syncState) {
                is SyncUiState.Done -> {
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        "✓ Synchronizované: ${syncState.accepted} záznamov" +
                            if (syncState.conflicted > 0) " (${syncState.conflicted} konfliktov)" else "",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.primary,
                    )
                }
                is SyncUiState.Error -> {
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        syncState.message,
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.error,
                    )
                }
                else -> {}
            }

            Spacer(modifier = Modifier.height(12.dp))
            OutlinedButton(
                onClick = onLogout,
                modifier = Modifier.fillMaxWidth(),
                colors = ButtonDefaults.outlinedButtonColors(contentColor = MaterialTheme.colorScheme.error)
            ) {
                Text("Odhlásiť sa")
            }
        }
    }
}

@Composable
private fun InfoRow(label: String, value: String) {
    Column(modifier = Modifier.padding(vertical = 4.dp)) {
        Text(label, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        Text(value, style = MaterialTheme.typography.bodyLarge)
    }
    Spacer(modifier = Modifier.height(4.dp))
}
