import SwiftUI

/// Custom range slider for selecting min/max timer duration
struct RangeSliderView: View {
    @Binding var minValue: Double
    @Binding var maxValue: Double

    let range: ClosedRange<Double>
    let step: Double

    init(
        minValue: Binding<Double>,
        maxValue: Binding<Double>,
        range: ClosedRange<Double> = 1...60,
        step: Double = 1
    ) {
        self._minValue = minValue
        self._maxValue = maxValue
        self.range = range
        self.step = step
    }

    var body: some View {
        VStack(spacing: 16) {
            // Labels
            HStack {
                Text("Min: \(Int(minValue)) min")
                    .font(.subheadline)
                    .foregroundColor(.textSecondary)
                Spacer()
                Text("Max: \(Int(maxValue)) min")
                    .font(.subheadline)
                    .foregroundColor(.textSecondary)
            }

            // Display values
            HStack(alignment: .firstTextBaseline, spacing: 4) {
                Text("\(Int(minValue))")
                    .font(.system(size: 28, weight: .semibold))
                    .foregroundColor(.textPrimary)

                Text("-")
                    .font(.system(size: 28, weight: .semibold))
                    .foregroundColor(.textSecondary)

                Text("\(Int(maxValue))")
                    .font(.system(size: 28, weight: .semibold))
                    .foregroundColor(.textPrimary)

                Text("min")
                    .font(.headline)
                    .foregroundColor(.textMuted)
                    .padding(.leading, 8)
            }

            // Min slider
            VStack(alignment: .leading, spacing: 4) {
                Text("Minimum")
                    .font(.caption)
                    .foregroundColor(.textMuted)

                Slider(value: $minValue, in: range, step: step) { _ in
                    // Ensure min doesn't exceed max - 1
                    if minValue >= maxValue {
                        minValue = maxValue - step
                    }
                }
                .tint(.accentPrimary)
            }

            // Max slider
            VStack(alignment: .leading, spacing: 4) {
                Text("Maximum")
                    .font(.caption)
                    .foregroundColor(.textMuted)

                Slider(value: $maxValue, in: range, step: step) { _ in
                    // Ensure max doesn't go below min + 1
                    if maxValue <= minValue {
                        maxValue = minValue + step
                    }
                }
                .tint(.accentPrimary)
            }

            // Helper text
            Text("Timer will go off at a random time within this range")
                .font(.caption)
                .foregroundColor(.textMuted)
                .padding(.top, 8)
        }
    }
}

#Preview {
    ZStack {
        Color.backgroundDark.ignoresSafeArea()

        RangeSliderView(
            minValue: .constant(5),
            maxValue: .constant(15)
        )
        .padding()
    }
}
