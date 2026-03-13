import os
import re

project_path = "native-ios/RandomTimer.xcodeproj/project.pbxproj"

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

# Map filenames to UUIDs (deterministic)
file_uuids = {}
build_uuids = {}
for f in files:
    h = hash(f) & 0xFFFFFFFFFFFF
    file_uuids[f] = f"DB1EBA{h:012X}"[:24]
    bh = hash(f + "_build") & 0xFFFFFFFFFFFF
    build_uuids[f] = f"DB1EBB{bh:012X}"[:24]

# 1. PBXFileReference
new_refs = ""
for f, u in file_uuids.items():
    if u not in content:
        new_refs += f'\t\t{u} /* {f} */ = {{isa = PBXFileReference; lastKnownFileType = audio.mp3; path = {f}; sourceTree = "<group>"; }};\n'
if new_refs:
    content = content.replace('/* Begin PBXFileReference section */\n', '/* Begin PBXFileReference section */\n' + new_refs)

# 2. PBXBuildFile
new_build_files = ""
for f, bu in build_uuids.items():
    if bu not in content:
        u = file_uuids[f]
        new_build_files += f'\t\t{bu} /* {f} in Resources */ = {{isa = PBXBuildFile; fileRef = {u} /* {f} */; }};\n'
if new_build_files:
    content = content.replace('/* Begin PBXBuildFile section */\n', '/* Begin PBXBuildFile section */\n' + new_build_files)

# 3. Sounds PBXGroup children
# Find the line: DB1EB0493351D1D4C087065E /* Sounds */ = {
# Then find the children = ( line after it.
group_start = content.find('DB1EB0493351D1D4C087065E /* Sounds */ = {')
if group_start != -1:
    children_line = content.find('children = (', group_start)
    if children_line != -1:
        insertion_point = content.find('\n', children_line) + 1
        new_children = ""
        for f, u in file_uuids.items():
            if u not in content: # This check is weak because u might be in PBXFileReference
                pass
            # Better check if the UUID is already in the children list of THIS group
            group_end = content.find(');', insertion_point)
            if u not in content[insertion_point:group_end]:
                new_children += f'\t\t\t\t{u} /* {f} */,\n'
        if new_children:
            content = content[:insertion_point] + new_children + content[insertion_point:]

# 4. Resources PBXResourcesBuildPhase files
# Find the line: C860582E5E34407E753D7F99 /* Resources */ = {
# Then find the files = ( line after it.
phase_start = content.find('C860582E5E34407E753D7F99 /* Resources */ = {')
if phase_start != -1:
    files_line = content.find('files = (', phase_start)
    if files_line != -1:
        insertion_point = content.find('\n', files_line) + 1
        new_resource_entries = ""
        for f, bu in build_uuids.items():
            phase_end = content.find(');', insertion_point)
            if bu not in content[insertion_point:phase_end]:
                new_resource_entries += f'\t\t\t\t{bu} /* {f} in Resources */,\n'
        if new_resource_entries:
            content = content[:insertion_point] + new_resource_entries + content[insertion_point:]

with open(project_path, 'w') as f:
    f.write(content)

print("Successfully updated project.pbxproj with audio assets")
