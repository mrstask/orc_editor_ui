class ORCEditorError(Exception):
    """Base exception for ORC Editor"""
    pass

class ORCLoadError(ORCEditorError):
    """Raised when loading an ORC file fails"""
    pass

class ORCSaveError(ORCEditorError):
    """Raised when saving an ORC file fails"""
    pass

class SchemaValidationError(ORCEditorError):
    """Raised when schema validation fails"""
    pass
