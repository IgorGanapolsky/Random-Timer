# Random Timer

Random Timer is a single-screen React Native app for sports and combative
training. It arms a random trigger within your chosen range and fires a timer
or haptic alarm without revealing the countdown.

## Features
- Random trigger within a min/max range
- Timer mode (counts up after trigger)
- Alarm mode (haptics until stopped or snoozed)
- Hidden countdown by design
- Light and dark UI

## Getting started
1. Install dependencies:
   - yarn install
2. Install iOS pods:
   - cd ios && pod install && cd ..
3. Start Metro:
   - yarn start
4. Run the app:
   - yarn ios
   - yarn android

## App behavior
- Set a min and max range, then press Start.
- The trigger time is hidden so you cannot predict it.
- Timer mode counts up after the trigger.
- Alarm mode vibrates until you stop or snooze.

## Testing
- yarn lint
- yarn test
