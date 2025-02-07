from typing import Dict, List, Union, Optional

import pyarrow


class SchemaValidator:
    @staticmethod
    def compare_schemas(original_schema: pyarrow.Schema, saved_schema: pyarrow.Schema) -> List[str]:
        """Compare two schemas and return a list of differences.

        Args:
            original_schema: The original PyArrow schema
            saved_schema: The schema to compare against

        Returns:
            List of string descriptions of differences found
        """
        differences = []
        orig_dict = SchemaValidator._schema_to_dict(original_schema)
        saved_dict = SchemaValidator._schema_to_dict(saved_schema)

        # Compare fields and types
        differences.extend(SchemaValidator._compare_fields(orig_dict, saved_dict))
        return differences

    @staticmethod
    def _schema_to_dict(schema: pyarrow.Schema) -> Dict[str, Dict[str, Union[str, Dict]]]:
        """Convert a PyArrow schema to a dictionary representation.

        Args:
            schema: PyArrow schema to convert

        Returns:
            Dictionary representation of the schema
        """
        result = {}
        for field in schema:
            result[field.name] = SchemaValidator._get_field_type(field)
        return result

    @staticmethod
    def _get_field_type(field: pyarrow.Field) -> Dict[str, Union[str, Dict]]:
        """Get the type information for a field.

        Args:
            field: PyArrow field to analyze

        Returns:
            Dictionary containing type information
        """
        type_info = {'type': str(field.type)}

        # Handle list types
        if isinstance(field.type, pyarrow.ListType):
            list_type = field.type
            if isinstance(list_type.value_type, pyarrow.StructType):
                struct_fields = {}
                for struct_field in list_type.value_type:
                    struct_fields[struct_field.name] = str(struct_field.type)
                type_info = {
                    'type': 'list<struct>',
                    'struct_fields': struct_fields
                }
            else:
                type_info['type'] = f'list<{str(list_type.value_type)}>'

        # Handle struct types
        elif isinstance(field.type, pyarrow.StructType):
            struct_fields = {}
            for struct_field in field.type:
                struct_fields[struct_field.name] = str(struct_field.type)
            type_info['struct_fields'] = struct_fields

        return type_info

    @staticmethod
    def _compare_fields(original_dict: Dict, saved_dict: Dict) -> List[str]:
        """Compare two schema dictionaries and return differences.

        Args:
            original_dict: Dictionary representation of original schema
            saved_dict: Dictionary representation of schema to compare against

        Returns:
            List of string descriptions of differences found
        """
        differences = []

        # Check for missing or different fields in saved schema
        for field_name, original_type in original_dict.items():
            if field_name not in saved_dict:
                differences.append(f"Missing field in saved schema: {field_name}")
            elif saved_dict[field_name] != original_type:
                # Get detailed type information for better error messages
                orig_type_str = SchemaValidator._format_type_info(original_type)
                saved_type_str = SchemaValidator._format_type_info(saved_dict[field_name])
                differences.append(
                    f"Type mismatch for {field_name}:\n"
                    f"  Original: {orig_type_str}\n"
                    f"  Saved: {saved_type_str}"
                )

        # Check for extra fields in saved schema
        for field_name in saved_dict:
            if field_name not in original_dict:
                differences.append(f"Extra field in saved schema: {field_name}")

        return differences

    @staticmethod
    def _format_type_info(type_info: Dict[str, Union[str, Dict]]) -> str:
        """Format type information into a readable string.

        Args:
            type_info: Dictionary containing type information

        Returns:
            Formatted string representation of the type
        """
        if isinstance(type_info, str):
            return type_info

        base_type = type_info['type']
        if 'struct_fields' in type_info:
            struct_fields = [f"{name}: {type_}"
                             for name, type_ in type_info['struct_fields'].items()]
            return f"{base_type}{{{', '.join(struct_fields)}}}"
        return base_type

    @staticmethod
    def validate_schema_compatibility(original_schema: pyarrow.Schema,
                                      new_schema: pyarrow.Schema) -> Optional[List[str]]:
        """Validate if a new schema is compatible with the original schema.

        Args:
            original_schema: The original PyArrow schema
            new_schema: The new schema to validate

        Returns:
            None if schemas are compatible, otherwise list of incompatibilities
        """
        differences = SchemaValidator.compare_schemas(original_schema, new_schema)
        return None if not differences else differences
