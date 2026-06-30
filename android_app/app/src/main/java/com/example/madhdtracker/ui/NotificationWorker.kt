package com.example.madhdtracker.ui

import android.content.Context
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import androidx.work.workDataOf
import androidx.room.Room
import com.example.madhdtracker.data.AppConfigLoader
import com.example.madhdtracker.data.AppDatabase
import com.example.madhdtracker.data.EntityConfigLoader
import com.example.madhdtracker.data.TrackerRepository
import com.example.madhdtracker.data.repository.PreferencesRepository
import com.example.madhdtracker.notifications.NotificationRules
import java.time.LocalTime

class NotificationWorker(
    appContext: Context,
    params: WorkerParameters
) : CoroutineWorker(appContext, params) {

    override suspend fun doWork(): Result {
        val prefs = PreferencesRepository(applicationContext)
        if (!prefs.areNotificationsEnabled()) return Result.success()

        val appConfig = AppConfigLoader.load(applicationContext.assets)
        val elementConfig = EntityConfigLoader.load(applicationContext.assets)
        val notifRules = NotificationRules(appConfig.notification, elementConfig.trackableKeys)
        if (notifRules.isQuietWindow(LocalTime.now())) return Result.success()

        val db = Room.databaseBuilder(applicationContext, AppDatabase::class.java, "adhd_tracker.db")
            .fallbackToDestructiveMigration()
            .build()
        val repository = TrackerRepository(db, appConfig, elementConfig)
        val decision = repository.evaluateNotification() ?: return Result.success()
        NotificationHelper.send(applicationContext, "mADHD Tracker", decision.message)
        repository.logNotification(decision.type)
        return Result.success(workDataOf("sent" to true))
    }
}
