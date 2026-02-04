import SwiftUI

/// Primary action button with customizable colors
struct PrimaryButton: View {
    let title: String
    let action: () -> Void
    var backgroundColor: Color = .accentPrimary
    var foregroundColor: Color = .textPrimary

    var body: some View {
        Button(action: action) {
            Text(title)
                .font(.headline)
                .foregroundColor(foregroundColor)
                .frame(maxWidth: .infinity)
                .frame(height: 56)
                .background(backgroundColor)
                .clipShape(RoundedRectangle(cornerRadius: 16))
        }
    }
}

/// Secondary (outline/glass) button
struct SecondaryButton: View {
    let title: String
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(title)
                .font(.headline)
                .foregroundColor(.textPrimary)
                .frame(maxWidth: .infinity)
                .frame(height: 56)
                .background(Color.glassBackground)
                .clipShape(RoundedRectangle(cornerRadius: 16))
                .overlay(
                    RoundedRectangle(cornerRadius: 16)
                        .stroke(Color.glassBorder, lineWidth: 1)
                )
        }
    }
}

/// Danger/destructive action button
struct DangerButton: View {
    let title: String
    let action: () -> Void

    var body: some View {
        PrimaryButton(
            title: title,
            action: action,
            backgroundColor: .timerDanger
        )
    }
}

#Preview {
    ZStack {
        Color.backgroundDark.ignoresSafeArea()

        VStack(spacing: 16) {
            PrimaryButton(title: "Start Timer") {}
            SecondaryButton(title: "Cancel") {}
            DangerButton(title: "Stop Alarm") {}
        }
        .padding()
    }
}
