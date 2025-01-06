#!/bin/bash

# Create a temporary directory for DMG contents
TEMP_DMG="temp_dmg"
rm -rf "$TEMP_DMG"
mkdir "$TEMP_DMG"

# Copy the app directory to the temporary directory
cp -r "dist/ORC Editor" "$TEMP_DMG/ORC Editor.app"

# Create a symbolic link to Applications folder
ln -s /Applications "$TEMP_DMG/Applications"

# Create the DMG
hdiutil create -volname "ORC Editor" -srcfolder "$TEMP_DMG" -ov -format UDZO "dist/ORC_Editor.dmg"

# Clean up
rm -rf "$TEMP_DMG"
