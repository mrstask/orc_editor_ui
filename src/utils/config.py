class Config:
    DEFAULT_WINDOW_SIZE = "700x600"
    DEFAULT_PADDING = "10"
    FILE_TYPES = [
        ("ORC files", "*.orc"),
        ("All files", "*.*")
    ]
    DEFAULT_COLUMN_WIDTH = 100
    EMPTY_VALUE = -1

    # Type mappings
    TYPE_MAPPINGS = {
        'timestamp[ms]': 'int64',
        'int64': 'int64'
    }
