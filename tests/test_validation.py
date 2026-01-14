"""Tests for response validation."""

import pytest
import json
from src.runtime.agents.validation import ResponseValidator


class TestResponseValidator:
    """Test response validation."""

    def test_validate_response_with_all_required_fields(self):
        """Test validation passes when all required fields are present."""
        schema = json.dumps({
            "status": "string - success or failure",
            "message": "string - result message"
        })

        response = {
            "status": "success",
            "message": "Task completed"
        }

        is_valid, errors = ResponseValidator.validate_response(response, schema)
        assert is_valid
        assert len(errors) == 0

    def test_validate_response_with_missing_required_field(self):
        """Test validation fails when required field is missing."""
        schema = json.dumps({
            "status": "string - success or failure",
            "message": "string - result message"
        })

        response = {
            "status": "success"
            # Missing 'message' field
        }

        is_valid, errors = ResponseValidator.validate_response(response, schema)
        assert not is_valid
        assert len(errors) == 1
        assert "message" in errors[0]

    def test_validate_response_with_optional_fields(self):
        """Test validation passes when optional fields are missing."""
        schema = json.dumps({
            "status": "string - success or failure",
            "details": "optional string - additional details"
        })

        response = {
            "status": "success"
            # 'details' is optional, so it's okay to omit
        }

        is_valid, errors = ResponseValidator.validate_response(response, schema)
        assert is_valid
        assert len(errors) == 0

    def test_validate_response_with_extra_fields(self):
        """Test validation warns but doesn't fail with extra fields."""
        schema = json.dumps({
            "status": "string - success or failure"
        })

        response = {
            "status": "success",
            "extra_field": "unexpected"
        }

        is_valid, errors = ResponseValidator.validate_response(response, schema)
        assert is_valid  # Extra fields don't cause validation failure
        assert len(errors) == 0

    def test_validate_response_with_invalid_schema(self):
        """Test validation passes when schema is invalid JSON."""
        schema = "not valid json {{"

        response = {
            "status": "success"
        }

        is_valid, errors = ResponseValidator.validate_response(response, schema)
        assert is_valid  # Skip validation if schema is invalid
        assert len(errors) == 0

    def test_validate_json_structure(self):
        """Test JSON structure validation."""
        # Valid JSON structures
        valid_data = [
            {"key": "value"},
            ["item1", "item2"],
            "string",
            123,
            None
        ]

        for data in valid_data:
            is_valid, error = ResponseValidator.validate_json_structure(data)
            assert is_valid, f"Should be valid: {data}"
            assert error is None

        # Invalid JSON structure (function, which can't be serialized)
        def test_func():
            pass

        is_valid, error = ResponseValidator.validate_json_structure(test_func)
        assert not is_valid
        assert error is not None

    def test_extract_required_fields(self):
        """Test extraction of required fields from schema."""
        schema = json.dumps({
            "status": "string - required field",
            "message": "string - required message",
            "details": "optional string - extra info",
            "debug": "optional object - debug data"
        })

        required = ResponseValidator.extract_required_fields(schema)

        assert "status" in required
        assert "message" in required
        assert "details" not in required
        assert "debug" not in required

    def test_sanitize_response(self):
        """Test response sanitization."""
        # Response with non-serializable values
        def test_func():
            pass

        response = {
            "status": "success",
            "function": test_func,  # Not serializable
            "nested": {
                "value": 123,
                "func": test_func
            },
            "list": [1, 2, test_func]
        }

        sanitized = ResponseValidator.sanitize_response(response)

        # Check that non-serializable values are converted to strings
        assert sanitized["status"] == "success"
        assert isinstance(sanitized["function"], str)
        assert sanitized["nested"]["value"] == 123
        assert isinstance(sanitized["nested"]["func"], str)
        assert sanitized["list"][0] == 1
        assert isinstance(sanitized["list"][2], str)

    def test_sanitize_response_preserves_valid_types(self):
        """Test that sanitization preserves valid JSON types."""
        response = {
            "string": "test",
            "int": 123,
            "float": 45.67,
            "bool": True,
            "none": None,
            "list": [1, 2, 3],
            "dict": {"nested": "value"}
        }

        sanitized = ResponseValidator.sanitize_response(response)

        assert sanitized == response  # Should be unchanged


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
