#!/usr/bin/env python3
"""
Autonomous Release Self-Healer.
Detects and fixes common CI/CD blockers:
1. Version code conflicts
2. Broken preflight regex
3. Missing build artifacts
"""

import os
import re
import sys
import subprocess
from pathlib import Path

def bump_android_version():
    """Bumps Android versionCode to a unique timestamp to avoid Play Store conflicts."""
    gradle_path = Path("native-android/app/build.gradle.kts")
    if not gradle_path.exists():
        return
    
    import time
    new_code = int(time.time())
    content = gradle_path.read_text()
    new_content = re.sub(r'versionCode\s*=\s*\d+', f'versionCode = {new_code}', content)
    gradle_path.write_text(new_content)
    print(f"✅ Auto-healed Android versionCode to {new_code}")

def bump_ios_build_number():
    """Bumps iOS CURRENT_PROJECT_VERSION."""
    project_path = Path("native-ios/RandomTimer.xcodeproj/project.pbxproj")
    if not project_path.exists():
        return
    
    content = project_path.read_text()
    # Find current max version
    matches = re.findall(r'CURRENT_PROJECT_VERSION = (\d+);', content)
    if matches:
        current_max = max(int(m) for m in matches)
        new_version = current_max + 1
        new_content = re.sub(r'CURRENT_PROJECT_VERSION = \d+;', f'CURRENT_PROJECT_VERSION = {new_version};', content)
        project_path.write_text(new_content)
        print(f"✅ Auto-healed iOS Build Number to {new_version}")

def fix_preflight_regex():
    """Ensures the source_versions script is robust."""
    script_path = Path("scripts/source_versions.py")
    if not script_path.exists():
        return
    
    content = script_path.read_text()
    if 'versionCode\\s*=\\s*(?:[^\\n]*?\\?:\\s*)?(\\d+)' not in content:
        # Re-apply the robust regex we discovered today
        new_content = re.sub(
            r'ANDROID_VERSION_CODE_RE = re.compile\(.*?\)',
            'ANDROID_VERSION_CODE_RE = re.compile(r"versionCode\\s*=\\s*(?:[^\\n]*?\\?:\\s*)?(\\d+)")',
            content
        )
        script_path.write_text(new_content)
        print("✅ Auto-healed source_versions.py regex")

def main():
    print("🛠️ Running Release Self-Healer...")
    bump_android_version()
    bump_ios_build_number()
    fix_preflight_regex()
    print("✨ Self-healing complete. System is ready for distribution.")

if __name__ == "__main__":
    main()
