package com.example.madhdtracker.data

import androidx.room.AutoMigration
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
        AsrsCheckinEntity::class,
        UserElementOverrideEntity::class,
        UserElementEntity::class
    ],
    version = 5,
    exportSchema = true,
    autoMigrations = [
        AutoMigration(from = 1, to = 2),
        AutoMigration(from = 2, to = 3),
        AutoMigration(from = 3, to = 4),
        AutoMigration(from = 4, to = 5)
    ]
)
abstract class AppDatabase : RoomDatabase() {
    abstract fun eventDayDao(): EventDayDao
    abstract fun eventValueDao(): EventValueDao
    abstract fun satisfactionDao(): SatisfactionDao
    abstract fun weightsDao(): WeightsDao
    abstract fun indexDao(): IndexDao
    abstract fun notificationLogDao(): NotificationLogDao
    abstract fun asrsDao(): AsrsDao
    abstract fun userElementOverrideDao(): UserElementOverrideDao
    abstract fun userElementDao(): UserElementDao
}
