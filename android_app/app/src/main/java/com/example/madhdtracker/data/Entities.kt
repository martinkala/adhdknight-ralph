package com.example.madhdtracker.data

import androidx.room.Entity
import androidx.room.ForeignKey
import androidx.room.Index
import androidx.room.PrimaryKey

@Entity(
    tableName = "event_day",
    indices = [Index(value = ["date"], unique = true)]
)
data class EventDayEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val date: String,
    val createdAt: String,
    val updatedAt: String
)

@Entity(
    tableName = "event_value",
    foreignKeys = [
        ForeignKey(
            entity = EventDayEntity::class,
            parentColumns = ["id"],
            childColumns = ["eventDayId"],
            onDelete = ForeignKey.CASCADE
        )
    ],
    indices = [Index("eventDayId"), Index("elementKey")]
)
data class EventValueEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val eventDayId: Long,
    val elementKey: String,
    val valueBinary: Int,
    val valueScale: Int?,
    val valueEffective: Double
)

@Entity(
    tableName = "satisfaction",
    foreignKeys = [
        ForeignKey(
            entity = EventDayEntity::class,
            parentColumns = ["id"],
            childColumns = ["eventDayId"],
            onDelete = ForeignKey.CASCADE
        )
    ],
    indices = [Index("eventDayId")]
)
data class SatisfactionEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val eventDayId: Long,
    val valueScale: Int,
    val valueEffective: Double
)

@Entity(tableName = "weights")
data class WeightEntity(
    @PrimaryKey val elementKey: String,
    val weightDefault: Double,
    val weightPersonal: Double?,
    val updatedAt: String
)

@Entity(
    tableName = "index_daily",
    foreignKeys = [
        ForeignKey(
            entity = EventDayEntity::class,
            parentColumns = ["id"],
            childColumns = ["eventDayId"],
            onDelete = ForeignKey.CASCADE
        )
    ],
    indices = [Index("eventDayId")]
)
data class IndexDailyEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val eventDayId: Long,
    val indexValue: Double
)

@Entity(tableName = "index_weekly")
data class IndexWeeklyEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val weekStart: String,
    val weekEnd: String,
    val indexValue: Double
)

@Entity(tableName = "notification_log")
data class NotificationLogEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val eventDayId: Long?,
    val type: String,
    val sentAt: String
)

@Entity(tableName = "asrs_checkin")
data class AsrsCheckinEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val date: String,
    val scoreRaw: Int,
    val scoreNormalized: Double
)
