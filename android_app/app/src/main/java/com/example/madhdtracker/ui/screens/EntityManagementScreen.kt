package com.example.madhdtracker.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExposedDropdownMenuBox
import androidx.compose.material3.ExposedDropdownMenuDefaults
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import com.example.madhdtracker.ui.EntityManagementViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun EntityManagementScreen(viewModel: EntityManagementViewModel) {
    val activeStates by viewModel.activeStates.collectAsState()
    val userElements by viewModel.userElements.collectAsState()
    val elementConfig = viewModel.elementConfig

    var showAddDialog by remember { mutableStateOf(false) }
    var addError by remember { mutableStateOf<String?>(null) }

    Scaffold(
        floatingActionButton = {
            FloatingActionButton(onClick = { showAddDialog = true }) {
                Text("+")
            }
        }
    ) { padding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(horizontal = 16.dp)
        ) {
            // System elements grouped by category
            elementConfig.categories.entries.forEach { (catKey, category) ->
                val categoryElements = elementConfig.elements.values.filter { it.parent == catKey }
                if (categoryElements.isEmpty()) return@forEach

                item {
                    Text(
                        text = category.label,
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.padding(top = 16.dp, bottom = 4.dp)
                    )
                    HorizontalDivider()
                }

                items(categoryElements, key = { it.key }) { element ->
                    val isActive = activeStates[element.key] ?: element.active
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 8.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column(modifier = Modifier.weight(1f)) {
                            Text(element.description, style = MaterialTheme.typography.bodyLarge)
                            Text(
                                "w=${element.weight} impact=${if (element.impact > 0) "+" else ""}${element.impact}",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                        Switch(
                            checked = isActive,
                            onCheckedChange = { viewModel.toggleElement(element.key, isActive) }
                        )
                    }
                }
            }

            // Root elements (parent == null)
            val rootElements = elementConfig.elements.values.filter { it.parent == null }
            if (rootElements.isNotEmpty()) {
                item {
                    Text(
                        text = "Ostatné",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.padding(top = 16.dp, bottom = 4.dp)
                    )
                    HorizontalDivider()
                }
                items(rootElements, key = { it.key }) { element ->
                    val isActive = activeStates[element.key] ?: element.active
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 8.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column(modifier = Modifier.weight(1f)) {
                            Text(element.description, style = MaterialTheme.typography.bodyLarge)
                        }
                        Switch(
                            checked = isActive,
                            onCheckedChange = { viewModel.toggleElement(element.key, isActive) }
                        )
                    }
                }
            }

            // User-defined elements
            if (userElements.isNotEmpty()) {
                item {
                    Text(
                        text = "Vlastné entity",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.padding(top = 16.dp, bottom = 4.dp)
                    )
                    HorizontalDivider()
                }
                items(userElements, key = { it.id }) { entity ->
                    val isActive = activeStates[entity.key] ?: entity.isActive
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 8.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column(modifier = Modifier.weight(1f)) {
                            Text(entity.description ?: entity.key, style = MaterialTheme.typography.bodyLarge)
                            Text(
                                "${entity.key} • ${entity.parentCategory}",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Switch(
                                checked = isActive,
                                onCheckedChange = { viewModel.toggleElement(entity.key, isActive) }
                            )
                            TextButton(onClick = { viewModel.removeUserElement(entity.key) }) {
                                Text("X", color = MaterialTheme.colorScheme.error)
                            }
                        }
                    }
                }
            }
        }
    }

    if (showAddDialog) {
        AddEntityDialog(
            categories = elementConfig.categories.keys.toList(),
            error = addError,
            onDismiss = { showAddDialog = false; addError = null },
            onConfirm = { key, weight, impact, category, description ->
                if (key.isBlank()) { addError = "Kľúč nesmie byť prázdny"; return@AddEntityDialog }
                if (weight <= 0.0) { addError = "Váha musí byť > 0"; return@AddEntityDialog }
                viewModel.addUserElement(key.trim(), weight, impact, category, description.ifBlank { null }, null)
                showAddDialog = false
                addError = null
            }
        )
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun AddEntityDialog(
    categories: List<String>,
    error: String?,
    onDismiss: () -> Unit,
    onConfirm: (key: String, weight: Double, impact: Int, category: String, description: String) -> Unit
) {
    var key by remember { mutableStateOf("") }
    var weightStr by remember { mutableStateOf("") }
    var impact by remember { mutableStateOf(1) }
    var selectedCategory by remember { mutableStateOf(categories.firstOrNull() ?: "") }
    var description by remember { mutableStateOf("") }
    var categoryExpanded by remember { mutableStateOf(false) }
    var impactExpanded by remember { mutableStateOf(false) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Pridať entitu") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(
                    value = key,
                    onValueChange = { key = it },
                    label = { Text("Kľúč (unikátny)") },
                    singleLine = true
                )
                OutlinedTextField(
                    value = weightStr,
                    onValueChange = { weightStr = it },
                    label = { Text("Váha") },
                    singleLine = true,
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal)
                )
                ExposedDropdownMenuBox(
                    expanded = impactExpanded,
                    onExpandedChange = { impactExpanded = it }
                ) {
                    OutlinedTextField(
                        value = if (impact == 1) "+1 (pozitívny)" else "-1 (negatívny)",
                        onValueChange = {},
                        readOnly = true,
                        label = { Text("Vplyv") },
                        trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(impactExpanded) },
                        modifier = Modifier.menuAnchor()
                    )
                    ExposedDropdownMenu(expanded = impactExpanded, onDismissRequest = { impactExpanded = false }) {
                        DropdownMenuItem(text = { Text("+1 (pozitívny)") }, onClick = { impact = 1; impactExpanded = false })
                        DropdownMenuItem(text = { Text("-1 (negatívny)") }, onClick = { impact = -1; impactExpanded = false })
                    }
                }
                ExposedDropdownMenuBox(
                    expanded = categoryExpanded,
                    onExpandedChange = { categoryExpanded = it }
                ) {
                    OutlinedTextField(
                        value = selectedCategory,
                        onValueChange = {},
                        readOnly = true,
                        label = { Text("Kategória") },
                        trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(categoryExpanded) },
                        modifier = Modifier.menuAnchor()
                    )
                    ExposedDropdownMenu(expanded = categoryExpanded, onDismissRequest = { categoryExpanded = false }) {
                        categories.forEach { cat ->
                            DropdownMenuItem(text = { Text(cat) }, onClick = { selectedCategory = cat; categoryExpanded = false })
                        }
                    }
                }
                OutlinedTextField(
                    value = description,
                    onValueChange = { description = it },
                    label = { Text("Popis (voliteľný)") },
                    singleLine = true
                )
                if (error != null) {
                    Text(error, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall)
                }
            }
        },
        confirmButton = {
            Button(onClick = {
                val weight = weightStr.replace(",", ".").toDoubleOrNull() ?: 0.0
                onConfirm(key, weight, impact, selectedCategory, description)
            }) { Text("Pridať") }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) { Text("Zrušiť") }
        }
    )
}
