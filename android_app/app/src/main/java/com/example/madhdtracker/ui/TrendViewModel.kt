package com.example.madhdtracker.ui

import androidx.compose.runtime.mutableStateOf
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.example.madhdtracker.data.DailyIndexRow
import com.example.madhdtracker.data.DailySubIndexRow
import com.example.madhdtracker.data.TrackerRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class TrendViewModel(
    private val repository: TrackerRepository
) : ViewModel() {
    val series = mutableStateOf<List<DailyIndexRow>>(emptyList())
    val weeklyAverage = mutableStateOf<Double?>(null)
    val dualSeries = mutableStateOf<List<DailySubIndexRow>>(emptyList())

    init {
        refresh()
    }

    fun refresh() {
        viewModelScope.launch(Dispatchers.IO) {
            val data = repository.getLatestDailySeries(7)
            val avg = if (data.isNotEmpty()) data.map { it.indexValue }.average() else null
            val dual = repository.getLatestDualIndexSeries(7)
            withContext(Dispatchers.Main) {
                series.value = data.reversed()
                weeklyAverage.value = avg
                dualSeries.value = dual.reversed()
            }
        }
    }
}

class TrendViewModelFactory(
    private val repository: TrackerRepository
) : ViewModelProvider.Factory {
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(TrendViewModel::class.java)) {
            @Suppress("UNCHECKED_CAST")
            return TrendViewModel(repository) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class")
    }
}
