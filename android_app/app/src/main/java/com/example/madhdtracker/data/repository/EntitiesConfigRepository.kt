package com.example.madhdtracker.data.repository

import android.content.Context
import android.util.Log
import com.example.madhdtracker.data.EntityConfigLoader
import com.example.madhdtracker.data.remote.ApiClient

private const val TAG = "EntitiesConfigRepo"

/**
 * Checks the server for a newer entities.yaml (per APP_ID) and, if found, downloads and
 * persists it as the local override (see EntityConfigLoader.load(context)). The server is
 * the source of truth going forward; the bundled asset only exists so the app is fully
 * functional offline from first launch, before any server has ever been reachable.
 *
 * A downloaded config only takes effect from the next app start — the current session
 * keeps whatever EntityConfig was already loaded when this check runs.
 */
class EntitiesConfigRepository(private val context: Context) {

    private val prefsRepo = PreferencesRepository(context)
    private val apiClient = ApiClient()

    suspend fun checkForUpdate() {
        val url = prefsRepo.getServerUrl()
        if (url.isBlank()) return

        val localVersion = EntityConfigLoader.load(context).version

        val versionResult = apiClient.getEntitiesVersion(url)
        val remoteVersion = versionResult.getOrElse { ex ->
            Log.d(TAG, "version check failed: ${ex.message}")
            return
        }.version

        if (!EntityConfigLoader.isNewerVersion(remoteVersion, localVersion)) {
            Log.d(TAG, "local entities.yaml ($localVersion) is up to date (server: $remoteVersion)")
            return
        }

        val configResult = apiClient.getEntitiesConfig(url)
        val yamlText = configResult.getOrElse { ex ->
            Log.d(TAG, "config download failed: ${ex.message}")
            return
        }

        // Validate before persisting — a malformed/truncated response must never replace a
        // working local config. A successful parse that still contains overall_feeling is
        // treated as valid; EntityConfigLoader.load falls back internally otherwise.
        val parsed = EntityConfigLoader.load(yamlText.byteInputStream())
        if (!parsed.nodes.containsKey("overall_feeling") || parsed.version != remoteVersion) {
            Log.d(TAG, "downloaded config failed validation, discarding")
            return
        }

        EntityConfigLoader.saveOverride(context, yamlText)
        Log.d(TAG, "entities.yaml updated: $localVersion -> $remoteVersion (applies on next app start)")
    }
}
