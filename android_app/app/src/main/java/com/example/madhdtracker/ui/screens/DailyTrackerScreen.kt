package com.example.madhdtracker.ui.screens

import androidx.compose.runtime.Composable
import com.example.madhdtracker.ui.TrackerViewModel

@Composable
fun DailyTrackerScreen(
    viewModel: TrackerViewModel,
    onSaved: () -> Unit = {},
    onActivityClick: (String) -> Unit = {}
) {
    TrackerScreen(viewModel, onSaved = onSaved, onActivityClick = onActivityClick)
}
