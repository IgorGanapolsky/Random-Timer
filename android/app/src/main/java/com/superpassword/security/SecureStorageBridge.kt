package com.superpassword.security

import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import com.facebook.react.bridge.*
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

class SecureStorageBridge(reactContext: ReactApplicationContext) : ReactContextBaseJavaModule(reactContext) {

  override fun getName(): String = "SecureStorageBridge"

  private val keyAlias = "SuperPasswordKey"
  private val androidKeyStore = "AndroidKeyStore"

  private fun getOrCreateKey(): SecretKey {
    val keyStore = KeyStore.getInstance(androidKeyStore)
    keyStore.load(null)

    val existingKey = keyStore.getEntry(keyAlias, null) as? KeyStore.SecretKeyEntry
    if (existingKey != null) return existingKey.secretKey

    val keyGenerator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, androidKeyStore)
    val spec = KeyGenParameterSpec.Builder(
      keyAlias,
      KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT
    )
      .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
      .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
      .setRandomizedEncryptionRequired(true)
      .setUserAuthenticationRequired(false)
      .build()

    keyGenerator.init(spec)
    return keyGenerator.generateKey()
  }

  @ReactMethod
  fun setSecureItem(key: String, value: String, promise: Promise) {
    try {
      val secretKey = getOrCreateKey()
      val cipher = Cipher.getInstance("AES/GCM/NoPadding")
      cipher.init(Cipher.ENCRYPT_MODE, secretKey)
      val iv = cipher.iv
      val encrypted = cipher.doFinal(value.toByteArray(Charsets.UTF_8))

      val data = Base64.encodeToString(iv + encrypted, Base64.NO_WRAP)
      val prefs = reactApplicationContext.getSharedPreferences("secure_store", 0)
      prefs.edit().putString(key, data).apply()

      promise.resolve(true)
    } catch (e: Exception) {
      promise.reject("SECURE_STORAGE_ERROR", "Failed to encrypt and store value", e)
    }
  }

  @ReactMethod
  fun getSecureItem(key: String, promise: Promise) {
    try {
      val prefs = reactApplicationContext.getSharedPreferences("secure_store", 0)
      val data = prefs.getString(key, null) ?: run {
        promise.reject("SECURE_STORAGE_ERROR", "No value found for key")
        return
      }

      val allBytes = Base64.decode(data, Base64.NO_WRAP)
      val iv = allBytes.copyOfRange(0, 12)
      val encrypted = allBytes.copyOfRange(12, allBytes.size)

      val secretKey = getOrCreateKey()
      val cipher = Cipher.getInstance("AES/GCM/NoPadding")
      val spec = GCMParameterSpec(128, iv)
      cipher.init(Cipher.DECRYPT_MODE, secretKey, spec)

      val decrypted = cipher.doFinal(encrypted)
      promise.resolve(String(decrypted, Charsets.UTF_8))
    } catch (e: Exception) {
      promise.reject("SECURE_STORAGE_ERROR", "Failed to retrieve and decrypt value", e)
    }
  }

  @ReactMethod
  fun removeSecureItem(key: String, promise: Promise) {
    val prefs = reactApplicationContext.getSharedPreferences("secure_store", 0)
    promise.resolve(prefs.edit().remove(key).commit())
  }
}
