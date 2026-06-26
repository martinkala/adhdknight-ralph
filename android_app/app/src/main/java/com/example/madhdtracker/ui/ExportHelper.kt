package com.example.madhdtracker.ui

import android.content.Context
import com.example.madhdtracker.data.TrackerRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File

object ExportHelper {
    suspend fun exportCsv(context: Context, repository: TrackerRepository): File = withContext(Dispatchers.IO) {
        val data = repository.exportAll()
        val file = File(context.filesDir, "adhd_export.csv")
        file.writeText(data)
        file
    }

    suspend fun exportJson(context: Context, repository: TrackerRepository): File = withContext(Dispatchers.IO) {
        val data = repository.exportJson()
        val file = File(context.filesDir, "adhd_export.json")
        file.writeText(data)
        file
    }
}
