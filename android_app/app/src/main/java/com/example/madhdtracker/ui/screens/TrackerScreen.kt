package com.example.madhdtracker.ui.screens

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.ui.Alignment
import androidx.compose.ui.graphics.Color
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.DatePicker
import androidx.compose.material3.DatePickerDialog
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.SelectableDates
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Slider
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.example.madhdtracker.ui.TrackerViewModel
import java.time.ZoneId
import java.time.format.DateTimeFormatter

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TrackerScreen(
    viewModel: TrackerViewModel,
    onSaved: () -> Unit = {},
    onActivityClick: (String) -> Unit = {},
    onDayDeleted: () -> Unit = {}
) {
    val formatter = remember { DateTimeFormatter.ISO_LOCAL_DATE }
    val showDatePicker = remember { mutableStateOf(false) }
    val showDeleteDialog = remember { mutableStateOf(false) }
    val date = viewModel.selectedDate.value.format(formatter)

    LaunchedEffect(viewModel.selectedDate.value) {
        viewModel.loadForDate(date)
    }

    Column(modifier = Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp)) {
        Text(text = "Denný tracker", style = MaterialTheme.typography.titleLarge)
        Spacer(modifier = Modifier.height(12.dp))
        OutlinedTextField(
            value = date,
            onValueChange = { },
            readOnly = true,
            label = { Text("Dátum") },
            modifier = Modifier.fillMaxWidth(),
            trailingIcon = {
                TextButton(onClick = { showDatePicker.value = true }) { Text("Zmeniť") }
            }
        )
        viewModel.dateError.value?.let { error ->
            Spacer(modifier = Modifier.height(4.dp))
            Text(text = error, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall)
        }
        Spacer(modifier = Modifier.height(12.dp))

        viewModel.elements.forEach { element ->
            val state = viewModel.formStates.getValue(element.key)

            val isActive = state.binary.value
            val sectionColor = when {
                element.impact == 1 && isActive -> Color(0x334CAF50)
                element.impact == 1 -> Color(0x1A4CAF50)
                isActive -> Color(0x33F44336)
                else -> Color(0x1AF44336)
            }
            Card(
                colors = CardDefaults.cardColors(containerColor = sectionColor),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text(
                        text = element.label,
                        style = MaterialTheme.typography.titleMedium,
                        modifier = Modifier.clickable { onActivityClick(element.key) }
                    )
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(text = "Vykonané", style = MaterialTheme.typography.labelMedium)
                        Switch(
                            checked = state.binary.value,
                            onCheckedChange = {
                                state.binary.value = it
                                viewModel.saveCurrent(date)
                            }
                        )
                    }
                    if (state.binary.value && element.hasScale) {
                        Slider(
                            value = state.scale.value.toFloat(),
                            onValueChange = { state.scale.value = it.toInt().coerceIn(element.scaleMin, element.scaleMax) },
                            onValueChangeFinished = { viewModel.saveCurrent(date) },
                            valueRange = element.scaleMin.toFloat()..element.scaleMax.toFloat(),
                            steps = element.scaleMax - element.scaleMin - 1,
                            modifier = Modifier.fillMaxWidth()
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(12.dp))
        }

        Spacer(modifier = Modifier.height(8.dp))
        OutlinedButton(
            onClick = { showDeleteDialog.value = true },
            modifier = Modifier.fillMaxWidth(),
            colors = androidx.compose.material3.ButtonDefaults.outlinedButtonColors(
                contentColor = MaterialTheme.colorScheme.error
            )
        ) {
            Text("Zmazať deň")
        }
        Spacer(modifier = Modifier.height(8.dp))
    }

    if (showDeleteDialog.value) {
        AlertDialog(
            onDismissRequest = { showDeleteDialog.value = false },
            title = { Text("Zmazať deň?") },
            text = { Text("Všetky záznamy pre $date budú vymazané.") },
            confirmButton = {
                TextButton(onClick = {
                    showDeleteDialog.value = false
                    viewModel.deleteDay(date) { onDayDeleted() }
                }) { Text("Zmazať", color = MaterialTheme.colorScheme.error) }
            },
            dismissButton = {
                TextButton(onClick = { showDeleteDialog.value = false }) { Text("Zrušiť") }
            }
        )
    }

    if (showDatePicker.value) {
        val pickerState = androidx.compose.material3.rememberDatePickerState(
            selectableDates = object : SelectableDates {
                override fun isSelectableDate(utcTimeMillis: Long): Boolean =
                    utcTimeMillis <= System.currentTimeMillis()
            }
        )
        DatePickerDialog(
            onDismissRequest = { showDatePicker.value = false },
            confirmButton = {
                TextButton(
                    onClick = {
                        val millis = pickerState.selectedDateMillis
                        if (millis != null) {
                            val local = java.time.Instant.ofEpochMilli(millis)
                                .atZone(ZoneId.systemDefault())
                                .toLocalDate()
                            viewModel.onDateSelected(local)
                        }
                        showDatePicker.value = false
                    }
                ) { Text("OK") }
            },
            dismissButton = {
                TextButton(onClick = { showDatePicker.value = false }) { Text("Zrušiť") }
            }
        ) {
            DatePicker(state = pickerState)
        }
    }
}
