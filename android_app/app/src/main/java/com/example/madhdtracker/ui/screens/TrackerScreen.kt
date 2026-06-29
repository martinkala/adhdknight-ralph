package com.example.madhdtracker.ui.screens

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.ui.Alignment
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Checkbox
import androidx.compose.material3.DatePicker
import androidx.compose.material3.DatePickerDialog
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
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
import com.example.madhdtracker.ui.ElementValueInput
import com.example.madhdtracker.ui.TrackerViewModel
import java.time.ZoneId
import java.time.format.DateTimeFormatter

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TrackerScreen(
    viewModel: TrackerViewModel,
    onSaved: () -> Unit = {},
    onActivityClick: (String) -> Unit = {}
) {
    val formatter = remember { DateTimeFormatter.ISO_LOCAL_DATE }
    val showDatePicker = remember { mutableStateOf(false) }

    LaunchedEffect(viewModel.selectedDate.value) {
        viewModel.loadForDate(viewModel.selectedDate.value.format(formatter))
    }

    Column(modifier = Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp)) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(text = "Denný tracker", style = MaterialTheme.typography.titleLarge)
            Button(
                onClick = {
                    val date = viewModel.selectedDate.value.format(formatter)
                    val inputs = viewModel.elements.map { element ->
                        val state = viewModel.formStates.getValue(element.key)
                        val scale = if (element.hasScale || state.detailEnabled.value) state.scale.value else null
                        val binary = if (element.hasScale) {
                            if (state.scale.value >= 3) 1 else 0
                        } else {
                            if (state.binary.value) 1 else 0
                        }
                        ElementValueInput(elementKey = element.key, valueBinary = binary, valueScale = scale)
                    }
                    val satisfactionScale = viewModel.formStates.getValue("overall_feeling").scale.value
                    viewModel.saveDay(date, inputs, satisfactionScale)
                    onSaved()
                }
            ) {
                Text(text = "Uložiť deň")
            }
        }
        Spacer(modifier = Modifier.height(12.dp))
        OutlinedTextField(
            value = viewModel.selectedDate.value.format(formatter),
            onValueChange = { },
            readOnly = true,
            label = { Text("Dátum") },
            modifier = Modifier.fillMaxWidth(),
            trailingIcon = {
                TextButton(onClick = { showDatePicker.value = true }) { Text("Zmeniť") }
            }
        )
        Spacer(modifier = Modifier.height(12.dp))

        viewModel.elements.forEach { element ->
            val state = viewModel.formStates.getValue(element.key)

            Card(
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text(
                        text = element.label,
                        style = MaterialTheme.typography.titleMedium,
                        modifier = Modifier.clickable { onActivityClick(element.key) }
                    )

                    if (element.hasScale) {
                        Text(text = "Povinné hodnotenie 1–5", style = MaterialTheme.typography.labelMedium)
                        Slider(
                            value = state.scale.value.toFloat(),
                            onValueChange = { state.scale.value = it.toInt().coerceIn(1, 5) },
                            valueRange = 1f..5f,
                            steps = 3,
                            modifier = Modifier.fillMaxWidth()
                        )
                    } else {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text(text = "Splnené (0/1)", style = MaterialTheme.typography.labelMedium)
                            Switch(
                                checked = state.binary.value,
                                onCheckedChange = { state.binary.value = it }
                            )
                        }
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text(text = "Detail 1–5", style = MaterialTheme.typography.labelMedium)
                            Checkbox(
                                checked = state.detailEnabled.value,
                                onCheckedChange = { state.detailEnabled.value = it }
                            )
                        }
                        if (state.detailEnabled.value) {
                            Slider(
                                value = state.scale.value.toFloat(),
                                onValueChange = { state.scale.value = it.toInt().coerceIn(1, 5) },
                                valueRange = 1f..5f,
                                steps = 3,
                                modifier = Modifier.fillMaxWidth()
                            )
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.height(12.dp))
        }

    }

    if (showDatePicker.value) {
        val pickerState = androidx.compose.material3.rememberDatePickerState()
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
