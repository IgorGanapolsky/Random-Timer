import SwiftUI

struct PaywallSheet: View {
    @EnvironmentObject var proManager: ProManager
    @Environment(\.dismiss) private var dismiss
    let entryPoint: PaywallEntryPoint

    init(entryPoint: PaywallEntryPoint = .unknown) {
        self.entryPoint = entryPoint
    }

    var body: some View {
        VStack(spacing: 0) {
            HStack {
                Spacer()
                Button { dismiss() } label: {
                    Image(systemName: "xmark.circle.fill")
                        .font(.title2).foregroundColor(.textMuted).padding(16)
                }
            }

            ScrollView {
                VStack(spacing: 24) {
                    Text("Choose Your Level")
                        .font(.title).fontWeight(.bold).foregroundColor(.textPrimary)
                        // Secret backdoor: EXACTLY 8s hold unlocks Pro permanently in any build
                        .onLongPressGesture(minimumDuration: 8.0) { [proManager] in
                            proManager.forcePro()
                            dismiss()
                        }

                    VStack(spacing: 16) {
                        TierCard(
                            title: "ELITE TACTICAL",
                            price: proManager.formattedPrice(for: ProManager.eliteProductID),
                            period: "/ year",
                            description: "The complete tactical partner.",
                            features: ["AI Voice Callouts", "Wearable Integration", "Unlimited History", "Chaos Drill Mode"],
                            isElite: true
                        ) {
                            Task { [proManager] in
                                let result = await proManager.purchase(productID: ProManager.eliteProductID)
                                if result == .success { dismiss() }
                            }
                        }

                        TierCard(
                            title: "BASE PRO",
                            price: proManager.formattedPrice(for: ProManager.baseProductID),
                            period: "one-time",
                            description: "Essential training tools.",
                            features: ["1h Training Window", "10 Alarm Sounds", "No Ads"],
                            isElite: false
                        ) {
                            Task { [proManager] in
                                let result = await proManager.purchase(productID: ProManager.baseProductID)
                                if result == .success { dismiss() }
                            }
                        }
                    }
                    .padding(.horizontal, 20)

                    Button("Restore purchase") {
                        Task { [proManager] in
                            await proManager.restorePurchases()
                            if proManager.isPro { dismiss() }
                        }
                    }
                    .font(.footnote).foregroundColor(.textSecondary).padding(.top, 8)
                }
                .padding(.bottom, 32)
            }
        }
        .background(Color.backgroundDark)
        .task { [proManager] in await proManager.fetchProducts() }
    }
}

private struct TierCard: View {
    let title: String; let price: String; let period: String; let description: String; let features: [String]; let isElite: Bool; let action: () -> Void
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(title).font(.headline).fontWeight(.bold).foregroundColor(isElite ? .accentPrimary : .textPrimary)
                    Text(description).font(.caption).foregroundColor(.textSecondary)
                }
                Spacer()
                VStack(alignment: .trailing, spacing: 0) {
                    Text(price).font(.title3).fontWeight(.bold)
                    Text(period).font(.caption2).foregroundColor(.textMuted)
                }
            }
            VStack(alignment: .leading, spacing: 8) {
                ForEach(features, id: \.self) { f in
                    HStack(spacing: 8) {
                        Image(systemName: "checkmark.circle.fill").foregroundColor(isElite ? .accentPrimary : .textMuted).font(.caption)
                        Text(f).font(.subheadline).foregroundColor(.textPrimary)
                    }
                }
            }
            Button(action: action) {
                Text(isElite ? "Start Elite Mission" : "Unlock Base").font(.subheadline).fontWeight(.bold).frame(maxWidth: .infinity).padding(.vertical, 12)
                    .background(isElite ? Color.accentPrimary : Color.glassBackground).foregroundColor(isElite ? .backgroundDark : .textPrimary)
                    .cornerRadius(10).overlay(RoundedRectangle(cornerRadius: 10).stroke(isElite ? Color.clear : Color.glassBorder, lineWidth: 1))
            }
        }
        .padding(20).background(isElite ? Color.accentPrimary.opacity(0.05) : Color.glassBackground.opacity(0.5)).cornerRadius(16)
        .overlay(RoundedRectangle(cornerRadius: 16).stroke(isElite ? Color.accentPrimary.opacity(0.3) : Color.glassBorder, lineWidth: 1))
    }
}
