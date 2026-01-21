"""
Unit tests for validation module.

Tests the ResponseValidator class for validating agent responses.
"""

import pytest
import json


class TestResponseValidator:
    """Test ResponseValidator class."""

    def test_validate_response_valid(self):
        """Test validating a valid response."""
        from src.runtime.agents.validation import ResponseValidator

        schema = '{"status": "The status", "result": "The result"}'
        response = {"status": "completed", "result": "success"}

        is_valid, errors = ResponseValidator.validate_response(response, schema)

        assert is_valid is True
        assert errors == []

    def test_validate_response_missing_field(self):
        """Test validating response with missing required field."""
        from src.runtime.agents.validation import ResponseValidator

        schema = '{"status": "The status", "result": "The result"}'
        response = {"status": "completed"}

        is_valid, errors = ResponseValidator.validate_response(response, schema)

        assert is_valid is False
        assert len(errors) == 1
        assert "result" in errors[0]

    def test_validate_response_optional_field(self):
        """Test validating response with optional field missing."""
        from src.runtime.agents.validation import ResponseValidator

        schema = '{"status": "The status", "notes": "(optional) Notes"}'
        response = {"status": "completed"}

        is_valid, errors = ResponseValidator.validate_response(response, schema)

        assert is_valid is True
        assert errors == []

    def test_validate_response_invalid_schema(self):
        """Test validating with invalid JSON schema."""
        from src.runtime.agents.validation import ResponseValidator

        schema = 'not valid json'
        response = {"status": "completed"}

        is_valid, errors = ResponseValidator.validate_response(response, schema)

        # Invalid schema should pass (skip validation)
        assert is_valid is True
        assert errors == []

    def test_validate_response_with_extra_fields(self):
        """Test that extra fields don't cause validation failure."""
        from src.runtime.agents.validation import ResponseValidator

        schema = '{"status": "The status"}'
        response = {"status": "completed", "extra_field": "value"}

        is_valid, errors = ResponseValidator.validate_response(response, schema)

        assert is_valid is True
        assert errors == []

    def test_validate_response_multiple_missing(self):
        """Test validating response with multiple missing fields."""
        from src.runtime.agents.validation import ResponseValidator

        schema = '{"field1": "Required", "field2": "Required", "field3": "Required"}'
        response = {}

        is_valid, errors = ResponseValidator.validate_response(response, schema)

        assert is_valid is False
        assert len(errors) == 3

    def test_validate_response_non_string_description(self):
        """Test validation with non-string description in schema."""
        from src.runtime.agents.validation import ResponseValidator

        # Schema with non-string value (nested object)
        schema = '{"status": "The status", "nested": {"type": "object"}}'
        response = {"status": "completed"}

        is_valid, errors = ResponseValidator.validate_response(response, schema)

        # nested has non-string description so it's skipped
        assert is_valid is True


class TestValidateJsonStructure:
    """Test validate_json_structure method."""

    def test_valid_dict(self):
        """Test validating valid dict structure."""
        from src.runtime.agents.validation import ResponseValidator

        data = {"key": "value", "number": 123}

        is_valid, error = ResponseValidator.validate_json_structure(data)

        assert is_valid is True
        assert error is None

    def test_valid_list(self):
        """Test validating valid list structure."""
        from src.runtime.agents.validation import ResponseValidator

        data = [1, 2, 3, "string"]

        is_valid, error = ResponseValidator.validate_json_structure(data)

        assert is_valid is True
        assert error is None

    def test_valid_nested(self):
        """Test validating nested structure."""
        from src.runtime.agents.validation import ResponseValidator

        data = {
            "list": [1, 2, 3],
            "nested": {"key": "value"},
            "mixed": [{"a": 1}, {"b": 2}]
        }

        is_valid, error = ResponseValidator.validate_json_structure(data)

        assert is_valid is True
        assert error is None

    def test_invalid_non_serializable(self):
        """Test validating non-serializable object."""
        from src.runtime.agents.validation import ResponseValidator

        class NonSerializable:
            pass

        data = {"obj": NonSerializable()}

        is_valid, error = ResponseValidator.validate_json_structure(data)

        assert is_valid is False
        assert error is not None

    def test_primitives(self):
        """Test validating primitive types."""
        from src.runtime.agents.validation import ResponseValidator

        assert ResponseValidator.validate_json_structure("string") == (True, None)
        assert ResponseValidator.validate_json_structure(123) == (True, None)
        assert ResponseValidator.validate_json_structure(12.5) == (True, None)
        assert ResponseValidator.validate_json_structure(True) == (True, None)
        assert ResponseValidator.validate_json_structure(None) == (True, None)


