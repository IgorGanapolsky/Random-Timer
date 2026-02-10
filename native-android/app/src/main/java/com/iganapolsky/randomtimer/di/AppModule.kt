package com.iganapolsky.randomtimer.di

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.PreferenceDataStoreFactory
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.preferencesDataStoreFile
import com.iganapolsky.randomtimer.data.SoundPreviewManagerImpl
import com.iganapolsky.randomtimer.data.repository.TimerRepositoryImpl
import com.iganapolsky.randomtimer.domain.SoundPreviewManager
import com.iganapolsky.randomtimer.domain.repository.TimerRepository
import com.iganapolsky.randomtimer.service.TimerServiceController
import com.iganapolsky.randomtimer.service.TimerServiceControllerImpl
import dagger.Binds
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import javax.inject.Singleton
import kotlin.random.Random

@Module
@InstallIn(SingletonComponent::class)
object AppModule {

    @Provides
    @Singleton
    fun provideDataStore(
        @ApplicationContext context: Context
    ): DataStore<Preferences> {
        return PreferenceDataStoreFactory.create {
            context.preferencesDataStoreFile("timer_preferences")
        }
    }

    @Provides
    @Singleton
    fun provideRandom(): Random = Random.Default

    @Provides
    @Singleton
    fun provideCoroutineScope(): CoroutineScope =
        CoroutineScope(SupervisorJob() + Dispatchers.Main)
}

@Module
@InstallIn(SingletonComponent::class)
abstract class RepositoryModule {

    @Binds
    @Singleton
    abstract fun bindTimerRepository(
        impl: TimerRepositoryImpl
    ): TimerRepository

    @Binds
    @Singleton
    abstract fun bindSoundPreviewManager(
        impl: SoundPreviewManagerImpl
    ): SoundPreviewManager

    @Binds
    @Singleton
    abstract fun bindTimerServiceController(
        impl: TimerServiceControllerImpl
    ): TimerServiceController
}
