package com.example.madhdtracker.ui

import androidx.compose.runtime.MutableState
import androidx.compose.runtime.mutableStateMapOf
import androidx.compose.runtime.mutableStateOf
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.example.madhdtracker.data.EventValueEntity
import com.example.madhdtracker.data.SatisfactionEntity
import com.example.madhdtracker.data.TrackerRepository
import com.example.madhdtracker.domain.logic.IndexCalculator
import com.example.madhdtracker.domain.model.ElementConfig
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.time.LocalDate
import java.time.OffsetDateTime
import java.time.format.DateTimeFormatter

class TrackerViewModel(
    private val repository: TrackerRepository,
    private val elementConfig: ElementConfig
) : ViewModel() {

    val elements: List<ElementUiState> = buildElementList(elementConfig)

    val selectedDate = mutableStateOf(LocalDate.now())

    val formStates = mutableStateMapOf<String, ElementInputState>().also { map ->
        elements.forEach { element ->
            map[element.key] = ElementInputState(
                binary = mutableStateOf(false),
                detailEnabled = mutableStateOf(element.key == "overall_feeling"),
                scale = mutableStateOf(3)
            )
        }
    }

    private var loadedDate: String? = null

    fun loadForDate(date: String) {
        if (date == loadedDate) return
        viewModelScope.launch(Dispatchers.IO) {
            val entities = repository.getValuesForDate(date)
            withContext(Dispatchers.Main) {
                loadedDate = date
                elements.forEach { element ->
                    val entity = entities[element.key]
                    val state = formStates[element.key] ?: return@forEach
                    if (entity != null) {
                        state.binary.value = entity.valueBinary == 1 || entity.valueScale != null
                        state.detailEnabled.value = element.key == "overall_feeling"
                        state.scale.value = entity.valueScale ?: 3
                    } else {
                        state.binary.value = false
                        state.detailEnabled.value = element.key == "overall_feeling"
                        state.scale.value = 3
                    }
                }
            }
        }
    }

    fun onDateSelected(date: LocalDate) {
        selectedDate.value = date
        loadedDate = null
        loadForDate(date.format(DateTimeFormatter.ISO_LOCAL_DATE))
    }

    fun saveDay(date: String, values: List<ElementValueInput>, satisfactionScale: Int) {
        viewModelScope.launch(Dispatchers.IO) {
            repository.seedDefaultWeightsIfEmpty()
            val day = repository.getOrCreateDay(date)

            val now = OffsetDateTime.now().toString()
            val eventValues = values.map { input ->
                val effective = IndexCalculator.valueEffective(input.valueBinary, input.valueScale)
                EventValueEntity(
                    eventDayId = day.id,
                    elementKey = input.elementKey,
                    valueBinary = input.valueBinary,
                    valueScale = input.valueScale,
                    valueEffective = effective
                )
            }

            val satisfactionEffective = IndexCalculator.valueEffective(0, satisfactionScale)
            val satisfaction = SatisfactionEntity(
                eventDayId = day.id,
                valueScale = satisfactionScale,
                valueEffective = satisfactionEffective
            )

            repository.saveDay(day.id, date, now, eventValues, satisfaction)
            repository.computeAndSaveDailyIndex(day.id)
            repository.computeAndSaveWeeklyIndex()
        }
    }

    companion object {
        private fun buildElementList(elementConfig: ElementConfig): List<ElementUiState> {
            val result = mutableListOf<ElementUiState>()
            // overall_feeling first (root element)
            elementConfig.elements["overall_feeling"]?.let { el ->
                result.add(ElementUiState(el.key, el.description, el.scale != null, el.impact))
            }
            // Remaining elements ordered by category
            elementConfig.categories.keys.forEach { catKey ->
                elementConfig.elements.values
                    .filter { it.parent == catKey }
                    .forEach { el ->
                        result.add(ElementUiState(el.key, el.description, el.scale != null, el.impact))
                    }
            }
            // Any root elements other than overall_feeling
            elementConfig.elements.values
                .filter { it.parent == null && it.key != "overall_feeling" }
                .forEach { el ->
                    result.add(ElementUiState(el.key, el.description, el.scale != null, el.impact))
                }
            return result.distinctBy { it.key }
        }
    }
}

data class ElementUiState(
    val key: String,
    val label: String,
    val hasScale: Boolean,
    val impact: Int
)

data class ElementInputState(
    val binary: MutableState<Boolean>,
    val detailEnabled: MutableState<Boolean>,
    val scale: MutableState<Int>
)

data class ElementValueInput(
    val elementKey: String,
    val valueBinary: Int,
    val valueScale: Int?
)

class TrackerViewModelFactory(
    private val repository: TrackerRepository,
    private val elementConfig: ElementConfig
) : ViewModelProvider.Factory {
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(TrackerViewModel::class.java)) {
            @Suppress("UNCHECKED_CAST")
            return TrackerViewModel(repository, elementConfig) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class")
    }
}
