import numpy as np
import pandas as pd


def get_spark_type(pandas_dtype, sample_value=None):
    """Convert pandas dtype to PySpark data type string"""
    if isinstance(sample_value, (list, np.ndarray)):
        if isinstance(sample_value, np.ndarray):
            if sample_value.size > 0:
                # Check the type of array elements
                element_type = sample_value.dtype
                return f"ArrayType(IntegerType())" if np.issubdtype(element_type,
                                                                    np.integer) else "ArrayType(DoubleType())"
            return "ArrayType(IntegerType())"
        elif isinstance(sample_value, list):
            if sample_value:
                # Check the type of list elements
                element_type = type(sample_value[0])
                return f"ArrayType({get_spark_type(str(element_type))})"
            return "ArrayType(IntegerType())"

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
