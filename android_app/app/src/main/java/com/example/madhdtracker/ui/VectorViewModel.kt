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

class VectorViewModel(
    private val repository: TrackerRepository
) : ViewModel() {
    val entities = mutableStateOf<Map<String, EventValueEntity>>(emptyMap())
    val loadedDate = mutableStateOf<String?>(null)

    fun refresh() {
        viewModelScope.launch(Dispatchers.IO) {
            val map = repository.getLatestVectorEntities()
            withContext(Dispatchers.Main) {
                entities.value = map
                loadedDate.value = null
            }
        }
    }

    fun loadForDate(date: String) {
        viewModelScope.launch(Dispatchers.IO) {
            val map = repository.getValuesForDate(date)
            withContext(Dispatchers.Main) {
                entities.value = map
                loadedDate.value = date
            }
        }
    }
}

class VectorViewModelFactory(
    private val repository: TrackerRepository
) : ViewModelProvider.Factory {
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(VectorViewModel::class.java)) {
            @Suppress("UNCHECKED_CAST")
            return VectorViewModel(repository) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class")
    }
}
