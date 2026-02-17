import Foundation
import os

extension Logger {
    private static let subsystem = Bundle.main.bundleIdentifier ?? "com.igorganapolsky.randomtimer"

    static let timer = Logger(subsystem: subsystem, category: "timer")
    static let notification = Logger(subsystem: subsystem, category: "notification")
    static let liveActivity = Logger(subsystem: subsystem, category: "liveActivity")
    static let analytics = Logger(subsystem: subsystem, category: "analytics")
}