class TestExtractRequiredFields:
    """Test extract_required_fields method."""

    def test_extract_required_fields(self):
        """Test extracting required fields from schema."""
        from src.runtime.agents.validation import ResponseValidator

        schema = '{"field1": "Required", "field2": "Also required", "optional": "(optional)"}'

        required = ResponseValidator.extract_required_fields(schema)

        assert "field1" in required
        assert "field2" in required
        assert "optional" not in required

    def test_extract_all_required(self):
        """Test extracting when all fields are required."""
        from src.runtime.agents.validation import ResponseValidator

        schema = '{"a": "Required", "b": "Also required"}'

        required = ResponseValidator.extract_required_fields(schema)

        assert required == {"a", "b"}

    def test_extract_all_optional(self):
        """Test extracting when all fields are optional."""
        from src.runtime.agents.validation import ResponseValidator

        schema = '{"a": "(optional)", "b": "(OPTIONAL) Some field"}'

        required = ResponseValidator.extract_required_fields(schema)

        assert required == set()

    def test_extract_invalid_json(self):
        """Test extracting from invalid JSON returns empty set."""
        from src.runtime.agents.validation import ResponseValidator

        schema = 'not valid json'

        required = ResponseValidator.extract_required_fields(schema)

        assert required == set()

    def test_extract_non_string_values(self):
        """Test extracting with non-string field values."""
        from src.runtime.agents.validation import ResponseValidator

        schema = '{"string_field": "Required", "nested": {"type": "object"}}'

        required = ResponseValidator.extract_required_fields(schema)

        # Only string_field should be in required (nested has non-string value)
        assert "string_field" in required
        assert "nested" not in required


class TestSanitizeResponse:
    """Test sanitize_response method."""

    def test_sanitize_primitives(self):
        """Test sanitizing primitives."""
        from src.runtime.agents.validation import ResponseValidator

        data = {
            "string": "value",
            "number": 123,
            "float": 12.5,
            "bool": True,
            "none": None
        }

        result = ResponseValidator.sanitize_response(data)

        assert result == data

    def test_sanitize_list(self):
        """Test sanitizing lists."""
        from src.runtime.agents.validation import ResponseValidator

        data = {"list": [1, 2, 3]}

        result = ResponseValidator.sanitize_response(data)

        assert result == data

    def test_sanitize_nested_dict(self):
        """Test sanitizing nested dicts."""
        from src.runtime.agents.validation import ResponseValidator

        data = {"outer": {"inner": {"deep": "value"}}}

        result = ResponseValidator.sanitize_response(data)

        assert result == data

    def test_sanitize_non_serializable(self):
        """Test sanitizing non-serializable objects."""
        from src.runtime.agents.validation import ResponseValidator

        class CustomObj:
            def __str__(self):
                return "CustomObj"

        data = {"obj": CustomObj()}

        result = ResponseValidator.sanitize_response(data)

        assert result["obj"] == "CustomObj"

    def test_sanitize_tuple(self):
        """Test sanitizing tuples (converted to lists)."""
        from src.runtime.agents.validation import ResponseValidator

        data = {"tuple": (1, 2, 3)}

        result = ResponseValidator.sanitize_response(data)

        assert result["tuple"] == [1, 2, 3]

    def test_sanitize_mixed(self):
        """Test sanitizing mixed content."""
        from src.runtime.agents.validation import ResponseValidator

        class CustomObj:
            def __str__(self):
                return "custom"

        data = {
            "list_with_obj": [1, CustomObj(), "str"],
            "nested": {"obj": CustomObj()}
        }

        result = ResponseValidator.sanitize_response(data)

        assert result["list_with_obj"] == [1, "custom", "str"]
        assert result["nested"]["obj"] == "custom"
