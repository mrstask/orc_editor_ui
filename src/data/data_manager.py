from dataclasses import dataclass
from typing import Dict, Any, List, Optional

import numpy as np
import pandas as pd
import pyarrow
import pyarrow.orc as orc

from src.exceptions.orc_exceptions import ORCSaveError, ORCLoadError


@dataclass
class ValidationResult:
    has_differences: bool
    differences: List[str]


class ORCDataManager:
    def __init__(self):
        self.df = None
        self.original_schema = None
        self.original_metadata = None

    def add_column(self, column_name: str, data_type: str, default_value: Any) -> None:
        """Add a new column to the DataFrame.

        Args:
            column_name: Name of the new column
            data_type: Data type of the new column
            default_value: Default value for the new column
        """
        if self.df is None:
            raise ValueError("No data loaded")

        # Check if column already exists
        if column_name in self.df.columns:
            raise ValueError(f"Column '{column_name}' already exists")

        # Add column with default value
        self.df[column_name] = default_value

        # Update schema if needed
        if self.original_schema is not None:
            import pyarrow as pa
            from src.utils.type_utils import get_pyarrow_type

            # Get PyArrow type for the new column
            pa_type = get_pyarrow_type(data_type)

            # Create new field
            new_field = pa.field(column_name, pa_type)

            # Create new schema with the additional field
            fields = list(self.original_schema)
            fields.append(new_field)

            # Update original schema
            self.original_schema = pa.schema(fields)

            # Update metadata if it exists
            if hasattr(self, 'original_metadata') and self.original_metadata:
                self.original_schema = self.original_schema.with_metadata(self.original_metadata)

    def load_file(self, filename: str) -> bool:
        """Load and parse an ORC file.

        Args:
            filename: Path to the ORC file to load

        Returns:
            bool: True if file was loaded successfully

        Raises:
            ORCLoadError: If there's an error loading or parsing the file
        """
        try:
            # Store filename
            self.current_file = filename

            # Open and read ORC file
            orc_file = orc.ORCFile(filename)
            table = orc_file.read()

            # Store schema information
            self.original_schema = table.schema
            self.original_metadata = table.schema.metadata if table.schema.metadata else {}

            # Convert to pandas DataFrame
            self.df = self._convert_to_pandas(table)

            return True

        except FileNotFoundError:
            raise ORCLoadError(f"File not found: {filename}")
        except PermissionError:
            raise ORCLoadError(f"Permission denied accessing file: {filename}")
        except pyarrow.lib.ArrowInvalid as e:
            raise ORCLoadError(f"Invalid ORC file format: {str(e)}")
        except Exception as e:
            raise ORCLoadError(f"Failed to load file: {str(e)}")

    def _convert_to_pandas(self, table: pyarrow.Table) -> pd.DataFrame:
        """Convert PyArrow table to pandas DataFrame with proper type conversions.

        Args:
            table: PyArrow table to convert

        Returns:
            pandas DataFrame with converted data
        """
        try:
            # First convert to pandas without type mapping
            df = table.to_pandas()

            # Apply type conversions for specific fields
            for field in table.schema:
                field_type = str(field.type)
                if field_type in ['timestamp[ms]', 'int64']:
                    if field.name in df.columns:
                        # Fill NaN values with -1 before converting to int64
                        df[field.name] = df[field.name].fillna(-1).astype('int64')

                elif field_type.startswith('list<'):
                    if field.name in df.columns:
                        # Ensure lists are properly converted from numpy arrays
                        df[field.name] = df[field.name].apply(
                            lambda x: x.tolist() if isinstance(x, np.ndarray) else x
                        )

                elif field_type.startswith('struct<'):
                    if field.name in df.columns:
                        # Ensure structs are properly converted to dictionaries
                        df[field.name] = df[field.name].apply(
                            lambda x: dict(x) if x is not None else None
                        )

            return df

        except Exception as e:
            raise ORCLoadError(f"Failed to convert data: {str(e)}")

    def _create_table(self) -> pyarrow.Table:
        """Create a PyArrow table from the current DataFrame using the original schema."""
        try:
            if hasattr(self, 'original_schema'):
                # Create table with original schema
                table = pyarrow.Table.from_pandas(
                    self.df,
                    schema=self.original_schema
                )
                # Set metadata if it exists
                if hasattr(self, 'original_metadata'):
                    table = table.replace_schema_metadata(self.original_metadata)
            else:
                # Infer schema from data if no original schema exists
                table = pyarrow.Table.from_pandas(self.df)

            return table
        except Exception as e:
            raise ORCSaveError(f"Failed to create table: {str(e)}")

    def _write_table(self, filename: str, table: pyarrow.Table) -> None:
        """Write the PyArrow table to an ORC file.

        Args:
            filename: Path to save the ORC file
            table: PyArrow table to write
        """
        try:
            with pyarrow.orc.ORCWriter(filename) as writer:
                writer.write(table)
        except Exception as e:
            raise ORCSaveError(f"Failed to write file: {str(e)}")

    def _validate_saved_file(self, filename: str) -> ValidationResult:
        """Validate the saved file by comparing schemas.

        Args:
            filename: Path to the saved file

        Returns:
            ValidationResult containing any schema differences
        """
        try:
            orc_file = orc.ORCFile(filename)
            saved_table = orc_file.read()
            saved_schema = saved_table.schema

            if hasattr(self, 'original_schema'):
                from src.utils.schema_validator import SchemaValidator
                differences = SchemaValidator.compare_schemas(
                    self.original_schema,
                    saved_schema
                )
                return ValidationResult(
                    has_differences=bool(differences),
                    differences=differences
                )
            return ValidationResult(has_differences=False, differences=[])

        except Exception as e:
            raise ORCSaveError(f"Failed to validate saved file: {str(e)}")

    def is_empty_column(self, column: str) -> bool:
        """Check if a column contains only empty lists/arrays or NaN values.

        Args:
            column: Name of the column to check

        Returns:
            True if the column is empty, False otherwise
        """
        if column not in self.df.columns:
            return True

        for value in self.df[column]:
            if isinstance(value, (np.ndarray, list)):
                if isinstance(value, np.ndarray) and value.size > 0:
                    return False
                if isinstance(value, list) and len(value) > 0:
                    return False
            elif not pd.isna(value):  # If it's not an empty list/array and not NaN
                return False
        return True

    def get_row_display_values(self, row_idx: int) -> Dict[str, str]:
        """Get the display values for a row.

        Args:
            row_idx: Index of the row

        Returns:
            Dictionary mapping column names to display values
        """
        if self.df is None or row_idx >= len(self.df):
            raise ValueError("Invalid row index")

        row = self.df.iloc[row_idx]
        display_values = {}

        for col in self.df.columns:
            value = row[col]
            if isinstance(value, (np.ndarray, list)):
                if isinstance(value, np.ndarray):
                    value = f"[{','.join(map(str, value))}]" if value.size > 0 else '[]'
                else:  # list
                    value = f"[{','.join(map(str, value))}]" if value else '[]'
            elif pd.api.types.is_integer_dtype(self.df[col].dtype):
                try:
                    value = 0 if pd.isna(value) else int(value)
                except (ValueError, TypeError):
                    value = 0
            display_values[col] = str(value)

        return display_values

    def update_row(self, row_idx: int, new_values: Dict[str, Any]) -> None:
        """Update a row with new values.

        Args:
            row_idx: Index of the row to update
            new_values: Dictionary mapping column names to new values
        """
        if self.df is None or row_idx >= len(self.df):
            raise ValueError("Invalid row index")

        try:
            # Create a Series with only the columns that exist in the DataFrame
            update_dict = {
                col: value for col, value in new_values.items()
                if col in self.df.columns
            }

            # Update the row using loc with a dictionary
            for col, value in update_dict.items():
                if isinstance(value, list):
                    # Handle lists (including lists of dictionaries)
                    if isinstance(self.df.loc[row_idx, col], np.ndarray):
                        # If the column is a numpy array, convert the list to a numpy array
                        value = np.array(value)
                    # Update the column with the new list or array
                    self.df.at[row_idx, col] = value
                else:
                    # Handle scalar values
                    self.df.at[row_idx, col] = value

        except Exception as e:
            print(f"Row update error details:")
            print(f"Row index: {row_idx}")
            print(f"New values: {new_values}")
            print(f"DataFrame columns: {self.df.columns.tolist()}")
            raise ValueError(f"Failed to update row: {str(e)}")

    def get_column_names(self) -> List[str]:
        """Get list of non-empty column names.

        Returns:
            List of column names excluding empty columns
        """
        if self.df is None:
            return []
        return [col for col in self.df.columns if not self.is_empty_column(col)]

    def get_value_type(self, column: str) -> Optional[type]:
        """Get the type of values in a column.

        Args:
            column: Name of the column

        Returns:
            Type of the column values or None if column doesn't exist
        """
        if self.df is None or column not in self.df.columns:
            return None

        series = self.df[column]
        if len(series) == 0:
            return None

        # Get first non-null value
        sample = series.dropna().iloc[0] if not series.isna().all() else None
        if sample is None:
            return None

        return type(sample)
