# ORC Editor

A GUI application for viewing and editing ORC (Optimized Row Columnar) files. This tool provides a user-friendly interface for inspecting and modifying data stored in ORC format, with special handling for complex data types including arrays, structs, and nested structures.

## Features

- View and edit ORC files through a graphical interface
- Support for complex data types:
  - Arrays/Lists
  - Nested structures
  - JSON/Dictionary fields
- In-place editing of data
- Preserve schema and metadata during save operations
- Type-safe modifications with validation

## Requirements

- Python 3.11 or higher
- Required packages (installed automatically with pip):
  - pandas
  - numpy
  - pyarrow
  - tkinter (usually comes with Python)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/orc-editor.git
cd orc-editor
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the application:
```bash
python main.py
```

2. Use the GUI to:
   - Open ORC files using the "Open ORC" button
   - View and edit data in the table view
   - Save modifications using the "Save ORC" button

## Project Structure

```
orc_editor/
├── main.py              # Application entry point
├── orc_editor.py        # Main editor window implementation
├── edit_dialog.py       # Dialog for editing row values
├── list_edit_dialog.py  # Dialog for editing list/array values
└── utils.py            # Utility functions
```

## Development

To contribute to the project:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Building

See BUILD_MACOS.md for instructions on building the application for macOS.

## License

[Your chosen license]

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
