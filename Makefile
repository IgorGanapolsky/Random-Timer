.PHONY: run-android-device run-android-emulator run-ios-device run-ios-sim fix-ios-device install-hooks
.PHONY: verify verify-android verify-android-instrumentation verify-ios verify-ios-ui maestro-android maestro-ios

ANDROID_DIR := native-android
IOS_DIR := native-ios
ANDROID_PACKAGE := com.iganapolsky.randomtimer
IOS_SCHEME := RandomTimer
IOS_PROJECT := $(IOS_DIR)/RandomTimer.xcodeproj

# Run on connected Android physical device
run-android-device:
	@DEVICE=$$(adb devices | grep -v emulator | grep device$$ | head -1 | cut -f1); \
	if [ -z "$$DEVICE" ]; then \
		echo "ERROR: No physical Android device found. Connect via USB and enable USB debugging."; \
		exit 1; \
	fi; \
	echo "==> Found device: $$DEVICE"; \
	adb -s $$DEVICE reverse tcp:8081 tcp:8081; \
	echo "==> Building and installing debug APK..."; \
	cd $(ANDROID_DIR) && ANDROID_SERIAL=$$DEVICE ./gradlew installDebug; \
	echo "==> Launching app..."; \
	adb -s $$DEVICE shell am start -n $(ANDROID_PACKAGE)/.MainActivity

# Run on Android emulator
run-android-emulator:
	@EMU=$$(adb devices | grep emulator | head -1 | cut -f1); \
	if [ -z "$$EMU" ]; then \
		echo "==> No emulator running. Starting one..."; \
		AVD=$$(emulator -list-avds | head -1); \
		if [ -z "$$AVD" ]; then \
			echo "ERROR: No AVDs configured. Create one in Android Studio."; \
			exit 1; \
		fi; \
		echo "==> Starting emulator: $$AVD"; \
		emulator -avd $$AVD -no-snapshot-load &disown; \
		echo "==> Waiting for emulator to boot..."; \
		adb wait-for-device; \
		sleep 10; \
		EMU=$$(adb devices | grep emulator | head -1 | cut -f1); \
	fi; \
	echo "==> Using emulator: $$EMU"; \
	echo "==> Building and installing debug APK..."; \
	cd $(ANDROID_DIR) && ./gradlew installDebug; \
	echo "==> Launching app..."; \
	adb -s $$EMU shell am start -n $(ANDROID_PACKAGE)/.MainActivity

# Run on connected iOS physical device (uses ios-deploy to avoid devicectl hanging)
run-ios-device:
	@DEVICE_ID=$$(xcodebuild -project $(IOS_PROJECT) -scheme $(IOS_SCHEME) -showdestinations 2>&1 | \
		grep "platform:iOS," | grep -v Simulator | grep -v placeholder | \
		head -1 | sed 's/.*id:\([^,}]*\).*/\1/'); \
	if [ -z "$$DEVICE_ID" ]; then \
		echo "ERROR: No physical iOS device found. Connect via USB and trust the computer."; \
		exit 1; \
	fi; \
	DEVICE_NAME=$$(xcodebuild -project $(IOS_PROJECT) -scheme $(IOS_SCHEME) -showdestinations 2>&1 | \
		grep "platform:iOS," | grep -v Simulator | grep -v placeholder | \
		head -1 | sed 's/.*name:\([^}]*\).*/\1/' | xargs); \
	echo "==> Building for $$DEVICE_NAME ($$DEVICE_ID)..."; \
	xcodebuild -project $(IOS_PROJECT) \
		-scheme $(IOS_SCHEME) \
		-destination "id=$$DEVICE_ID" \
		-configuration Debug \
		build 2>&1 | tail -1; \
	APP_PATH="$$(xcodebuild -project $(IOS_PROJECT) -scheme $(IOS_SCHEME) -configuration Debug -showBuildSettings 2>/dev/null | grep ' CONFIGURATION_BUILD_DIR' | grep -v EXCLUDED | head -1 | awk '{print $$3}')/$(IOS_SCHEME).app"; \
	echo "==> Installing via ios-deploy..."; \
	ios-deploy --bundle "$$APP_PATH" --no-wifi --nostart; \
	echo "==> Launching..."; \
	xcrun devicectl device process launch --device "$$DEVICE_ID" com.igorganapolsky.randomtimer 2>&1 | tail -1 && \
	echo "✅ App running on $$DEVICE_NAME" || \
	echo "❌ Launch failed. Check device connection."

# Run on iOS Simulator
run-ios-sim:
	@SIM=$$(xcrun simctl list devices available | grep "iPhone" | grep -v unavailable | head -1 | sed 's/.*(\(.*\)) .*/\1/'); \
	if [ -z "$$SIM" ]; then \
		echo "ERROR: No iOS simulators available."; \
		exit 1; \
	fi; \
	SIM_NAME=$$(xcrun simctl list devices available | grep "iPhone" | grep -v unavailable | head -1 | sed 's/ (.*//' | xargs); \
	echo "==> Booting simulator: $$SIM_NAME ($$SIM)"; \
	xcrun simctl boot $$SIM 2>/dev/null || true; \
	open -a Simulator; \
	echo "==> Building for simulator..."; \
	xcodebuild -project $(IOS_PROJECT) \
		-scheme $(IOS_SCHEME) \
		-destination "id=$$SIM" \
		-configuration Debug \
		build 2>&1 | tail -5; \
	echo "==> Installing and launching on simulator..."; \
	xcrun simctl install $$SIM build/Debug-iphonesimulator/$(IOS_SCHEME).app; \
	xcrun simctl launch $$SIM com.igorganapolsky.randomtimer

# Fix iOS device install hanging (CoreDevice sandbox exhaustion bug)
fix-ios-device:
	@echo "==> Killing stale CoreDevice services..."
	@sudo killall -9 CoreDeviceService 2>/dev/null || true
	@sudo killall -9 remotepairingd 2>/dev/null || true
	@echo "==> Restarting usbmuxd..."
	@sudo killall -9 usbmuxd 2>/dev/null || true
	@sleep 2
	@echo "==> Verifying device connection..."
	@xcrun devicectl list devices 2>/dev/null || echo "No devices found — reconnect USB cable"
	@echo "==> Done. Try 'make run-ios-device' again. If still hanging, reboot your Mac."

# Install git hooks
install-hooks:
	@cp scripts/pre-commit .git/hooks/pre-commit
	@chmod +x .git/hooks/pre-commit
	@echo "✅ Pre-commit hook installed"

# Verify (unit tests + builds)
verify: verify-android verify-ios

verify-android:
	@echo "==> Android: unit tests + debug build"
	@cd $(ANDROID_DIR) && ./gradlew testDebugUnitTest assembleDebug --no-daemon

verify-android-instrumentation:
	@echo "==> Android: instrumentation tests (requires emulator/device)"
	@cd $(ANDROID_DIR) && ./gradlew connectedDebugAndroidTest --no-daemon

verify-ios:
	@echo "==> iOS: unit tests (simulator)"
	@./scripts/ios_verify.sh

verify-ios-ui:
	@echo "==> iOS: UI tests (simulator)"
	@./scripts/ios_verify.sh --ui

maestro-android:
	@echo "==> Maestro: Android flows (requires emulator/device + maestro CLI)"
	@maestro test .maestro/smoke-test.yaml

maestro-ios:
	@echo "==> Maestro: iOS flows (requires simulator + maestro CLI)"
	@maestro test .maestro/ios-smoke-test.yaml
