package com.iganapolsky.randomtimer.appfunctions

import androidx.appfunctions.AppFunctionSerializable

@AppFunctionSerializable(isDescribedByKDoc = true)
data class TimerFunctionResult(
    val action: String,
    val status: String,
    val message: String,
    val entitlementLevel: String,
    val minSeconds: Int = 0,
    val maxSeconds: Int = 0,
    val alarmDuration: Int = 0,
    val targetDurationSeconds: Int = 0,
    val soundType: String,
    val voiceEnabled: Boolean = false,
    val voiceGender: String,
    val hiddenMode: Boolean = false,
    val repeatEnabled: Boolean = false,
    val vibrationEnabled: Boolean = false,
)
