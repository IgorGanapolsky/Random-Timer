import os
import re
import uuid

project_path = "native-ios/RandomTimer.xcodeproj/project.pbxproj"
audio_dir = "native-ios/RandomTimer/Resources/Sounds"

files = [
    "cmd_drive_forward.mp3",
    "cmd_keep_pressure.mp3",
    "cmd_move_now.mp3",
    "cmd_push_pace.mp3",
    "cmd_push_through.mp3",
    "cmd_reset_breathe.mp3",
    "cmd_stay_sharp.mp3",
    "elapsed_120s.mp3",
    "elapsed_180s.mp3",
    "elapsed_300s.mp3",
    "elapsed_30s.mp3",
    "elapsed_600s.mp3",
    "elapsed_60s.mp3",
    "elapsed_90s.mp3",
    "preview_elapsed.mp3"
]

with open(project_path, 'r') as f:
    content = f.read()

# 1. Create PBXFileReference for each file
# Find the start of the PBXFileReference section
file_ref_section_match = re.search(r'/\* Begin PBXFileReference section \*/', content)
if not file_ref_section_match:
    print("Could not find PBXFileReference section")
    exit(1)

# Map filenames to UUIDs (using deterministic ones based on filename for idempotency)
file_uuids = {}
for f in files:
    # Use a consistent prefix but randomized enough to not collide
    # Xcode UUIDs are 24 chars.
    h = hash(f) & 0xFFFFFFFFFFFF
    u = f"DB1EBA{h:012X}"[:24]
    file_uuids[f] = u

new_file_refs = ""
for f, u in file_uuids.items():
    if u not in content:
        new_file_refs += f'\t\t{u} /* {f} */ = {{isa = PBXFileReference; lastKnownFileType = audio.mp3; path = {f}; sourceTree = "<group>"; }};\n'

if new_file_refs:
    content = content.replace('/* Begin PBXFileReference section */', '/* Begin PBXFileReference section */\n' + new_file_refs)

# 2. Add to "Sounds" PBXGroup
# Find the Sounds group
sounds_group_match = re.search(r'([0-9A-F]{24}) /\* Sounds \*/ = \{[^{]*isa = PBXGroup;[^{]*children = \(', content)
if not sounds_group_match:
    print("Could not find Sounds group")
    exit(1)

new_children = ""
for f, u in file_uuids.items():
    if u not in content:
        new_children += f'\t\t\t\t{u} /* {f} */,\n'

if new_children:
    insertion_point = sounds_group_match.end()
    content = content[:insertion_point] + '\n' + new_children + content[insertion_point:]

# 3. Add to PBXResourcesBuildPhase
# Find the main target's resources build phase
# Main target is RandomTimer
resources_phase_match = re.search(r'([0-9A-F]{24}) /\* Resources \*/ = \{[^{]*isa = PBXResourcesBuildPhase;[^{]*files = \(', content)
if not resources_phase_match:
    print("Could not find PBXResourcesBuildPhase section")
    exit(1)

# We also need PBXBuildFile entries for each file reference
build_file_section_match = re.search(r'/\* Begin PBXBuildFile section \*/', content)
if not build_file_section_match:
    print("Could not find PBXBuildFile section")
    exit(1)

build_uuids = {}
new_build_files = ""
for f, u in file_uuids.items():
    # Another set of UUIDs for the build files
    h = hash(f + "_build") & 0xFFFFFFFFFFFF
    bu = f"DB1EBB{h:012X}"[:24]
    build_uuids[f] = bu
    if bu not in content:
        new_build_files += f'\t\t{bu} /* {f} in Resources */ = {{isa = PBXBuildFile; fileRef = {u} /* {f} */; }};\n'

if new_build_files:
    content = content.replace('/* Begin PBXBuildFile section */', '/* Begin PBXBuildFile section */\n' + new_build_files)

# Now add build files to the resources phase
new_resource_entries = ""
for f, bu in build_uuids.items():
    if bu not in content:
        new_resource_entries += f'\t\t\t\t{bu} /* {f} in Resources */,\n'

if new_resource_entries:
    insertion_point = resources_phase_match.end()
    content = content[:insertion_point] + '\n' + new_resource_entries + content[insertion_point:]

with open(project_path, 'w') as f:
    f.write(content)

print("Successfully updated project.pbxproj with audio assets")
