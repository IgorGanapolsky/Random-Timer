package com.iganapolsky.randomtimer.di

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.PreferenceDataStoreFactory
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.preferencesDataStoreFile
import com.google.android.play.core.appupdate.AppUpdateManager
import com.google.android.play.core.appupdate.AppUpdateManagerFactory
import com.iganapolsky.randomtimer.data.SoundPreviewManagerImpl
import com.iganapolsky.randomtimer.data.repository.TimerRepositoryImpl
import com.iganapolsky.randomtimer.domain.SoundPreviewManager
import com.iganapolsky.randomtimer.domain.repository.TimerRepository
import com.iganapolsky.randomtimer.service.TimerServiceController
import com.iganapolsky.randomtimer.service.TimerServiceControllerImpl
import com.iganapolsky.randomtimer.analytics.AnalyticsService
import com.iganapolsky.randomtimer.monetization.AdMobRewardedAdPort
import com.iganapolsky.randomtimer.monetization.RewardedAdCoordinator
import com.iganapolsky.randomtimer.monetization.RewardedAdPort
import com.iganapolsky.randomtimer.monetization.RewardedAdUnlockStore
import com.iganapolsky.randomtimer.stats.TrainingStatsService
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
        @ApplicationContext context: Context,
    ): DataStore<Preferences> =
        PreferenceDataStoreFactory.create {
            context.preferencesDataStoreFile("timer_preferences")
        }

    @Provides
    @Singleton
    fun provideTrainingStatsService(
        @ApplicationContext context: Context,
    ): TrainingStatsService = TrainingStatsService(context)

    @Provides
    @Singleton
    fun provideRandom(): Random = Random.Default

    @Provides
    @Singleton
    fun provideCoroutineScope(): CoroutineScope = CoroutineScope(SupervisorJob() + Dispatchers.Main)

    @Provides
    @Singleton
    fun provideAppUpdateManager(
        @ApplicationContext context: Context,
    ): AppUpdateManager = AppUpdateManagerFactory.create(context)

    @Provides
    @Singleton
    fun provideRewardedAdUnlockStore(
        @ApplicationContext context: Context,
    ): RewardedAdUnlockStore = RewardedAdUnlockStore(context)

    @Provides
    @Singleton
    fun provideRewardedAdPort(): RewardedAdPort = AdMobRewardedAdPort()

    @Provides
    @Singleton
    fun provideRewardedAdCoordinator(
        analyticsService: AnalyticsService,
        unlockStore: RewardedAdUnlockStore,
        port: RewardedAdPort,
    ): RewardedAdCoordinator = RewardedAdCoordinator(analyticsService, unlockStore, port)
}

@Module
@InstallIn(SingletonComponent::class)
abstract class RepositoryModule {
    @Binds
    @Singleton
    abstract fun bindTimerRepository(impl: TimerRepositoryImpl): TimerRepository

    @Binds
    @Singleton
    abstract fun bindSoundPreviewManager(impl: SoundPreviewManagerImpl): SoundPreviewManager

    @Binds
    @Singleton
    abstract fun bindTimerServiceController(impl: TimerServiceControllerImpl): TimerServiceController
}
