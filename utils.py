import pandas as pd
import numpy as np
import json


def is_json(value):
    """Check if a value is a JSON string"""
    if not isinstance(value, str):
        return False
    try:
        json.loads(value)
        return True
    except (ValueError, TypeError):
        return False


def get_spark_type(pandas_dtype, sample_value=None):
    """Convert pandas dtype to PySpark data type string"""
    # Check for dictionary or JSON string first
    if isinstance(sample_value, dict):
        return 'StructType()'
    if isinstance(sample_value, str) and is_json(sample_value):
        return 'StructType()'

    # Handle arrays and lists
    if isinstance(sample_value, (list, np.ndarray)):
        if isinstance(sample_value, np.ndarray):
            if sample_value.size > 0:
                if sample_value.dtype.kind in ['U', 'S', 'O']:  # Unicode, String, or Object dtype
                    return "ArrayType(StringType())"
                element_type = sample_value.dtype
                return f"ArrayType(IntegerType())" if np.issubdtype(element_type,
                                                                    np.integer) else "ArrayType(DoubleType())"
            return "ArrayType(StringType())"  # Default to string array if empty
        elif isinstance(sample_value, list):
            if sample_value:
                first_elem = sample_value[0]
                if isinstance(first_elem, dict):
                    return "ArrayType(StructType())"
                elif isinstance(first_elem, str):
                    return "ArrayType(StringType())"
                elif isinstance(first_elem, int):
                    return "ArrayType(IntegerType())"
                elif isinstance(first_elem, float):
                    return "ArrayType(DoubleType())"
                else:
                    return "ArrayType(StringType())"  # Default to string for unknown types
            return "ArrayType(StringType())"  # Default to string array if empty

    # Handle scalar types
    dtype_str = str(pandas_dtype)
    if pd.api.types.is_integer_dtype(pandas_dtype):
        if dtype_str == 'int8':
            return 'ByteType()'
        elif dtype_str == 'int16':
            return 'ShortType()'
        elif dtype_str == 'int32':
            return 'IntegerType()'
        else:  # int64
            return 'LongType()'
    elif pd.api.types.is_float_dtype(pandas_dtype):
        if dtype_str == 'float32':
            return 'FloatType()'
        else:  # float64
            return 'DoubleType()'
    elif pd.api.types.is_bool_dtype(pandas_dtype):
        return 'BooleanType()'
    elif pd.api.types.is_datetime64_any_dtype(pandas_dtype):
        return 'TimestampType()'
    elif pd.api.types.is_string_dtype(pandas_dtype):
        return 'StringType()'
    else:
        return 'StringType()'  # Default to string for unknown types
