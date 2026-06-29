package com.example.madhdtracker.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.example.madhdtracker.data.TrackerRepository
import com.example.madhdtracker.data.UserElementEntity
import com.example.madhdtracker.domain.model.ElementConfig
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

class EntityManagementViewModel(
    private val repository: TrackerRepository
) : ViewModel() {

    private val _activeStates = MutableStateFlow<Map<String, Boolean>>(emptyMap())
    val activeStates: StateFlow<Map<String, Boolean>> = _activeStates

    private val _userElements = MutableStateFlow<List<UserElementEntity>>(emptyList())
    val userElements: StateFlow<List<UserElementEntity>> = _userElements

    val elementConfig: ElementConfig get() = repository.elementConfig

    init {
        loadState()
    }

    private fun loadState() {
        viewModelScope.launch(Dispatchers.IO) {
            val activeKeys = repository.getActiveElementKeys()
            val allSystemKeys = repository.elementConfig.elements.keys
            val userElems = repository.getUserElements()
            val allUserKeys = userElems.map { it.key }.toSet()
            val allKeys = allSystemKeys + allUserKeys
            _activeStates.value = allKeys.associateWith { it in activeKeys }
            _userElements.value = userElems
        }
    }

    fun toggleElement(key: String, currentActive: Boolean) {
        viewModelScope.launch(Dispatchers.IO) {
            repository.setElementActive(key, !currentActive)
            _activeStates.value = _activeStates.value.toMutableMap().also { it[key] = !currentActive }
        }
    }

    fun addUserElement(
        key: String,
        weight: Double,
        impact: Int,
        parentCategory: String,
        description: String?,
        scale: List<Int>?
    ) {
        viewModelScope.launch(Dispatchers.IO) {
            val added = repository.addUserElement(key, weight, impact, parentCategory, description, scale)
            if (added) {
                loadState()
            }
        }
    }

    fun removeUserElement(key: String) {
        viewModelScope.launch(Dispatchers.IO) {
            repository.removeUserElement(key)
            loadState()
        }
    }
}

class EntityManagementViewModelFactory(
    private val repository: TrackerRepository
) : ViewModelProvider.Factory {
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(EntityManagementViewModel::class.java)) {
            @Suppress("UNCHECKED_CAST")
            return EntityManagementViewModel(repository) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class")
    }
}
