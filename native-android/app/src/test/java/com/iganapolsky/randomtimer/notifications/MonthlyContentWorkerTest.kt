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
    fun `doWork returns success and shows notification on 1st of month`() = runBlocking {
        mockkStatic(Calendar::class)
        val calendar = mockk<Calendar>()
        every { Calendar.getInstance() } returns calendar
        every { calendar.get(Calendar.DAY_OF_MONTH) } returns 1

        val worker = MonthlyContentWorker(context, mockk(relaxed = true))
        val result = worker.doWork()

        assertEquals(ListenableWorker.Result.success(), result)
        
        val notificationManager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        val shadowNotificationManager = Shadows.shadowOf(notificationManager)
        assertEquals(1, shadowNotificationManager.size())
    }

    @Test
    fun `doWork returns success and does NOT show notification on other days`() = runBlocking {
        mockkStatic(Calendar::class)
        val calendar = mockk<Calendar>()
        every { Calendar.getInstance() } returns calendar
        every { calendar.get(Calendar.DAY_OF_MONTH) } returns 15

        val worker = MonthlyContentWorker(context, mockk(relaxed = true))
        val result = worker.doWork()

        assertEquals(ListenableWorker.Result.success(), result)
        val notificationManager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        val shadowNotificationManager = Shadows.shadowOf(notificationManager)
        assertEquals(0, shadowNotificationManager.size())
    }
}
