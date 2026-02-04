package com.iganapolsky.randomtimer.feedback

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class FeedbackManager @Inject constructor(
    private val context: Context
) {
    companion object {
        private const val FEEDBACK_EMAIL = "igor.ganapolsky@gmail.com"
        private const val FEEDBACK_SUBJECT = "Random Timer Feedback"
    }

    fun sendFeedback() {
        val deviceInfo = buildDeviceInfo()
        val body = """


---
Device Info (please don't delete):
$deviceInfo
""".trimIndent()

        val intent = Intent(Intent.ACTION_SENDTO).apply {
            data = Uri.parse("mailto:")
            putExtra(Intent.EXTRA_EMAIL, arrayOf(FEEDBACK_EMAIL))
            putExtra(Intent.EXTRA_SUBJECT, FEEDBACK_SUBJECT)
            putExtra(Intent.EXTRA_TEXT, body)
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        }

        context.startActivity(Intent.createChooser(intent, "Send Feedback").apply {
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        })
    }

    private fun buildDeviceInfo(): String {
        val packageInfo = try {
            context.packageManager.getPackageInfo(context.packageName, 0)
        } catch (e: Exception) {
            null
        }

        return """
App Version: ${packageInfo?.versionName ?: "Unknown"} (${packageInfo?.longVersionCode ?: "?"})
Android Version: ${Build.VERSION.RELEASE} (API ${Build.VERSION.SDK_INT})
Device: ${Build.MANUFACTURER} ${Build.MODEL}
""".trimIndent()
    }
}
