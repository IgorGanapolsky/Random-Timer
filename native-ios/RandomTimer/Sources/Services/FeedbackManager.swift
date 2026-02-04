import UIKit
import MessageUI

/// Manages user feedback via email
@MainActor
final class FeedbackManager: NSObject {
    static let shared = FeedbackManager()

    private let feedbackEmail = "igor.ganapolsky@gmail.com"
    private let feedbackSubject = "Random Timer Feedback"

    private override init() {
        super.init()
    }

    func sendFeedback(from viewController: UIViewController) {
        if MFMailComposeViewController.canSendMail() {
            let mailVC = MFMailComposeViewController()
            mailVC.mailComposeDelegate = self
            mailVC.setToRecipients([feedbackEmail])
            mailVC.setSubject(feedbackSubject)
            mailVC.setMessageBody(buildEmailBody(), isHTML: false)
            viewController.present(mailVC, animated: true)
        } else {
            // Fallback to mailto: URL
            openMailtoURL()
        }
    }

    private func buildEmailBody() -> String {
        let deviceInfo = buildDeviceInfo()
        return """


---
Device Info (please don't delete):
\(deviceInfo)
"""
    }

    private func buildDeviceInfo() -> String {
        let appVersion = Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "Unknown"
        let buildNumber = Bundle.main.infoDictionary?["CFBundleVersion"] as? String ?? "?"
        let systemVersion = UIDevice.current.systemVersion
        let deviceModel = UIDevice.current.model

        return """
App Version: \(appVersion) (\(buildNumber))
iOS Version: \(systemVersion)
Device: \(deviceModel)
"""
    }

    private func openMailtoURL() {
        let deviceInfo = buildDeviceInfo().addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? ""
        let body = "%0A%0A---%0ADevice Info:%0A\(deviceInfo)"
        let urlString = "mailto:\(feedbackEmail)?subject=\(feedbackSubject.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? "")&body=\(body)"

        if let url = URL(string: urlString) {
            UIApplication.shared.open(url)
        }
    }
}

extension FeedbackManager: MFMailComposeViewControllerDelegate {
    nonisolated func mailComposeController(_ controller: MFMailComposeViewController, didFinishWith result: MFMailComposeResult, error: Error?) {
        controller.dismiss(animated: true)
    }
}
