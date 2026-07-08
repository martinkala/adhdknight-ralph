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
    val dateError = mutableStateOf<String?>(null)

    val formStates = mutableStateMapOf<String, ElementInputState>().also { map ->
        elements.forEach { el ->
            map[el.key] = ElementInputState(
                binary = mutableStateOf(false),
                detailEnabled = mutableStateOf(el.hasScale),
                scale = mutableStateOf((el.scaleMin + el.scaleMax) / 2)
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
                    val midpoint = (element.scaleMin + element.scaleMax) / 2
                    if (entity != null) {
                        state.binary.value = entity.valueBinary == 1 || entity.valueScale != null
                        state.detailEnabled.value = element.hasScale
                        state.scale.value = entity.valueScale ?: midpoint
                        state.note.value = entity.note ?: ""
                    } else {
                        state.binary.value = false
                        state.detailEnabled.value = element.hasScale
                        state.scale.value = midpoint
                        state.note.value = ""
                        state.showNote.value = false
                    }
                }
            }
        }
    }

    fun onDateSelected(date: LocalDate) {
        if (date.isAfter(LocalDate.now())) {
            dateError.value = "Nemožno zadať budúci dátum"
            return
        }
        dateError.value = null
        selectedDate.value = date
        loadedDate = null
        loadForDate(date.format(DateTimeFormatter.ISO_LOCAL_DATE))
    }

    fun saveNote(date: String, elementKey: String, note: String) {
        viewModelScope.launch(Dispatchers.IO) {
            repository.updateNote(date, elementKey, note.ifBlank { null })
        }
    }

    fun deleteDay(date: String, onDeleted: () -> Unit) {
        viewModelScope.launch(Dispatchers.IO) {
            val day = repository.getDayByDate(date) ?: return@launch
            repository.deleteDay(day.id)
            withContext(Dispatchers.Main) { onDeleted() }
        }
    }

    fun saveCurrent(date: String) {
        val inputs = elements.map { element ->
            val state = formStates[element.key] ?: return@map ElementValueInput(element.key, 0, null, element.scaleMin, element.scaleMax)
            val midpoint = (element.scaleMin + element.scaleMax) / 2
            val (binary, scale) = when {
                !state.binary.value -> Pair(0, null)
                element.hasScale -> Pair(if (state.scale.value >= midpoint) 1 else 0, state.scale.value)
                else -> Pair(1, null)
            }
            ElementValueInput(elementKey = element.key, valueBinary = binary, valueScale = scale, scaleMin = element.scaleMin, scaleMax = element.scaleMax)
        }
        val satisfactionScale = formStates["overall_feeling"]?.scale?.value ?: 3
        saveDay(date, inputs, satisfactionScale)
    }

    fun saveDay(date: String, values: List<ElementValueInput>, satisfactionScale: Int) {
        viewModelScope.launch(Dispatchers.IO) {
            repository.seedDefaultWeightsIfEmpty()
            val day = repository.getOrCreateDay(date)

            val now = OffsetDateTime.now().toString()
            val noteMap = elements.associate { el -> el.key to (formStates[el.key]?.note?.value?.ifBlank { null }) }
            val eventValues = values.map { input ->
                val effective = IndexCalculator.valueEffective(input.valueBinary, input.valueScale, input.scaleMin, input.scaleMax)
                EventValueEntity(
                    eventDayId = day.id,
                    elementKey = input.elementKey,
                    valueBinary = input.valueBinary,
                    valueScale = input.valueScale,
                    valueEffective = effective,
                    note = noteMap[input.elementKey]
                )
            }

            // overall_feeling always uses 1-5 scale (Constitution IV)
            val satisfactionEffective = IndexCalculator.valueEffective(0, satisfactionScale, scaleMin = 1, scaleMax = 5)
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
                    result.add(ElementUiState(el.key, el.label, true, el.impact ?: 1, el.scaleMin, el.scaleMax))
                }
            // Root nodes without scale
            entityConfig.trackableNodes.values
                .filter { it.parent == null && it.scale == null }
                .forEach { el ->
                    result.add(ElementUiState(el.key, el.label, false, el.impact ?: 1, el.scaleMin, el.scaleMax))
                }
            // Group children ordered by group node iteration
            entityConfig.groupNodes.keys.forEach { catKey ->
                entityConfig.trackableNodes.values
                    .filter { it.parent == catKey }
                    .forEach { el ->
                        result.add(ElementUiState(el.key, el.label, el.scale != null, el.impact ?: 1, el.scaleMin, el.scaleMax))
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
    val impact: Int,
    val scaleMin: Int = 1,
    val scaleMax: Int = 5
)

data class ElementInputState(
    val binary: MutableState<Boolean>,
    val detailEnabled: MutableState<Boolean>,
    val scale: MutableState<Int>,
    val note: MutableState<String> = mutableStateOf(""),
    val showNote: MutableState<Boolean> = mutableStateOf(false)
)

data class ElementValueInput(
    val elementKey: String,
    val valueBinary: Int,
    val valueScale: Int?,
    val scaleMin: Int = 1,
    val scaleMax: Int = 5
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
