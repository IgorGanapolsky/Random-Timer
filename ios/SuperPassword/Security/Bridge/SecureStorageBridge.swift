import Foundation
import React
import SwiftKeychainWrapper
import CryptoSwift

@objc(SecureStorageBridge)
class SecureStorageBridge: NSObject {
    
    @objc
    static func requiresMainQueueSetup() -> Bool {
        return false
    }
    
    @objc
    func setSecureItem(_ key: String, value: String, resolver: @escaping RCTPromiseResolveBlock, rejecter: @escaping RCTPromiseRejectBlock) {
        DispatchQueue.global(qos: .userInitiated).async {
            do {
                // Generate random salt for each encryption
                let salt = AES.randomIV(12)
                let key = try HKDF(password: value, salt: salt, variant: .sha256).calculate()
                
                // Encrypt value
                let aes = try AES(key: key, blockMode: GCM(iv: salt), padding: .pkcs7)
                let encrypted = try aes.encrypt(value.bytes)
                
                // Store in Keychain
                let savedInKeychain = KeychainWrapper.standard.set(
                    Data(encrypted + salt),
                    forKey: key
                )
                
                if savedInKeychain {
                    DispatchQueue.main.async {
                        resolver(true)
                    }
                } else {
                    throw NSError(
                        domain: "SecureStorageBridge",
                        code: -1,
                        userInfo: [NSLocalizedDescriptionKey: "Failed to save to Keychain"]
                    )
                }
            } catch {
                DispatchQueue.main.async {
                    rejecter(
                        "SECURE_STORAGE_ERROR",
                        "Failed to encrypt and store value",
                        error
                    )
                }
            }
        }
    }
    
    @objc
    func getSecureItem(_ key: String, resolver: @escaping RCTPromiseResolveBlock, rejecter: @escaping RCTPromiseRejectBlock) {
        DispatchQueue.global(qos: .userInitiated).async {
            do {
                guard let data = KeychainWrapper.standard.data(forKey: key) else {
                    throw NSError(
                        domain: "SecureStorageBridge",
                        code: -1,
                        userInfo: [NSLocalizedDescriptionKey: "No value found for key"]
                    )
                }
                
                // Extract salt and encrypted data
                let salt = data.suffix(12)
                let encrypted = data.prefix(data.count - 12)
                
                // Decrypt value
                let key = try HKDF(password: String(data: encrypted, encoding: .utf8) ?? "", 
                                 salt: Array(salt),
                                 variant: .sha256).calculate()
                
                let aes = try AES(key: key, blockMode: GCM(iv: Array(salt)), padding: .pkcs7)
                let decrypted = try aes.decrypt(Array(encrypted))
                
                guard let result = String(bytes: decrypted, encoding: .utf8) else {
                    throw NSError(
                        domain: "SecureStorageBridge",
                        code: -1,
                        userInfo: [NSLocalizedDescriptionKey: "Failed to decode decrypted data"]
                    )
                }
                
                DispatchQueue.main.async {
                    resolver(result)
                }
            } catch {
                DispatchQueue.main.async {
                    rejecter(
                        "SECURE_STORAGE_ERROR",
                        "Failed to retrieve and decrypt value",
                        error
                    )
                }
            }
        }
    }
    
    @objc
    func removeSecureItem(_ key: String, resolver: @escaping RCTPromiseResolveBlock, rejecter: @escaping RCTPromiseRejectBlock) {
        DispatchQueue.global(qos: .userInitiated).async {
            let removed = KeychainWrapper.standard.removeObject(forKey: key)
            DispatchQueue.main.async {
                resolver(removed)
            }
        }
    }
}
