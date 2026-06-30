package com.example.madhdtracker

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Home
import androidx.compose.material3.Icon
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
import androidx.navigation.compose.rememberNavController
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.room.Room
import com.example.madhdtracker.data.AppDatabase
import com.example.madhdtracker.data.TrackerRepository
import com.example.madhdtracker.data.repository.PreferencesRepository
import com.example.madhdtracker.notifications.NotificationRules
import com.example.madhdtracker.notifications.NotificationScheduler
import com.example.madhdtracker.ui.EntityManagementViewModel
import com.example.madhdtracker.ui.EntityManagementViewModelFactory
import com.example.madhdtracker.ui.HomeViewModel
import com.example.madhdtracker.ui.HomeViewModelFactory
import com.example.madhdtracker.ui.NotificationHelper
import com.example.madhdtracker.ui.TrackerViewModel
import com.example.madhdtracker.ui.TrackerViewModelFactory
import com.example.madhdtracker.ui.TrendViewModel
import com.example.madhdtracker.ui.TrendViewModelFactory
import com.example.madhdtracker.ui.VectorViewModel
import com.example.madhdtracker.ui.VectorViewModelFactory
import com.example.madhdtracker.ui.PermissionHelper
import com.example.madhdtracker.data.AppConfigLoader
import com.example.madhdtracker.data.EntityConfigLoader
import com.example.madhdtracker.ui.navigation.AppNavGraph
import com.example.madhdtracker.ui.navigation.AppRoutes
import com.example.madhdtracker.ui.theme.AppTheme
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.time.LocalTime

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
    HOME, TRACKER, TREND, SETTINGS, INFO
}

@Composable
private fun AppRoot() {
    val context = LocalContext.current
    val db = remember {
        Room.databaseBuilder(context, AppDatabase::class.java, "adhd_tracker.db")
            .build()
    }
    val appConfig = remember { AppConfigLoader.load(context.assets) }
    val elementConfig = remember { EntityConfigLoader.load(context.assets) }
    val repository = remember { TrackerRepository(db, appConfig, elementConfig) }
    val navController = rememberNavController()
    val trackerViewModel: TrackerViewModel = viewModel(
        factory = TrackerViewModelFactory(repository, elementConfig)
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
    val entityManagementViewModel: EntityManagementViewModel = viewModel(
        factory = EntityManagementViewModelFactory(repository)
    )

    PermissionHelper.RequestPostNotificationsPermission()

    LaunchedEffect(Unit) {
        val prefs = PreferencesRepository(context)
        val notifRules = NotificationRules(appConfig.notification, elementConfig.elements.keys)
        if (prefs.areNotificationsEnabled() && !notifRules.isQuietWindow(LocalTime.now())) {
            val decision = withContext(Dispatchers.IO) { repository.evaluateNotification() }
            if (decision != null) {
                NotificationHelper.send(context, "mADHD Tracker", decision.message)
                withContext(Dispatchers.IO) { repository.logNotification(decision.type) }
            }
            NotificationScheduler.scheduleDaily(context)
        } else {
            NotificationScheduler.cancelDaily(context)
        }
    }

    Column(modifier = Modifier.fillMaxSize()) {
        Box(modifier = Modifier.weight(1f)) {
            AppNavGraph(
                navController = navController,
                trackerViewModel = trackerViewModel,
                homeViewModel = homeViewModel,
                trendViewModel = trendViewModel,
                vectorViewModel = vectorViewModel,
                entityManagementViewModel = entityManagementViewModel,
                repository = repository
            )
        }

        val navBackStackEntry = navController.currentBackStackEntryAsState()
        val currentRoute = navBackStackEntry.value?.destination?.route

        NavigationBar {
            Screen.values().forEach { screen ->
                val route = when (screen) {
                    Screen.HOME -> AppRoutes.HOME
                    Screen.TRACKER -> AppRoutes.TRACKER
                    Screen.TREND -> AppRoutes.TREND
                    Screen.SETTINGS -> AppRoutes.SETTINGS
                    Screen.INFO -> AppRoutes.INFO
                }
                val label = when (screen) {
                    Screen.HOME -> "Home"
                    Screen.TRACKER -> "Tracker"
                    Screen.TREND -> "Trend"
                    Screen.SETTINGS -> "Settings"
                    Screen.INFO -> "Info"
                }
                NavigationBarItem(
                    selected = currentRoute == route,
                    onClick = { navController.navigate(route) },
                    label = { Text(label) },
                    icon = {
                        if (screen == Screen.HOME) {
                            Icon(Icons.Filled.Home, contentDescription = "Home")
                        } else {
                            Text(screen.name.first().toString())
                        }
                    }
                )
            }
        }
    }
}
