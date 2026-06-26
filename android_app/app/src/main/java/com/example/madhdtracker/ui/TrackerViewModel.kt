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
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.time.LocalDate
import java.time.OffsetDateTime
import java.time.format.DateTimeFormatter

class TrackerViewModel(
    private val repository: TrackerRepository
) : ViewModel() {

    val elements = listOf(
        ElementUiState("overall_feeling", "Celkový pocit", true),
        ElementUiState("sleep", "Spánok", false),
        ElementUiState("activity", "Fyzická aktivita", false),
        ElementUiState("stress_work", "Stres v práci", false),
        ElementUiState("stress_personal", "Stres v osobnom živote", false),
        ElementUiState("protein", "Strava proteíny", false),
        ElementUiState("caffeine", "Čaj/káva", false),
        ElementUiState("alcohol", "Alkohol", false),
        ElementUiState("mindfulness", "Mindfulness/relax", false)
    )

    val selectedDate = mutableStateOf(LocalDate.now())

    val formStates = mutableStateMapOf<String, ElementInputState>().also { map ->
        elements.forEach { element ->
            map[element.key] = ElementInputState(
                binary = mutableStateOf(false),
                detailEnabled = mutableStateOf(element.isSatisfaction),
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
                        state.binary.value = entity.valueBinary == 1
                        state.detailEnabled.value = entity.valueScale != null || element.isSatisfaction
                        state.scale.value = entity.valueScale ?: 3
                    } else {
                        state.binary.value = false
                        state.detailEnabled.value = element.isSatisfaction
                        state.scale.value = 3
                    }
                }
            }
        }
    }

    fun onDateSelected(date: LocalDate) {
        selectedDate.value = date
        loadedDate = null  // force reload for new date
        loadForDate(date.format(DateTimeFormatter.ISO_LOCAL_DATE))
    }

    fun saveDay(date: String, values: List<ElementValueInput>, satisfactionScale: Int) {
        viewModelScope.launch(Dispatchers.IO) {
            repository.seedDefaultWeightsIfEmpty()
            val day = repository.getOrCreateDay(date)

            val now = OffsetDateTime.now().toString()
            val eventValues = values.map { input ->
                val effective = input.valueScale?.let { (it - 1) / 4.0 } ?: input.valueBinary.toDouble()
                EventValueEntity(
                    eventDayId = day.id,
                    elementKey = input.elementKey,
                    valueBinary = input.valueBinary,
                    valueScale = input.valueScale,
                    valueEffective = effective
                )
            }

            val satisfactionEffective = (satisfactionScale - 1) / 4.0
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
}

data class ElementUiState(
    val key: String,
    val label: String,
    val isSatisfaction: Boolean
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
    private val repository: TrackerRepository
) : ViewModelProvider.Factory {
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(TrackerViewModel::class.java)) {
            @Suppress("UNCHECKED_CAST")
            return TrackerViewModel(repository) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class")
    }
}
