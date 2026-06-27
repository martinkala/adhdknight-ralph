package com.example.madhdtracker.data

import androidx.room.Room
import androidx.room.testing.MigrationTestHelper
import androidx.sqlite.db.framework.FrameworkSQLiteOpenHelperFactory
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class MigrationTest {

    companion object {
        private const val TEST_DB = "migration-test-db"
    }

    @get:Rule
    val helper = MigrationTestHelper(
        InstrumentationRegistry.getInstrumentation(),
        AppDatabase::class.java
    )

    @Test
    fun migrate1to2_addsPositiveAndNegativeIndexColumns() {
        // Create DB at version 1
        val dbV1 = helper.createDatabase(TEST_DB, 1)

        // Insert a row into index_daily using v1 schema (no positiveIndex/negativeIndex)
        dbV1.execSQL(
            "INSERT INTO event_day (id, date, createdAt, updatedAt) VALUES (1, '2026-01-01', 'now', 'now')"
        )
        dbV1.execSQL(
            "INSERT INTO index_daily (id, eventDayId, indexValue) VALUES (1, 1, 72.5)"
        )
        dbV1.close()

        // Run AutoMigration 1→2
        val dbV2 = helper.runMigrationsAndValidate(TEST_DB, 2, true)

        // Verify new columns exist and are NULL for the historical row
        val cursor = dbV2.query(
            "SELECT positiveIndex, negativeIndex FROM index_daily WHERE id = 1"
        )
        assertNotNull("index_daily row should exist after migration", cursor)
        cursor.moveToFirst()
        val posIdx = cursor.getColumnIndex("positiveIndex")
        val negIdx = cursor.getColumnIndex("negativeIndex")
        assert(posIdx >= 0) { "Column positiveIndex should exist" }
        assert(negIdx >= 0) { "Column negativeIndex should exist" }
        // Historical row → both columns are NULL
        assert(cursor.isNull(posIdx)) { "positiveIndex should be NULL for historical row" }
        assert(cursor.isNull(negIdx)) { "negativeIndex should be NULL for historical row" }
        cursor.close()
        dbV2.close()
    }

    @Test
    fun migrate1to2_newRowsCanStoreSubIndices() {
        // DB v2 built fresh can store positiveIndex and negativeIndex
        val db = Room.inMemoryDatabaseBuilder(
            ApplicationProvider.getApplicationContext(),
            AppDatabase::class.java
        ).allowMainThreadQueries().build()

        val now = "2026-06-27T10:00:00Z"
        val dayId = db.eventDayDao().upsert(EventDayEntity(date = "2026-06-27", createdAt = now, updatedAt = now))
        db.indexDao().insertDaily(
            IndexDailyEntity(
                eventDayId = dayId,
                indexValue = 72.5,
                positiveIndex = 85.0,
                negativeIndex = 30.0
            )
        )

        val result = db.indexDao().getLatestDaily()
        assertNotNull(result)
        assert(result!!.positiveIndex == 85.0) { "positiveIndex should be 85.0" }
        assert(result.negativeIndex == 30.0) { "negativeIndex should be 30.0" }
        db.close()
    }
}
