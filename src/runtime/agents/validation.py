"""Response validation utilities for agent runtime."""

import json
import logging
from typing import Dict, Any, List, Optional, Set

logger = logging.getLogger(__name__)


class ResponseValidator:
    """Validates agent responses against expected output schemas."""

    @staticmethod
    def validate_response(response_data: Dict[str, Any], expected_schema: str) -> tuple[bool, List[str]]:
        """
        Validate response data against expected schema.

        Args:
            response_data: Actual response from agent
            expected_schema: Expected output format as JSON string

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Parse expected schema
        try:
            schema = json.loads(expected_schema)
        except json.JSONDecodeError as e:
            logger.warning(f"Could not parse expected schema as JSON: {e}")
            # If schema isn't valid JSON, skip validation
            return True, []

        # Validate presence of required fields
        for field, description in schema.items():
            if isinstance(description, str):
                # Check if field is marked as optional
                is_optional = "optional" in description.lower()

                if not is_optional and field not in response_data:
                    errors.append(f"Missing required field: '{field}'")

        # Check for unexpected fields (warn but don't fail)
        expected_fields = set(schema.keys())
        actual_fields = set(response_data.keys())
        unexpected = actual_fields - expected_fields

        if unexpected:
            logger.debug(f"Response contains unexpected fields: {unexpected}")

        is_valid = len(errors) == 0
        return is_valid, errors

    @staticmethod
    def validate_json_structure(data: Any) -> tuple[bool, Optional[str]]:
        """
        Validate that data is valid JSON structure.

        Args:
            data: Data to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check if it's JSON-serializable
            json.dumps(data)
            return True, None
        except (TypeError, ValueError) as e:
            return False, str(e)

    @staticmethod
    def extract_required_fields(schema_str: str) -> Set[str]:
        """
        Extract list of required fields from schema string.

        Args:
            schema_str: Schema as JSON string

        Returns:
            Set of required field names
        """
        try:
            schema = json.loads(schema_str)
            required = set()

            for field, description in schema.items():
                if isinstance(description, str) and "optional" not in description.lower():
                    required.add(field)

            return required

        except json.JSONDecodeError:
            logger.warning("Could not parse schema to extract required fields")
            return set()

    @staticmethod
    def sanitize_response(response_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize response data by removing non-serializable values.

        Args:
            response_data: Response data to sanitize

        Returns:
            Sanitized response data
        """
        def _sanitize_value(value: Any) -> Any:
            """Recursively sanitize values."""
            if value is None or isinstance(value, (str, int, float, bool)):
                return value
            elif isinstance(value, (list, tuple)):
                return [_sanitize_value(v) for v in value]
            elif isinstance(value, dict):
                return {k: _sanitize_value(v) for k, v in value.items()}
            else:
                # Convert non-serializable to string
                return str(value)

        return _sanitize_value(response_data)
