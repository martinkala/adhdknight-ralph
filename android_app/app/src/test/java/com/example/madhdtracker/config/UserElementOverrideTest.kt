package com.example.madhdtracker.config

import com.example.madhdtracker.data.EntityConfigLoader
import com.example.madhdtracker.data.TrackerRepository
import com.example.madhdtracker.data.UserElementOverrideEntity
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class UserElementOverrideTest {

    private val elementConfig = EntityConfigLoader.buildFallback()

    @Test
    fun computeActiveKeys_noOverrides_returnsAllActiveElements() {
        val overrides = emptyList<UserElementOverrideEntity>()
        val activeKeys = TrackerRepository.computeActiveKeys(elementConfig, overrides)

        assertTrue(activeKeys.contains("sleep"))
        assertTrue(activeKeys.contains("caffeine"))
        assertTrue(activeKeys.contains("overall_feeling"))
        assertTrue(activeKeys.contains("mindfulness"))
        // All 9 default elements are active by default
        assertTrue(activeKeys.size == 9)
    }

    @Test
    fun computeActiveKeys_overrideCaffeineInactive_caffeineExcluded() {
        val overrides = listOf(UserElementOverrideEntity(elementKey = "caffeine", isActive = false))
        val activeKeys = TrackerRepository.computeActiveKeys(elementConfig, overrides)

        assertFalse(activeKeys.contains("caffeine"))
        assertTrue(activeKeys.contains("sleep"))
        assertTrue(activeKeys.contains("stress_work"))
    }

    @Test
    fun computeActiveKeys_reactivateCaffeine_caffeineIncluded() {
        // First deactivate, then verify reactivation by having isActive=true override
        val overrides = listOf(UserElementOverrideEntity(elementKey = "caffeine", isActive = true))
        val activeKeys = TrackerRepository.computeActiveKeys(elementConfig, overrides)

        assertTrue(activeKeys.contains("caffeine"))
    }

    @Test
    fun computeActiveKeys_unknownKeyOverride_safelyIgnored() {
        val overrides = listOf(UserElementOverrideEntity(elementKey = "nonexistent_key_xyz", isActive = false))
        val activeKeys = TrackerRepository.computeActiveKeys(elementConfig, overrides)

        // All 9 real elements should remain active
        assertTrue(activeKeys.size == 9)
        assertTrue(activeKeys.contains("sleep"))
    }

    @Test
    fun computeActiveKeys_multipleDeactivations_allExcluded() {
        val overrides = listOf(
            UserElementOverrideEntity(elementKey = "caffeine", isActive = false),
            UserElementOverrideEntity(elementKey = "alcohol", isActive = false),
            UserElementOverrideEntity(elementKey = "stress_personal", isActive = false)
        )
        val activeKeys = TrackerRepository.computeActiveKeys(elementConfig, overrides)

        assertFalse(activeKeys.contains("caffeine"))
        assertFalse(activeKeys.contains("alcohol"))
        assertFalse(activeKeys.contains("stress_personal"))
        assertTrue(activeKeys.contains("sleep"))
        assertTrue(activeKeys.contains("overall_feeling"))
    }
}
