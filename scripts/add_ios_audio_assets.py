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

def _section_index(marker: str) -> int:
    index = content.find(marker)
    if index == -1:
        print(f"Could not find marker: {marker}")
        exit(1)
    return index


def _group_children_insertion_point(group_name: str) -> int:
    group_marker = f"/* {group_name} */ = {{"
    group_index = _section_index(group_marker)
    children_marker = "children = ("
    children_index = content.find(children_marker, group_index)
    if children_index == -1:
        print(f"Could not find children list for group: {group_name}")
        exit(1)
    return children_index + len(children_marker)


def _resources_files_insertion_point() -> int:
    resources_marker = "/* Resources */ = {"
    resources_index = _section_index(resources_marker)
    files_marker = "files = ("
    files_index = content.find(files_marker, resources_index)
    if files_index == -1:
        print("Could not find PBXResourcesBuildPhase files list")
        exit(1)
    return files_index + len(files_marker)

# 1. Create PBXFileReference for each file
# Find the start of the PBXFileReference section
_section_index('/* Begin PBXFileReference section */')

# Map filenames to UUIDs (using deterministic ones based on filename for idempotency)
file_uuids = {}
for index, f in enumerate(files, start=1):
    file_uuids[f] = f"DB1EBA{index:018X}"[:24]

new_file_refs = ""
for f, u in file_uuids.items():
    if u not in content:
        new_file_refs += f'\t\t{u} /* {f} */ = {{isa = PBXFileReference; lastKnownFileType = audio.mp3; path = {f}; sourceTree = "<group>"; }};\n'

if new_file_refs:
    content = content.replace('/* Begin PBXFileReference section */', '/* Begin PBXFileReference section */\n' + new_file_refs)

# 2. Add to "Sounds" PBXGroup
new_children = ""
for f, u in file_uuids.items():
    if u not in content:
        new_children += f'\t\t\t\t{u} /* {f} */,\n'

if new_children:
    insertion_point = _group_children_insertion_point("Sounds")
    content = content[:insertion_point] + '\n' + new_children + content[insertion_point:]

# 3. Add to PBXResourcesBuildPhase
# We also need PBXBuildFile entries for each file reference
_section_index('/* Begin PBXBuildFile section */')

build_uuids = {}
new_build_files = ""
for index, (f, u) in enumerate(file_uuids.items(), start=1):
    # Another set of UUIDs for the build files
    bu = f"DB1EBB{index:018X}"[:24]
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
    insertion_point = _resources_files_insertion_point()
    content = content[:insertion_point] + '\n' + new_resource_entries + content[insertion_point:]

with open(project_path, 'w') as f:
    f.write(content)

print("Successfully updated project.pbxproj with audio assets")
