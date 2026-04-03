package com.iganapolsky.randomtimer.appfunctions

import androidx.appfunctions.AppFunctionData
import androidx.appfunctions.AppFunctionSearchSpec
import androidx.appfunctions.ExecuteAppFunctionRequest
import androidx.appfunctions.ExecuteAppFunctionResponse
import androidx.appfunctions.testing.AppFunctionTestRule
import androidx.test.core.app.ApplicationProvider
import com.google.common.truth.Truth.assertThat
import com.iganapolsky.randomtimer.RandomTimerApp
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.test.runTest
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@OptIn(ExperimentalCoroutinesApi::class)
@RunWith(RobolectricTestRunner::class)
@Config(application = RandomTimerApp::class, sdk = [34])
class RandomTimerAppFunctionsE2ETest {
    private val context = ApplicationProvider.getApplicationContext<RandomTimerApp>()

    @get:Rule
    val appFunctionTestRule = AppFunctionTestRule(context)

    @Test
    fun `startRandomTimer is discoverable and executable through app functions manager`() =
        runTest {
            val manager = appFunctionTestRule.getAppFunctionManager()
            val packageMetadata =
                manager
                    .observeAppFunctions(
                        AppFunctionSearchSpec(
                            packageNames = setOf(context.packageName),
                        ),
                    ).first()
                    .single { metadata -> metadata.packageName == context.packageName }

            val functionMetadata =
                packageMetadata.appFunctions.single { metadata ->
                    metadata.id == RandomTimerAppFunctionsIds.START_RANDOM_TIMER_ID
                }

            val request =
                ExecuteAppFunctionRequest(
                    targetPackageName = context.packageName,
                    functionIdentifier = functionMetadata.id,
                    functionParameters =
                        AppFunctionData
                            .Builder(functionMetadata.parameters, functionMetadata.components)
                            .setInt("minSeconds", 20)
                            .setInt("maxSeconds", 20)
                            .setInt("alarmDuration", 10)
                            .setString("soundType", "INTENSE")
                            .setBoolean("voiceEnabled", false)
                            .setString("voiceGender", "MALE")
                            .setBoolean("hiddenMode", false)
                            .setBoolean("repeatEnabled", false)
                            .setBoolean("vibrationEnabled", false)
                            .build(),
                )

            val response = manager.executeAppFunction(request)

            assertThat(response).isInstanceOf(ExecuteAppFunctionResponse.Success::class.java)
            val payload =
                (response as ExecuteAppFunctionResponse.Success)
                    .returnValue
                    .getAppFunctionData(ExecuteAppFunctionResponse.Success.PROPERTY_RETURN_VALUE)
            checkNotNull(payload)
            assertThat(payload.getString("action")).isEqualTo("start_random_timer")
            assertThat(payload.getString("status")).isEqualTo("running")
            assertThat(payload.getInt("minSeconds")).isEqualTo(20)
            assertThat(payload.getInt("targetDurationSeconds")).isEqualTo(20)
            assertThat(payload.getString("soundType")).isEqualTo("INTENSE")
        }
}
