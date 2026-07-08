package com.example.madhdtracker.ui

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.example.madhdtracker.data.repository.LoginResult
import com.example.madhdtracker.data.repository.SyncAllResult
import com.example.madhdtracker.data.repository.UserRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

sealed class AccountUiState {
    object LoggedOut : AccountUiState()
    object Loading : AccountUiState()
    data class LoggedIn(val email: String, val totalDays: Int, val createdAt: String) : AccountUiState()
    data class Error(val message: String) : AccountUiState()
}

sealed class SyncUiState {
    object Idle : SyncUiState()
    object Syncing : SyncUiState()
    data class Done(val accepted: Int, val conflicted: Int) : SyncUiState()
    data class Error(val message: String) : SyncUiState()
}

class AccountViewModel(application: Application) : AndroidViewModel(application) {

    private val userRepository = UserRepository(application)

    private val _uiState = MutableStateFlow<AccountUiState>(AccountUiState.LoggedOut)
    val uiState: StateFlow<AccountUiState> = _uiState

    private val _syncState = MutableStateFlow<SyncUiState>(SyncUiState.Idle)
    val syncState: StateFlow<SyncUiState> = _syncState

    init {
        val user = userRepository.getCurrentUser()
        if (user != null) {
            _uiState.value = AccountUiState.LoggedIn(user.email, user.totalDays, user.createdAt)
            viewModelScope.launch { sync() }
        }
    }

    fun login(email: String, password: String) {
        viewModelScope.launch {
            _uiState.value = AccountUiState.Loading
            when (val result = userRepository.login(email, password)) {
                is LoginResult.Success -> {
                    _uiState.value = AccountUiState.LoggedIn(result.email, result.totalDays, result.createdAt)
                    sync()
                }
                is LoginResult.Error -> _uiState.value = AccountUiState.Error(result.message)
                LoginResult.NoServer -> _uiState.value = AccountUiState.Error("Zadajte URL servera v nastaveniach")
            }
        }
    }

    fun register(email: String, password: String) {
        viewModelScope.launch {
            _uiState.value = AccountUiState.Loading
            _uiState.value = when (val result = userRepository.register(email, password)) {
                is LoginResult.Success -> AccountUiState.LoggedIn(result.email, result.totalDays, result.createdAt)
                is LoginResult.Error -> AccountUiState.Error(result.message)
                LoginResult.NoServer -> AccountUiState.Error("Zadajte URL servera v nastaveniach")
            }
        }
    }

    fun logout() {
        userRepository.logout()
        _uiState.value = AccountUiState.LoggedOut
        _syncState.value = SyncUiState.Idle
    }

    fun sync() {
        viewModelScope.launch {
            _syncState.value = SyncUiState.Syncing
            _syncState.value = when (val result = userRepository.syncAll()) {
                is SyncAllResult.Success -> SyncUiState.Done(result.accepted, result.conflicted)
                is SyncAllResult.Error -> SyncUiState.Error(result.message)
                SyncAllResult.NoServer -> SyncUiState.Error("Zadajte URL servera v nastaveniach")
                SyncAllResult.NotLoggedIn -> SyncUiState.Error("Prihláste sa pred synchronizáciou")
            }
        }
    }
}
