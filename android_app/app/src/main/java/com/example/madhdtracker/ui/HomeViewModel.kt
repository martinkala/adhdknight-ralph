package com.example.madhdtracker.ui

import androidx.compose.runtime.mutableStateOf
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.example.madhdtracker.data.EventValueEntity
import com.example.madhdtracker.data.TrackerRepository
import com.example.madhdtracker.domain.model.ElementConfig
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.time.LocalDate

class HomeViewModel(
    private val repository: TrackerRepository
) : ViewModel() {
    val elementConfig: ElementConfig get() = repository.elementConfig

    val indexValue = mutableStateOf<Double?>(null)
    val satisfactionValue = mutableStateOf<Int?>(null)
    val completionText = mutableStateOf<String?>(null)
    val vectorEntities = mutableStateOf<Map<String, EventValueEntity>>(emptyMap())
    val positiveIndex = mutableStateOf<Double?>(null)
    val negativeIndex = mutableStateOf<Double?>(null)
    val hasTodayData = mutableStateOf(false)
    val displayedDate = mutableStateOf(LocalDate.now())
    val availableDates = mutableStateOf<List<LocalDate>>(emptyList())

    init {
        viewModelScope.launch(Dispatchers.IO) {
            loadAvailableDates()
            loadForDate(LocalDate.now())
        }
    }

    private suspend fun loadAvailableDates() {
        val dates = repository.getAllEventDates()
            .mapNotNull { runCatching { LocalDate.parse(it) }.getOrNull() }
        val today = LocalDate.now()
        val withToday = if (today !in dates) dates + today else dates
        withContext(Dispatchers.Main) {
            availableDates.value = withToday.sortedDescending()
        }
    }

    fun loadForDate(date: LocalDate = LocalDate.now()) {
        viewModelScope.launch(Dispatchers.IO) {
            val dateStr = date.toString()
            val index = repository.getIndexForDate(dateStr)
            val satisfaction = repository.getSatisfactionForDate(dateStr)
            val completion = repository.getCompletionCountsForDate(dateStr)
            val entities = repository.getValuesForDate(dateStr)
            val subIndices = repository.getSubIndicesForDate(dateStr)
            val today = LocalDate.now()
            withContext(Dispatchers.Main) {
                displayedDate.value = date
                indexValue.value = index
                satisfactionValue.value = satisfaction
                completionText.value = completion?.let { "${it.first} z ${it.second}" }
                vectorEntities.value = entities
                positiveIndex.value = subIndices.first
                negativeIndex.value = subIndices.second
                hasTodayData.value = date == today && index != null
            }
        }
    }

    fun loadPreviousDay() {
        val dates = availableDates.value
        val current = displayedDate.value
        val idx = dates.indexOf(current)
        val prev = if (idx >= 0 && idx < dates.size - 1) dates[idx + 1] else null
        if (prev != null) loadForDate(prev)
    }

    fun loadNextDay() {
        val dates = availableDates.value
        val current = displayedDate.value
        val idx = dates.indexOf(current)
        val next = if (idx > 0) dates[idx - 1] else null
        if (next != null) loadForDate(next)
    }

    fun refresh() {
        loadForDate(displayedDate.value)
    }
}

class HomeViewModelFactory(
    private val repository: TrackerRepository
) : ViewModelProvider.Factory {
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(HomeViewModel::class.java)) {
            @Suppress("UNCHECKED_CAST")
            return HomeViewModel(repository) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class")
    }
}
