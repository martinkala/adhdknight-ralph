package com.example.madhdtracker.data.db

import androidx.room.Room
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.example.madhdtracker.data.AppDatabase
import com.example.madhdtracker.data.EventDayEntity
import com.example.madhdtracker.data.EventValueEntity
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import java.time.OffsetDateTime

@RunWith(AndroidJUnit4::class)
class DatabaseIntegrationTest {
    private lateinit var db: AppDatabase

    @Before
    fun setup() {
        db = Room.inMemoryDatabaseBuilder(
            ApplicationProvider.getApplicationContext(),
            AppDatabase::class.java
        ).allowMainThreadQueries().build()
    }

    @After
    fun tearDown() {
        db.close()
    }

    @Test
    fun canInsertAndReadDayValues() {
        val now = OffsetDateTime.now().toString()
        val dayId = db.eventDayDao().upsert(EventDayEntity(date = "2026-01-01", createdAt = now, updatedAt = now))
        db.eventValueDao().upsertAll(
            listOf(
                EventValueEntity(eventDayId = dayId, elementKey = "sleep", valueBinary = 1, valueScale = null, valueEffective = 1.0)
            )
        )

        val values = db.eventValueDao().getByDay(dayId)
        assertEquals(1, values.size)
        assertEquals("sleep", values.first().elementKey)
    }
}
