For a **solid color**, two things matter: (1) layout (`ZStack` vs one root + background) and (2) **which `background` overload you use**.

Another answer correctly flags that **`.background(Color.someColor.ignoresSafeArea())` is a bad pattern**: you are passing a **View** (`Color` after `.ignoresSafeArea()`) into the older **view** `background` path, which is **deprecated** in current SDKs. Prefer Apple’s **`ShapeStyle`** background or the **`ViewBuilder`** background instead (see [`background(_:ignoresSafeAreaEdges:)`](https://developer.apple.com/documentation/swiftui/view/background(_:ignoressafeareaedges:)) and [`background(alignment:content:)`](https://developer.apple.com/documentation/swiftui/view/background(alignment:content:))).

### `ZStack` — background layer first (still fine)

Putting `Color` in the stack is **not** the same as the deprecated `background` overload; we still do this in production:

[`ActiveTimerScreen.swift` (lines 75–78)](https://github.com/IgorGanapolsky/Random-Timer/blob/develop/native-ios/RandomTimer/Sources/UI/Screens/ActiveTimerScreen.swift#L75-L78)

```swift
ZStack {
    Color.backgroundDark.ignoresSafeArea()
    // … content …
}
```

Same idea in [`CircularTimerView.swift`](https://github.com/IgorGanapolsky/Random-Timer/blob/develop/native-ios/RandomTimer/Sources/UI/Components/CircularTimerView.swift#L270-L272) and [`GlassCard.swift`](https://github.com/IgorGanapolsky/Random-Timer/blob/develop/native-ios/RandomTimer/Sources/UI/Components/GlassCard.swift#L26-L28).

### Full-screen **color** on one root — use `ShapeStyle` `background`, not `Color`+`ignoresSafeArea()` inside `background(...)`

When the root is already a single structure (here with `safeAreaInset` for the bottom bar), use **`Color` as a `ShapeStyle`** and let the modifier handle safe area:

[`TimerSetupScreen.swift`](https://github.com/IgorGanapolsky/Random-Timer/blob/develop/native-ios/RandomTimer/Sources/UI/Screens/TimerSetupScreen.swift) (search for `background(Color.backgroundDark` — we use **`ignoresSafeAreaEdges`** there, not `.ignoresSafeArea()` on the color):

```swift
// … ScrollView + content …
.safeAreaInset(edge: .bottom) { /* primary button */ }
.background(Color.backgroundDark, ignoresSafeAreaEdges: .all)
```

(`ignoresSafeAreaEdges` defaults to `.all` for this overload; you can omit it if you want the default.)

**Alternative** for arbitrary background **views** (images, stacks): `background(alignment:content:)`:

```swift
.background {
    Color.blue
        .ignoresSafeArea() // OK here: background uses the ViewBuilder API
}
```

For **filled shapes** with a style, [`background(_:in:fillStyle:)`](https://developer.apple.com/documentation/swiftui/view/background(_:in:fillstyle:)) is also the modern tool.

### Full-screen **image** (`scaledToFill`)

We don’t ship that exact pattern in the app, so no repo link. Same layout rule as before: give `scaledToFill` a **definite** full-screen proposal (e.g. `background { … }` on an expanded container), not a loosely sized bottom `ZStack` layer — see [this related question](https://stackoverflow.com/q/79341392/20386264).

---

Disclosure: I work on Random Tactical Timer; the GitHub links above are to that app’s source.
