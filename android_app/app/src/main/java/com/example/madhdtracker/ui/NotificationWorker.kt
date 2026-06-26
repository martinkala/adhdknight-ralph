package com.example.madhdtracker.ui

import android.content.Context
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import androidx.work.workDataOf
import androidx.room.Room
import com.example.madhdtracker.data.AppDatabase
import com.example.madhdtracker.data.TrackerRepository

class NotificationWorker(
    appContext: Context,
    params: WorkerParameters
) : CoroutineWorker(appContext, params) {

    override suspend fun doWork(): Result {
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
