import SwiftUI

struct PaywallSheet: View {
    @EnvironmentObject var proManager: ProManager
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        VStack(spacing: 24) {
            Text("Upgrade to Pro")
                .font(.title2)
                .fontWeight(.bold)
                .foregroundColor(.textPrimary)

            Text("One-time purchase. No subscriptions.")
                .font(.caption)
                .foregroundColor(.textSecondary)

            VStack(alignment: .leading, spacing: 12) {
                ProFeatureRow(text: "10 alarm sounds (vs 2 free)")
                ProFeatureRow(text: "Extended range up to 60 minutes")
                ProFeatureRow(text: "Support independent development")
            }
            .padding(.horizontal)

            PrimaryButton(title: "Unlock Pro \u{2022} \(proManager.formattedPrice)") {
                Task {
                    let success = await proManager.purchase()
                    if success {
                        dismiss()
                    }
                }
            }

            Button("Restore purchase") {
                Task {
                    await proManager.restorePurchases()
                    if proManager.isPro {
                        dismiss()
                    }
                }
            }
            .font(.footnote)
            .foregroundColor(.textSecondary)
        }
        .padding(24)
        .background(Color.backgroundDark)
        .task {
            await proManager.fetchProduct()
        }
    }
}

private struct ProFeatureRow: View {
    let text: String

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: "checkmark")
                .foregroundColor(.accentPrimary)
                .font(.body)
            Text(text)
                .font(.body)
                .foregroundColor(.textPrimary)
        }
    }
}
