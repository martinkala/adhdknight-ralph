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
import com.example.madhdtracker.domain.model.EntityConfig
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.time.LocalDate
import java.time.OffsetDateTime
import java.time.format.DateTimeFormatter

class TrackerViewModel(
    private val repository: TrackerRepository,
    private val elementConfig: EntityConfig
) : ViewModel() {

    private val _elements = mutableListOf<ElementUiState>().also { it.addAll(buildElementList(elementConfig)) }
    val elements: List<ElementUiState> get() = _elements

    val selectedDate = mutableStateOf(LocalDate.now())

    val formStates = mutableStateMapOf<String, ElementInputState>().also { map ->
        elements.forEach { element ->
            map[element.key] = ElementInputState(
                binary = mutableStateOf(false),
                detailEnabled = mutableStateOf(element.hasScale),
                scale = mutableStateOf(3)
            )
        }
    }

    private var loadedDate: String? = null

    init {
        viewModelScope.launch(Dispatchers.IO) {
            val userEls = repository.getUserElements()
            if (userEls.isNotEmpty()) {
                val userStates = userEls.map { ue ->
                    ElementUiState(
                        key = ue.key,
                        label = ue.description ?: ue.key,
                        hasScale = ue.scale != null,
                        impact = ue.impact
                    )
                }
                val newStates = userStates.filter { us -> _elements.none { it.key == us.key } }
                withContext(Dispatchers.Main) {
                    _elements.addAll(newStates)
                    newStates.forEach { us ->
                        formStates[us.key] = ElementInputState(
                            binary = mutableStateOf(false),
                            detailEnabled = mutableStateOf(false),
                            scale = mutableStateOf(3)
                        )
                    }
                }
            }
        }
    }

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
                        state.detailEnabled.value = element.hasScale
                        state.scale.value = entity.valueScale ?: 3
                    } else {
                        state.binary.value = false
                        state.detailEnabled.value = element.hasScale
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

    fun saveCurrent(date: String) {
        val inputs = elements.map { element ->
            val state = formStates[element.key] ?: return@map ElementValueInput(element.key, 0, null)
            val (binary, scale) = when {
                !state.binary.value -> Pair(0, null)
                element.hasScale -> Pair(if (state.scale.value >= 3) 1 else 0, state.scale.value)
                else -> Pair(1, null)
            }
            ElementValueInput(elementKey = element.key, valueBinary = binary, valueScale = scale)
        }
        val satisfactionScale = formStates["overall_feeling"]?.scale?.value ?: 3
        saveDay(date, inputs, satisfactionScale)
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
        private fun buildElementList(entityConfig: EntityConfig): List<ElementUiState> {
            val result = mutableListOf<ElementUiState>()
            // Root nodes with scale first (slider elements; overall_feeling leads by YAML order)
            entityConfig.trackableNodes.values
                .filter { it.parent == null && it.scale != null }
                .forEach { el ->
                    result.add(ElementUiState(el.key, el.label, true, el.impact ?: 1))
                }
            // Root nodes without scale
            entityConfig.trackableNodes.values
                .filter { it.parent == null && it.scale == null }
                .forEach { el ->
                    result.add(ElementUiState(el.key, el.label, false, el.impact ?: 1))
                }
            // Group children ordered by group node iteration
            entityConfig.groupNodes.keys.forEach { catKey ->
                entityConfig.trackableNodes.values
                    .filter { it.parent == catKey }
                    .forEach { el ->
                        result.add(ElementUiState(el.key, el.label, el.scale != null, el.impact ?: 1))
                    }
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
    private val elementConfig: EntityConfig
) : ViewModelProvider.Factory {
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(TrackerViewModel::class.java)) {
            @Suppress("UNCHECKED_CAST")
            return TrackerViewModel(repository, elementConfig) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class")
    }
}
