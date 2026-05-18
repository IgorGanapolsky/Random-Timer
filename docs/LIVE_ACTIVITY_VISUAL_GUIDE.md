# Live Activity Visual Guide

## Lock Screen Layout

```
┌─────────────────────────────────────┐
│  🕐  Random Timer                   │
│      Timer: 1m - 3m            ⭕   │
│                                 │   │
│                            Progress │
└─────────────────────────────────────┘
```

**Components**:
- **Left Icon**: Pulsing timer icon with glow
- **Timer Name**: "Random Timer" in bold white
- **Range Display**: "Timer: 1m - 3m" in muted white
- **Progress Ring**: Animated circular indicator (right side)

**Colors** (status-based):
- 🟢 Running: Emerald green (#10B981)
- 🟡 Warning: Amber (#F59E0B)
- 🔴 Danger/Alarm: Rose red (#EF4444)

## Dynamic Island - Compact View

```
┌──────────────┐
│ 🕐    1m-3m  │
└──────────────┘
```

**Layout**:
- Left: Animated timer icon
- Right: Compact range ("1m-3m" in monospaced font)

## Dynamic Island - Expanded View

```
┌───────────────────────────────────────┐
│                                       │
│  🕐              Random Timer   ⚫Active│
│                                       │
│              Timer Active             │
│                                       │
│               1m - 3m                 │
│                                       │
│            Random interval            │
│                                       │
│         ┌─────────────┐              │
│         │ 🛑 Stop     │              │
│         └─────────────┘              │
└───────────────────────────────────────┘
```

**Regions**:
- **Leading (left)**: Large timer icon with glow
- **Trailing (right)**: Status badge pill
- **Center**:
  - Timer name (headline)
  - "Timer Active" (subheadline)
  - "1m - 3m" (large bold monospaced)
  - "Random interval" (caption)
- **Bottom**: Red stop button (ready for App Intent)

## Animations

### Timer Icon
- **Running**: Continuous pulse effect
- **Alarm**: Bounce effect (repeating)
- **Paused**: Static

### Progress Ring
- **Update**: Smooth easing animation (0.5s duration)
- **Pulse**: Subtle ±5% pulse for visual interest
- **Complete**: Checkmark icon

### Bell Icon (Alarm)
- **Bounce**: Repeating bounce animation
- **Color**: Red (#EF4444)

## State Variations

### Running State
```
🕐 Random Timer
   Timer: 1m - 3m
   [Green progress ring showing ~50%]
```

### Warning State (< 30s)
```
🕐 Random Timer
   Timer: 1m - 3m
   [Amber progress ring showing ~90%]
```

### Danger State (< 10s)
```
🕐 Random Timer
   Timer: 1m - 3m
   [Red progress ring showing ~95%]
```

### Alarm State
```
🔔 Random Timer
   Time's up!
   [Red checkmark icon]
```

## Typography

- **Timer Name**: `.headline` (bold, 17pt)
- **Range Text**: `.subheadline` (regular, 15pt)
- **Status**: `.title3` (bold, 20pt)
- **Large Numbers**: `.title2` (bold, 22pt, monospaced)
- **Captions**: `.caption` (regular, 12pt)

## Spacing

- **Horizontal Padding**: 16pt
- **Vertical Padding**: 12pt (Lock Screen), 8pt (Dynamic Island)
- **Icon Spacing**: 16pt between elements
- **Text Spacing**: 4pt between lines in same block

## Accessibility

### VoiceOver Labels
- Timer Icon: "Timer running"
- Progress Ring: "Timer progress, 50 percent"
- Status Badge: "Active status"
- Stop Button: "Stop timer"

### Dynamic Type
- All text scales with system font size
- Maintains relative sizing relationships
- Minimum touch targets: 44x44pt

## Color Palette

```
Background Dark:   #0F0A1A  ■■■■■
Emerald Green:     #10B981  ■■■■■
Amber:             #F59E0B  ■■■■■
Rose Red:          #EF4444  ■■■■■
Red:             #EF4444  ■■■■■
White:             #F8FAFC  ■■■■■
Muted Gray:        #A1A1AA  ■■■■■
```

## SF Symbols Used

- `timer` - Main timer icon
- `bell.badge.fill` - Alarm notification
- `pause.circle.fill` - Paused state
- `stop.fill` - Stop button
- `checkmark` - Completion indicator

## Device Compatibility

- **Lock Screen**: iOS 16.1+, all devices
- **Dynamic Island**: iOS 16.1+, iPhone 14 Pro or newer
  - Fallback: Shows in notification/banner on older devices
- **Compact View**: iPhone 14 Pro/Max, iPhone 15 Pro/Max
- **Expanded View**: Long press Dynamic Island

## Real-World Examples

### Example 1: Meditation Timer
```
User sets: 5m - 10m
Live Activity shows: "Timer: 5m - 10m"
No exact countdown → preserves surprise
Green pulsing icon → calming visual
```

### Example 2: Workout Rest
```
User sets: 30s - 2m
Live Activity shows: "Timer: 30s - 2m"
Progress ring → visual feedback
Can glance without unlocking phone
```

### Example 3: Cooking Timer
```
User sets: 10m - 15m
Live Activity shows: "Timer: 10m - 15m"
Bouncing bell when done → clear alert
Can dismiss from Lock Screen
```

## Design Inspiration

Inspired by:
- **Apple Fitness**: Clean, status-based colors
- **Focus Time**: Pulsing animation during active session
- **Timer apps**: Circular progress indicators
- **iOS HIG**: Native feel, SF Symbols, system fonts

## Best Practices

1. **Keep it Glanceable**: User should understand status in <1 second
2. **Respect Privacy**: Don't reveal exact time remaining (random timer)
3. **Use System Colors**: Maintain consistency with iOS
4. **Animate Purposefully**: Every animation has meaning
5. **Support Accessibility**: Always include labels and values
6. **Be Battery Conscious**: Only update when necessary

## Testing Checklist

- [ ] Lock Screen displays correctly
- [ ] Dynamic Island compact view works
- [ ] Dynamic Island expanded view works
- [ ] Animations are smooth (60fps)
- [ ] VoiceOver reads correctly
- [ ] Dynamic Type scales properly
- [ ] Colors match design system
- [ ] Status changes update Live Activity
- [ ] Alarm state shows bouncing bell
- [ ] Progress ring animates smoothly

## Preview Screenshots

To see the actual rendered views:
1. Open Xcode
2. Navigate to `RandomTimerWidget/RandomTimerLiveActivity.swift`
3. Use Xcode Previews (Canvas)
4. Toggle between different preview configurations
5. Test on physical device for Dynamic Island

## Notes

- The Live Activity automatically dismisses after timer completes (based on `staleDate`)
- System may limit number of concurrent Live Activities
- Live Activities persist across app launches
- User can disable Live Activities in Settings
- Widget extension runs in limited memory/CPU environment
