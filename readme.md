# ORC Editor

A Python-based GUI application for viewing and editing ORC files.

## Prerequisites

- Python 3.12+
- pip (Python package installer)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd orc-editor
```

2. Create and activate virtual environment:
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Unix/MacOS
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install pandas numpy pyarrow tkinter tzdata
```

4. Set timezone environment variable:
```python
import os
os.environ['PYTHONTZ'] = 'True'
```

## Running the Application

From the project root directory:
```bash
python main.py
```

## Building Executable

1. Install PyInstaller:
```bash
pip install pyinstaller
```

2. Build the executable:
```bash
pyinstaller orc_editor.spec
```

The executable will be created in `dist/ORC_Editor/`.

## Features

- Open and view ORC files
- Edit row data
- Toggle empty columns
- Save modified ORC files
- Support for complex data types (arrays, structs)

## Project Structure

```
orc_editor/
├── main.py              # Application entry point
├── src/
│   ├── components/     # UI components
│   ├── exceptions/     # Custom exceptions
│   ├── utils/         # Utility functions
│   └── __init__.py
└── orc_editor.spec    # PyInstaller specification
```

## Development Setup in PyCharm

1. Open project in PyCharm
2. Configure Python Interpreter:
   - Select virtual environment (.venv)
3. Set environment variables:
   - Open Run/Debug Configuration
   - Add Environment Variable: `PYTHONTZ=True`
4. Run main.py