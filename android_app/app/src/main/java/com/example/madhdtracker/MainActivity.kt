package com.example.madhdtracker

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.room.Room
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import com.example.madhdtracker.data.AppDatabase
import com.example.madhdtracker.data.TrackerRepository
import com.example.madhdtracker.ui.HomeViewModel
import com.example.madhdtracker.ui.HomeViewModelFactory
import com.example.madhdtracker.ui.NotificationHelper
import com.example.madhdtracker.ui.NotificationWorker
import com.example.madhdtracker.ui.TrackerViewModel
import com.example.madhdtracker.ui.TrackerViewModelFactory
import com.example.madhdtracker.ui.TrendViewModel
import com.example.madhdtracker.ui.TrendViewModelFactory
import com.example.madhdtracker.ui.VectorViewModel
import com.example.madhdtracker.ui.VectorViewModelFactory
import com.example.madhdtracker.ui.PermissionHelper
import com.example.madhdtracker.ui.screens.HomeScreen
import com.example.madhdtracker.ui.screens.SettingsScreen
import com.example.madhdtracker.ui.screens.TrackerScreen
import com.example.madhdtracker.ui.screens.TrendScreen
import com.example.madhdtracker.ui.screens.VectorScreen
import com.example.madhdtracker.ui.theme.AppTheme
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.util.concurrent.TimeUnit

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            AppTheme {
                Surface(modifier = Modifier.fillMaxSize()) {
                    AppRoot()
                }
            }
        }
    }
}

enum class Screen {
    HOME, TRACKER, TREND, VECTOR, SETTINGS
}

@Composable
private fun AppRoot() {
    val context = LocalContext.current
    val db = remember {
        Room.databaseBuilder(context, AppDatabase::class.java, "adhd_tracker.db")
            .fallbackToDestructiveMigration()
            .build()
    }
    val repository = remember { TrackerRepository(db) }
    val navController = rememberNavController()
    val trackerViewModel: TrackerViewModel = viewModel(
        factory = TrackerViewModelFactory(repository)
    )
    val homeViewModel: HomeViewModel = viewModel(
        factory = HomeViewModelFactory(repository)
    )
    val trendViewModel: TrendViewModel = viewModel(
        factory = TrendViewModelFactory(repository)
    )
    val vectorViewModel: VectorViewModel = viewModel(
        factory = VectorViewModelFactory(repository)
    )

    PermissionHelper.RequestPostNotificationsPermission()

    LaunchedEffect(Unit) {
        val decision = withContext(Dispatchers.IO) { repository.evaluateNotification() }
        if (decision != null) {
            NotificationHelper.send(context, "mADHD Tracker", decision.message)
            withContext(Dispatchers.IO) { repository.logNotification(decision.type) }
        }

        val work = PeriodicWorkRequestBuilder<NotificationWorker>(24, TimeUnit.HOURS)
            .build()
        WorkManager.getInstance(context).enqueueUniquePeriodicWork(
            "daily_notifications",
            ExistingPeriodicWorkPolicy.UPDATE,
            work
        )
    }

    Column(modifier = Modifier.fillMaxSize()) {
        NavHost(
            navController = navController,
            startDestination = Screen.HOME.name
        ) {
            composable(Screen.HOME.name) {
                HomeScreen(homeViewModel)
            }
            composable(Screen.TRACKER.name) {
                TrackerScreen(trackerViewModel, onSaved = {
                    navController.navigate(Screen.HOME.name) {
                        popUpTo(Screen.HOME.name) { inclusive = false }
                    }
                })
            }
            composable(Screen.TREND.name) { TrendScreen(trendViewModel) }
            composable(Screen.VECTOR.name) { VectorScreen(vectorViewModel) }
            composable(Screen.SETTINGS.name) { SettingsScreen(repository) }
        }

        val navBackStackEntry = navController.currentBackStackEntryAsState()
        val currentRoute = navBackStackEntry.value?.destination?.route

        NavigationBar {
            Screen.values().forEach { screen ->
                NavigationBarItem(
                    selected = currentRoute == screen.name,
                    onClick = { navController.navigate(screen.name) },
                    label = { Text(screen.name.lowercase().replaceFirstChar { it.uppercase() }) },
                    icon = { Text(screen.name.first().toString()) }
                )
            }
        }
    }
}
