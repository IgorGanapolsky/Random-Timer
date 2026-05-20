import Foundation

/// P2 scaffold: non-consumable discipline IAP packs (create in App Store Connect before billing queries).
enum DisciplinePackCatalog {
    static let packSpecialForces = "pack_special_forces"
    static let packBoxingHiit = "pack_boxing_hiit"
    static let packCrossfit = "pack_crossfit"
    static let packBjj = "pack_bjj"

    static let androidProductIds: [String] = [
        packSpecialForces,
        packBoxingHiit,
        packCrossfit,
        packBjj,
    ]

    static func iosProductId(forAndroidProductId androidId: String) -> String {
        switch androidId {
        case packSpecialForces:
            return "com.iganapolsky.randomtimer.pack.special_forces"
        case packBoxingHiit:
            return "com.iganapolsky.randomtimer.pack.boxing_hiit"
        case packCrossfit:
            return "com.iganapolsky.randomtimer.pack.crossfit"
        case packBjj:
            return "com.iganapolsky.randomtimer.pack.bjj"
        default:
            fatalError("Unknown discipline pack: \(androidId)")
        }
    }

    static var iosProductIds: [String] {
        androidProductIds.map(iosProductId(forAndroidProductId:))
    }
}
