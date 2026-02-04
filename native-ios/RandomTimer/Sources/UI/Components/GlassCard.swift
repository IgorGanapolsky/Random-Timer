import SwiftUI

/// Glassmorphism card component
struct GlassCard<Content: View>: View {
    let content: Content

    init(@ViewBuilder content: () -> Content) {
        self.content = content()
    }

    var body: some View {
        content
            .padding(24)
            .background(
                RoundedRectangle(cornerRadius: 24)
                    .fill(Color.glassBackground)
                    .overlay(
                        RoundedRectangle(cornerRadius: 24)
                            .stroke(Color.glassBorder, lineWidth: 1)
                    )
            )
    }
}

#Preview {
    ZStack {
        Color.backgroundDark.ignoresSafeArea()

        GlassCard {
            VStack(alignment: .leading, spacing: 8) {
                Text("Glass Card")
                    .font(.headline)
                    .foregroundColor(.textPrimary)

                Text("This is a glassmorphism card component")
                    .font(.subheadline)
                    .foregroundColor(.textSecondary)
            }
        }
        .padding()
    }
}
