# Skill: Setup Android

Automatically fix Android development environment issues, including network security config, Metro bundler connection, and build problems.

## Trigger

User invokes `/setup-android` or mentions Android connection/build issues.

## Workflow

Execute these steps autonomously:

### 1. Check Network Security Config

```bash
# Check if network_security_config.xml exists
ls android/app/src/main/res/xml/network_security_config.xml
```

If missing, create it:

```xml
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <domain-config cleartextTrafficPermitted="true">
        <domain includeSubdomains="true">localhost</domain>
        <domain includeSubdomains="true">10.0.2.2</domain>
        <domain includeSubdomains="true">10.0.3.2</domain>
    </domain-config>
    <debug-overrides>
        <trust-anchors>
            <certificates src="user"/>
            <certificates src="system"/>
        </trust-anchors>
    </debug-overrides>
    <base-config cleartextTrafficPermitted="true">
        <trust-anchors>
            <certificates src="system"/>
        </trust-anchors>
    </base-config>
</network-security-config>
```

### 2. Verify AndroidManifest.xml

Check that `android:networkSecurityConfig="@xml/network_security_config"` is in the `<application>` tag of `android/app/src/main/AndroidManifest.xml`. Add if missing.

### 3. Setup ADB Port Forwarding

```bash
adb reverse tcp:8081 tcp:8081
```

### 4. Check Device Connection

```bash
adb devices
```

Report if device shows as `unauthorized` and instruct user to allow USB debugging.

### 5. Clean and Rebuild (if requested or build errors exist)

```bash
cd android && ./gradlew clean && cd ..
npm run android
```

## Success Criteria

- `network_security_config.xml` exists and is properly linked
- ADB shows connected device
- Metro bundler can connect to device

## Output

Report what was fixed and current status. If issues persist, provide manual troubleshooting steps.
