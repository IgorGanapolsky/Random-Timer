import Foundation

/// Free-tier Pro sound access via subscription or rewarded-ad trial unlock.
enum ProSoundAccess {
    static func canEquipProSound(isPro: Bool, hasTrialUnlock: Bool) -> Bool {
        isPro || hasTrialUnlock
    }

    static func shouldConsumeTrialOnEquip(
        isPro: Bool,
        hasTrialUnlock: Bool,
        previousSound: SoundType,
        newSound: SoundType
    ) -> Bool {
        !isPro &&
            hasTrialUnlock &&
            newSound.isPro &&
            !previousSound.isPro
    }
}
