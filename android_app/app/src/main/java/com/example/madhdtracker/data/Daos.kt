package com.example.madhdtracker.data

import androidx.room.Dao
import androidx.room.Delete
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import com.example.madhdtracker.data.DailySubIndexRow

@Dao
interface EventDayDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(day: EventDayEntity): Long

    @Query("SELECT * FROM event_day WHERE date = :date LIMIT 1")
    suspend fun getByDate(date: String): EventDayEntity?

    @Query("SELECT * FROM event_day ORDER BY date DESC LIMIT 1")
    suspend fun getLatest(): EventDayEntity?

    @Query("SELECT * FROM event_day ORDER BY date DESC LIMIT :limit")
    suspend fun getLatestDays(limit: Int): List<EventDayEntity>

    @Query("SELECT date FROM event_day ORDER BY date DESC")
    suspend fun getAllDates(): List<String>

    @Query("DELETE FROM event_day WHERE id = :dayId")
    suspend fun deleteById(dayId: Long)
}

@Dao
interface EventValueDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertAll(values: List<EventValueEntity>)

    @Query("SELECT * FROM event_value WHERE eventDayId = :dayId")
    suspend fun getByDay(dayId: Long): List<EventValueEntity>

    @Query("DELETE FROM event_value WHERE eventDayId = :dayId")
    suspend fun deleteByDay(dayId: Long)
}

@Dao
interface SatisfactionDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(satisfaction: SatisfactionEntity)

    @Query("SELECT * FROM satisfaction ORDER BY id DESC LIMIT 1")
    suspend fun getLatest(): SatisfactionEntity?

    @Query("SELECT * FROM satisfaction WHERE eventDayId = :dayId LIMIT 1")
    suspend fun getByDay(dayId: Long): SatisfactionEntity?
}

@Dao
interface WeightsDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertAll(weights: List<WeightEntity>)

    @Query("SELECT * FROM weights")
    suspend fun getAll(): List<WeightEntity>
}

@Dao
interface IndexDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertDaily(index: IndexDailyEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertWeekly(index: IndexWeeklyEntity)

    @Query("SELECT * FROM index_daily ORDER BY id DESC LIMIT 1")
    suspend fun getLatestDaily(): IndexDailyEntity?

    @Query("SELECT * FROM index_daily WHERE eventDayId = :dayId LIMIT 1")
    suspend fun getByDayId(dayId: Long): IndexDailyEntity?

    @Query("DELETE FROM index_daily WHERE eventDayId = :dayId")
    suspend fun deleteByDayId(dayId: Long)

    @Query(
        """
        SELECT event_day.date as date, index_daily.indexValue as indexValue
        FROM index_daily
        INNER JOIN event_day ON index_daily.eventDayId = event_day.id
        ORDER BY event_day.date DESC
        LIMIT :limit
        """
    )
    suspend fun getLatestDailyWithDate(limit: Int): List<DailyIndexRow>

    @Query(
        """
        SELECT event_day.date as date, index_daily.positiveIndex as positiveIndex, index_daily.negativeIndex as negativeIndex
        FROM index_daily
        INNER JOIN event_day ON index_daily.eventDayId = event_day.id
        ORDER BY event_day.date DESC
        LIMIT :limit
        """
    )
    suspend fun getLatestDualWithDate(limit: Int): List<DailySubIndexRow>
}

@Dao
interface NotificationLogDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(log: NotificationLogEntity)

    @Query("SELECT * FROM notification_log ORDER BY sentAt DESC LIMIT 1")
    suspend fun getLatest(): NotificationLogEntity?
}

@Dao
interface AsrsDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(checkin: AsrsCheckinEntity)

    @Query("SELECT * FROM asrs_checkin ORDER BY date DESC LIMIT :limit")
    suspend fun getRecent(limit: Int): List<AsrsCheckinEntity>
}

@Dao
interface UserElementOverrideDao {
    @Query("SELECT * FROM user_element_override")
    suspend fun getAll(): List<UserElementOverrideEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(override: UserElementOverrideEntity)

    @Query("DELETE FROM user_element_override WHERE elementKey = :key")
    suspend fun delete(key: String)
}

@Dao
interface UserElementDao {
    @Query("SELECT * FROM user_element")
    suspend fun getAll(): List<UserElementEntity>

    @Insert
    suspend fun insert(element: UserElementEntity): Long

    @Delete
    suspend fun delete(element: UserElementEntity)
}
