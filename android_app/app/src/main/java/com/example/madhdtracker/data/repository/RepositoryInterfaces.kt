package com.example.madhdtracker.data.repository

import com.example.madhdtracker.data.EventDayEntity
import com.example.madhdtracker.data.EventValueEntity
import com.example.madhdtracker.data.IndexDailyEntity
import com.example.madhdtracker.data.IndexWeeklyEntity
import com.example.madhdtracker.data.NotificationLogEntity
import com.example.madhdtracker.data.WeightEntity

interface DayRepository {
    suspend fun getByDate(date: String): EventDayEntity?
    suspend fun getLatest(): EventDayEntity?
    suspend fun upsert(day: EventDayEntity): Long
}

interface ValueRepository {
    suspend fun getByDay(dayId: Long): List<EventValueEntity>
    suspend fun upsertAll(values: List<EventValueEntity>)
    suspend fun deleteByDay(dayId: Long)
}

interface WeightRepository {
    suspend fun getAll(): List<WeightEntity>
    suspend fun upsertAll(weights: List<WeightEntity>)
}

interface IndexRepository {
    suspend fun insertDaily(index: IndexDailyEntity)
    suspend fun insertWeekly(index: IndexWeeklyEntity)
}

interface NotificationRepository {
    suspend fun insert(log: NotificationLogEntity)
}
