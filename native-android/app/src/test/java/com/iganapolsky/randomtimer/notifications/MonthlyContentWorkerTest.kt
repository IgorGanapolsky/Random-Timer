package com.iganapolsky.randomtimer.notifications

import android.app.NotificationManager
import android.content.Context
import androidx.work.ListenableWorker
import androidx.work.testing.TestListenableWorkerBuilder
import io.mockk.every
import io.mockk.mockk
import io.mockk.mockkStatic
import io.mockk.unmockkStatic
import io.mockk.verify
import kotlinx.coroutines.runBlocking
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Before
import org.junit.Test
import java.util.Calendar

class MonthlyContentWorkerTest {

    private lateinit var context: Context
    private lateinit var notificationManager: NotificationManager

    @Before
    fun setup() {
        context = mockk(relaxed = true)
        notificationManager = mockk(relaxed = true)
        every { context.getSystemService(Context.NOTIFICATION_SERVICE) } returns notificationManager
        every { context.applicationContext } returns context
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

        val worker = TestListenableWorkerBuilder<MonthlyContentWorker>(context).build()
        val result = worker.doWork()

        assertEquals(ListenableWorker.Result.success(), result)
        verify { notificationManager.notify(any(), any()) }
    }

    @Test
    fun `doWork returns success and does NOT show notification on other days`() = runBlocking {
        mockkStatic(Calendar::class)
        val calendar = mockk<Calendar>()
        every { Calendar.getInstance() } returns calendar
        every { calendar.get(Calendar.DAY_OF_MONTH) } returns 15

        val worker = TestListenableWorkerBuilder<MonthlyContentWorker>(context).build()
        val result = worker.doWork()

        assertEquals(ListenableWorker.Result.success(), result)
        verify(exactly = 0) { notificationManager.notify(any(), any()) }
    }
}
