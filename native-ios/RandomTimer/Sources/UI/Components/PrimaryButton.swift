import SwiftUI

/// Primary action button with customizable colors and press-state feedback
struct PrimaryButton: View {
    let title: String
    let action: () -> Void
    var backgroundColor: Color = .accentPrimary
    var foregroundColor: Color = .textPrimary

    var body: some View {
        Button(action: action) {
            ZStack {
                RoundedRectangle(cornerRadius: 16)
                    .fill(backgroundColor)
                Text(title)
                    .font(.headline)
                    .multilineTextAlignment(.center)
                    .minimumScaleFactor(0.65)
                    .lineLimit(3)
                    .padding(.horizontal, 10)
                    .foregroundStyle(foregroundColor)
            }
            .frame(maxWidth: .infinity)
            .frame(height: 56)
            .contentShape(RoundedRectangle(cornerRadius: 16))
        }
        .buttonStyle(PressableButtonStyle())
        .accessibilityLabel(title)
    }
}

/// Secondary (outline/glass) button with press-state feedback
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
        .buttonStyle(PressableButtonStyle())
        .accessibilityLabel(title)
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
        .accessibilityLabel(title)
        .accessibilityAddTraits(.isButton)
    }
}

/// Button style that provides visual press feedback (scale + opacity)
struct PressableButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .scaleEffect(configuration.isPressed ? 0.97 : 1.0)
            .opacity(configuration.isPressed ? 0.85 : 1.0)
            .animation(.easeInOut(duration: 0.15), value: configuration.isPressed)
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
