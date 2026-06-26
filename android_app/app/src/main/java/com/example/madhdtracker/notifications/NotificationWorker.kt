package com.example.madhdtracker.notifications

import android.content.Context
import androidx.room.Room
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import androidx.work.workDataOf
import com.example.madhdtracker.data.AppDatabase
import com.example.madhdtracker.data.TrackerRepository
import com.example.madhdtracker.data.repository.PreferencesRepository
import com.example.madhdtracker.ui.NotificationHelper
import java.time.LocalTime

class NotificationWorker(
    appContext: Context,
    params: WorkerParameters
) : CoroutineWorker(appContext, params) {

    override suspend fun doWork(): Result {
        val prefs = PreferencesRepository(applicationContext)
        if (!prefs.areNotificationsEnabled()) return Result.success()
        if (NotificationRules.isQuietWindow(LocalTime.now())) return Result.success()

        val db = Room.databaseBuilder(applicationContext, AppDatabase::class.java, "adhd_tracker.db")
            .fallbackToDestructiveMigration()
            .build()
        val repository = TrackerRepository(db)
        val decision = repository.evaluateNotification() ?: return Result.success()
        NotificationHelper.send(applicationContext, "mADHD Tracker", decision.message)
        repository.logNotification(decision.type)
        return Result.success(workDataOf("sent" to true))
    }
}
