# Building for macOS

This document describes how to build the ORC Editor application for macOS and create a distributable DMG file.

## Prerequisites

- macOS 10.9 or later
- Python 3.11 or higher
- pip package manager
- Command line tools

## Setup Build Environment

1. Install command line tools if not already installed:
```bash
xcode-select --install
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
pip install pyinstaller
```

## Build Process

1. Create the spec file:
```bash
# Copy orc_editor.spec to your project directory
# Content of the spec file is provided in the repository
```

2. Clean previous builds:
```bash
rm -rf build dist
```

3. Build the application:
```bash
pyinstaller orc_editor.spec
```

After successful build, you'll find the application in `dist/ORC Editor/`.

## Creating DMG Installer

1. Create the DMG creation script:
```bash
# Copy create_dmg.sh to your project directory
# Make it executable
chmod +x create_dmg.sh
```

2. Run the DMG creation script:
```bash
./create_dmg.sh
```

The resulting DMG file will be created in the `dist` directory as `ORC_Editor.dmg`.

## Troubleshooting

### Common Issues

1. **Missing Modules**
   - Add any missing modules to the `hiddenimports` list in `orc_editor.spec`
   - Rebuild using PyInstaller

2. **Permission Issues**
   - Ensure all scripts have proper execution permissions
   - Run `chmod +x` on necessary files

3. **Build Failures**
   - Check Python version compatibility
   - Verify all dependencies are installed
   - Clean and rebuild

## Distribution

The built application can be distributed in two ways:

1. **Application Bundle**
   - Located in `dist/ORC Editor/`
   - Can be copied directly to Applications folder

2. **DMG Installer**
   - Located at `dist/ORC_Editor.dmg`
   - Provides standard macOS installation experience

## Notes

- The application is built for the architecture of the building machine
- For universal binary (Intel/Apple Silicon), additional configuration is required
- Code signing is not included in this basic build process
