package com.iganapolsky.randomtimer.appfunctions

import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import dagger.hilt.EntryPoint

@EntryPoint
@InstallIn(SingletonComponent::class)
interface RandomTimerAppFunctionEntryPoint {
    fun randomTimerAppFunctionHandler(): RandomTimerAppFunctionHandler
}
