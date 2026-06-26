package com.example.madhdtracker.ui

import androidx.compose.runtime.mutableStateOf
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.example.madhdtracker.data.EventValueEntity
import com.example.madhdtracker.data.TrackerRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class HomeViewModel(
    private val repository: TrackerRepository
) : ViewModel() {
    val indexValue = mutableStateOf<Double?>(null)
    val satisfactionValue = mutableStateOf<Int?>(null)
    val completionText = mutableStateOf<String?>(null)
    val vectorEntities = mutableStateOf<Map<String, EventValueEntity>>(emptyMap())

    init {
        refresh()
    }

    fun refresh() {
        viewModelScope.launch(Dispatchers.IO) {
            val index = repository.getLatestDailyIndex()
            val satisfaction = repository.getLatestSatisfaction()
            val completion = repository.getLatestCompletionCounts()
            val entities = repository.getLatestVectorEntities()
            withContext(Dispatchers.Main) {
                indexValue.value = index
                satisfactionValue.value = satisfaction
                completionText.value = completion?.let { "${it.first} z ${it.second}" }
                vectorEntities.value = entities
            }
        }
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
