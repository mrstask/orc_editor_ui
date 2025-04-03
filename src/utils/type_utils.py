"""Utilities for working with data types and conversions."""


def get_pyarrow_type(data_type):
    """Convert selected data type to PyArrow type for schema compatibility.

    Args:
        data_type: String representation of data type

    Returns:
        PyArrow data type object
    """
    import pyarrow as pa

    type_mapping = {
        "String": pa.string(),
        "Integer": pa.int64(),
        "Float": pa.float64(),
        "Boolean": pa.bool_(),
        "List<String>": pa.list_(pa.string()),
        "List<Integer>": pa.list_(pa.int64()),
        "List<Float>": pa.list_(pa.float64()),
        "List<Boolean>": pa.list_(pa.bool_())
    }

    return type_mapping.get(data_type, pa.string())
