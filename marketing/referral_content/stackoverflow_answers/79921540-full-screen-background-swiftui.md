For a **solid color**, both patterns are fine. We use **both** in production in [Random Tactical Timer](https://github.com/IgorGanapolsky/Random-Timer) (SwiftUI).

### `ZStack` — background layer first

We paint the screen with `Color.backgroundDark` under the main UI:

[`ActiveTimerScreen.swift` (lines 75–78)](https://github.com/IgorGanapolsky/Random-Timer/blob/develop/native-ios/RandomTimer/Sources/UI/Screens/ActiveTimerScreen.swift#L75-L78)

```swift
ZStack {
    Color.backgroundDark.ignoresSafeArea()
    // … content …
}
```

Same idea appears in previews/components that need the same canvas, e.g. [`CircularTimerView.swift`](https://github.com/IgorGanapolsky/Random-Timer/blob/develop/native-ios/RandomTimer/Sources/UI/Components/CircularTimerView.swift#L270-L272) and [`GlassCard.swift`](https://github.com/IgorGanapolsky/Random-Timer/blob/develop/native-ios/RandomTimer/Sources/UI/Components/GlassCard.swift#L26-L28).

### `.background(…).ignoresSafeArea()` on the root stack

When the root is already a single vertical structure (here with `safeAreaInset` for the bottom bar), we attach the full-screen color on that container:

[`TimerSetupScreen.swift` (line 458)](https://github.com/IgorGanapolsky/Random-Timer/blob/develop/native-ios/RandomTimer/Sources/UI/Screens/TimerSetupScreen.swift#L458)

```swift
// … ScrollView + content …
.safeAreaInset(edge: .bottom) { /* primary button */ }
.background(Color.backgroundDark.ignoresSafeArea())
```

So for **color only**: pick whichever matches your hierarchy—`ZStack` when you think in layers; `.frame(maxWidth: .infinity, maxHeight: .infinity)` + `.background(Color…ignoresSafeArea())` when you want the background on one expanded root (we use the latter on setup, the former on the active timer screen).

### Full-screen **image** (`scaledToFill`)

We don’t ship a full-screen `scaledToFill` image in that form, so I won’t point at our repo for that. In general, `scaledToFill` needs a **definite size**—pin the image with a full-screen proposal (e.g. `.background { Image(…).resizable().scaledToFill().ignoresSafeArea() }` on an expanded container) rather than a loosely sized bottom `ZStack` layer; see [this related question](https://stackoverflow.com/q/79341392/20386264).

---

Disclosure: I work on Random Tactical Timer; the GitHub links above are to that app’s source.
