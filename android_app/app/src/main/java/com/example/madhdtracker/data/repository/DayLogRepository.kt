package com.example.madhdtracker.data.repository

import com.example.madhdtracker.data.AppDatabase
import com.example.madhdtracker.data.EventDayEntity
import com.example.madhdtracker.data.EventValueEntity
import com.example.madhdtracker.data.SatisfactionEntity

class DayLogRepository(
    private val db: AppDatabase
) {
    suspend fun getByDate(date: String): EventDayEntity? {
        return db.eventDayDao().getByDate(date)
    }

    suspend fun saveDay(
        dayId: Long,
        date: String,
        createdAt: String,
        updatedAt: String,
        values: List<EventValueEntity>,
        satisfaction: SatisfactionEntity
    ) {
        db.eventDayDao().upsert(EventDayEntity(id = dayId, date = date, createdAt = createdAt, updatedAt = updatedAt))
        db.eventValueDao().deleteByDay(dayId)
        db.eventValueDao().upsertAll(values)
        db.satisfactionDao().upsert(satisfaction)
    }
}
