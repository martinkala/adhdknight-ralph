package com.example.madhdtracker.data

import androidx.room.Database
import androidx.room.RoomDatabase

@Database(
    entities = [
        EventDayEntity::class,
        EventValueEntity::class,
        SatisfactionEntity::class,
        WeightEntity::class,
        IndexDailyEntity::class,
        IndexWeeklyEntity::class,
        NotificationLogEntity::class,
        AsrsCheckinEntity::class
    ],
    version = 1,
    exportSchema = false
)
abstract class AppDatabase : RoomDatabase() {
    abstract fun eventDayDao(): EventDayDao
    abstract fun eventValueDao(): EventValueDao
    abstract fun satisfactionDao(): SatisfactionDao
    abstract fun weightsDao(): WeightsDao
    abstract fun indexDao(): IndexDao
    abstract fun notificationLogDao(): NotificationLogDao
    abstract fun asrsDao(): AsrsDao
}
