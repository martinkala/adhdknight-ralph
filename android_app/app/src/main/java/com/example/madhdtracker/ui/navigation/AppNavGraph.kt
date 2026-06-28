package com.example.madhdtracker.ui.navigation

import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.navArgument
import com.example.madhdtracker.ui.HomeViewModel
import com.example.madhdtracker.ui.TrackerViewModel
import com.example.madhdtracker.ui.TrendViewModel
import com.example.madhdtracker.ui.VectorViewModel
import com.example.madhdtracker.ui.screens.ActivityDetailScreen
import com.example.madhdtracker.ui.screens.HomeScreen
import com.example.madhdtracker.ui.screens.NotificationSettingsScreen
import com.example.madhdtracker.ui.screens.SettingsScreen
import com.example.madhdtracker.ui.screens.TrackerScreen
import com.example.madhdtracker.ui.screens.TrendScreen
import com.example.madhdtracker.ui.screens.VectorScreen
import com.example.madhdtracker.data.TrackerRepository

object AppRoutes {
    const val HOME = "home"
    const val TRACKER = "tracker"
    const val TREND = "trend"
    const val VECTOR = "vector"
    const val VECTOR_DATE = "vector/{date}"
    const val SETTINGS = "settings"
    const val NOTIFICATIONS = "notifications"
    const val ACTIVITY_DETAIL = "activity/{key}"

    fun activityDetail(key: String): String = "activity/$key"
    fun vectorForDate(date: String): String = "vector/$date"
}

@Composable
fun AppNavGraph(
    navController: NavHostController,
    trackerViewModel: TrackerViewModel,
    homeViewModel: HomeViewModel,
    trendViewModel: TrendViewModel,
    vectorViewModel: VectorViewModel,
    repository: TrackerRepository
) {
    val elementLabels = remember(trackerViewModel.elements) {
        trackerViewModel.elements.associate { it.key to it.label }
    }

    NavHost(
        navController = navController,
        startDestination = AppRoutes.HOME
    ) {
        composable(AppRoutes.HOME) {
            HomeScreen(homeViewModel, onEditClick = {
                navController.navigate(AppRoutes.TRACKER)
            })
        }
        composable(AppRoutes.TRACKER) {
            TrackerScreen(trackerViewModel, onSaved = {
                navController.navigate(AppRoutes.HOME) {
                    popUpTo(AppRoutes.HOME) { inclusive = false }
                }
            }, onActivityClick = { key ->
                navController.navigate(AppRoutes.activityDetail(key))
            })
        }
        composable(AppRoutes.TREND) {
            TrendScreen(trendViewModel, onDayClick = { date ->
                navController.navigate(AppRoutes.vectorForDate(date))
            })
        }
        composable(AppRoutes.VECTOR) { VectorScreen(vectorViewModel) }
        composable(
            route = AppRoutes.VECTOR_DATE,
            arguments = listOf(navArgument("date") { defaultValue = "" })
        ) { entry ->
            val date = entry.arguments?.getString("date")?.ifEmpty { null }
            VectorScreen(vectorViewModel, date = date)
        }
        composable(AppRoutes.SETTINGS) {
            SettingsScreen(repository, onOpenNotifications = {
                navController.navigate(AppRoutes.NOTIFICATIONS)
            })
        }
        composable(AppRoutes.NOTIFICATIONS) {
            NotificationSettingsScreen()
        }
        composable(
            route = AppRoutes.ACTIVITY_DETAIL,
            arguments = listOf(navArgument("key") { defaultValue = "" })
        ) { entry ->
            val key = entry.arguments?.getString("key") ?: ""
            val title = elementLabels[key] ?: key
            ActivityDetailScreen(activityKey = key, title = title)
        }
    }
}
