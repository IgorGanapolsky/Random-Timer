.PHONY: run-android-device run-android-emulator run-ios-device run-ios-sim fix-ios-device install-hooks
.PHONY: verify verify-android verify-android-instrumentation verify-ios verify-ios-ui maestro-android maestro-ios
.PHONY: playwright-install playwright-install-agent-browser playwright-verify-local playwright-verify-strict playwright-store-console playwright-store-console-agent playwright-sync-auth-secrets
.PHONY: device-tests device-tests-adb phoneclaw-visual
.PHONY: memory-doctor memory-summary memory-lessons memory-capture-down memory-capture-up
.PHONY: molmoweb-proof-example molmoweb-proof-homepage

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
	@SIM=$$(xcrun simctl list devices available | grep "iPhone" | grep -v unavailable | head -1 | awk -F '[()]' '{print $$2}'); \
	if [ -z "$$SIM" ]; then \
		echo "ERROR: No iOS simulators available."; \
		exit 1; \
	fi; \
	SIM_NAME=$$(xcrun simctl list devices available | grep "iPhone" | grep -v unavailable | head -1 | sed 's/ (.*//' | xargs); \
	echo "==> Booting simulator: $$SIM_NAME ($$SIM)"; \
	xcrun simctl boot $$SIM 2>/dev/null || true; \
	open -a Simulator; \
	echo "==> Building for simulator..."; \
	set -e; set -o pipefail; \
	xcodebuild -project $(IOS_PROJECT) \
		-scheme $(IOS_SCHEME) \
		-destination "id=$$SIM" \
		-configuration Debug \
		build \
		CODE_SIGNING_ALLOWED=NO \
		2>&1 | tail -5; \
	APP_PATH="$$(xcodebuild -project $(IOS_PROJECT) -scheme $(IOS_SCHEME) -destination "id=$$SIM" -configuration Debug -showBuildSettings 2>/dev/null | grep ' CONFIGURATION_BUILD_DIR' | grep -v EXCLUDED | head -1 | awk '{print $$3}')/$(IOS_SCHEME).app"; \
	echo "==> Installing and launching on simulator..."; \
	xcrun simctl install $$SIM "$$APP_PATH"; \
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

playwright-install:
	@echo "==> Playwright: install dependencies + chromium"
	@cd tests/playwright && npm ci && npm run install:browsers

playwright-install-agent-browser:
	@echo "==> Installing agent-browser CLI globally"
	@npm install -g agent-browser@0.10.0

playwright-verify-local:
	@echo "==> Playwright: quality gate + local deterministic checks"
	@cd tests/playwright && npm ci && npm run verify

playwright-verify-strict:
	@echo "==> Playwright: strict store-readiness gate"
	@cd tests/playwright && npm ci && npm run verify:strict

playwright-store-console:
	@echo "==> Playwright: read-only authenticated store-console checks"
	@cd tests/playwright && npm ci && npm run test:console

playwright-store-console-agent:
	@echo "==> agent-browser: read-only authenticated store-console checks"
	@cd tests/playwright && npm ci && npm run test:console:agent-browser

playwright-sync-auth-secrets:
	@echo "==> Playwright: sync .auth storage states to GitHub Actions secrets"
	@cd tests/playwright && npm ci && npm run auth:sync-secrets

# Device tests (requires connected Android device/emulator)
device-tests:
	@bash scripts/device-tests/run-all.sh

device-tests-adb:
	@bash scripts/device-tests/run-all.sh --adb-only

phoneclaw-visual:
	@echo "==> PhoneClaw: pushing visual test scripts to device"
	@bash scripts/device-tests/phoneclaw/setup-device.sh

memory-doctor:
	@bash scripts/verify_memory_gateway.sh

memory-summary:
	@echo "==> Memory Gateway: feedback summary"
	@npx -y mcp-memory-gateway@0.8.0 summary

memory-lessons:
	@echo "==> Memory Gateway: lesson search"
	@npx -y mcp-memory-gateway@0.8.0 lessons --query="$(Q)" --limit="$${LIMIT:-5}"

memory-capture-down:
	@test -n "$(CONTEXT)" || (echo "ERROR: provide CONTEXT=\"...\"" && exit 1)
	@echo "==> Memory Gateway: capture negative feedback"
	@npx -y mcp-memory-gateway@0.8.0 capture --feedback=down --context="$(CONTEXT)" --tags="$(TAGS)"

memory-capture-up:
	@test -n "$(CONTEXT)" || (echo "ERROR: provide CONTEXT=\"...\"" && exit 1)
	@echo "==> Memory Gateway: capture positive feedback"
	@npx -y mcp-memory-gateway@0.8.0 capture --feedback=up --context="$(CONTEXT)" --tags="$(TAGS)"

# Forge & Maintenance
forge-maintenance:
	@bash scripts/maintenance_loop.sh

self-heal:
	@python3 scripts/release_self_healer.py

# Internal distribution (Firebase + TestFlight)
distribute:
	@gh workflow run internal-distribution.yml --ref develop

# iOS Logic Verification (Sub-target for maintenance)
verify-ios-logic:
	xcodebuild -project native-ios/RandomTimer.xcodeproj -scheme RandomTimer -destination "platform=iOS Simulator,name=iPhone 16 Pro Max" test -only-testing:RandomTimerTests/TimerConfigTests

# MolmoWeb browser verification shortcuts (contracts in scripts/tests/test_molmoweb_contracts.py)
molmoweb-proof-example:
	@python3 scripts/molmoweb_browser_verify.py --help

molmoweb-proof-homepage:
	@python3 scripts/molmoweb_browser_verify.py --help
