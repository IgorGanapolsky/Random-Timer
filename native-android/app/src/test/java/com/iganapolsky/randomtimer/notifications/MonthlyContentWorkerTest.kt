package com.iganapolsky.randomtimer.notifications

import android.app.NotificationManager
import android.content.Context
import androidx.test.core.app.ApplicationProvider
import androidx.work.ListenableWorker
import androidx.work.WorkerParameters
import io.mockk.every
import io.mockk.mockk
import io.mockk.mockkStatic
import io.mockk.unmockkStatic
import kotlinx.coroutines.runBlocking
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.Shadows
import java.util.Calendar

@RunWith(RobolectricTestRunner::class)
class MonthlyContentWorkerTest {

    private lateinit var context: Context

    @Before
    fun setup() {
        context = ApplicationProvider.getApplicationContext()
    }

    @After
    fun tearDown() {
        unmockkStatic(Calendar::class)
    }

    @Test
    fun `doWork shows dynamic notification on 1st when Pro`() = runBlocking {
        mockkStatic(Calendar::class)
        val calendar = mockk<Calendar>()
        every { Calendar.getInstance() } returns calendar
        every { calendar.get(Calendar.DAY_OF_MONTH) } returns 1

        val worker =
            MonthlyContentWorker(
                context,
                mockk(relaxed = true),
                calendarProvider = { calendar },
                isProProvider = { true },
                releaseMonthProvider = { "2026-05" },
            )
        val result = worker.doWork()

        assertEquals(ListenableWorker.Result.success(), result)

        val notificationManager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        val shadowNotificationManager = Shadows.shadowOf(notificationManager)
        assertEquals(1, shadowNotificationManager.size())
        val notification = shadowNotificationManager.getNotification(MonthlyContentWorker.NOTIFICATION_ID)
        assertEquals("New Audio Drops for May 2026", notification.extras.getString("android.title"))
    }

    @Test
    fun `doWork skips notification when not Pro`() = runBlocking {
        mockkStatic(Calendar::class)
        val calendar = mockk<Calendar>()
        every { Calendar.getInstance() } returns calendar
        every { calendar.get(Calendar.DAY_OF_MONTH) } returns 1

        val worker =
            MonthlyContentWorker(
                context,
                mockk(relaxed = true),
                isProProvider = { false },
                releaseMonthProvider = { "2026-05" },
            )
        val result = worker.doWork()

        assertEquals(ListenableWorker.Result.success(), result)
        val notificationManager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        assertEquals(0, Shadows.shadowOf(notificationManager).size())
    }

    @Test
    fun `doWork does not notify on non-first day`() = runBlocking {
        mockkStatic(Calendar::class)
        val calendar = mockk<Calendar>()
        every { Calendar.getInstance() } returns calendar
        every { calendar.get(Calendar.DAY_OF_MONTH) } returns 15

        val worker =
            MonthlyContentWorker(
                context,
                mockk(relaxed = true),
                isProProvider = { true },
                releaseMonthProvider = { "2026-05" },
            )
        val result = worker.doWork()

        assertEquals(ListenableWorker.Result.success(), result)
        val notificationManager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        assertEquals(0, Shadows.shadowOf(notificationManager).size())
    }
}
