import pytest
import time
from src.runtime.agents.name_generator import FamilyNameGenerator


class TestFamilyNameGenerator:
    """Test suite for FamilyNameGenerator following TDD RED phase."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.name_generator = FamilyNameGenerator()

    def test_name_generation_produces_string(self):
        """Test that name generation produces a string output."""
        # Arrange
        generator = self.name_generator
        
        # Act
        generated_name = generator.generate_name()
        
        # Assert
        assert isinstance(generated_name, str), f"Expected string, got {type(generated_name)}"
        assert len(generated_name) > 0, "Generated name should not be empty"

    def test_name_generation_uniqueness(self):
        """Test that name generation produces highly unique names."""
        # Arrange
        generator = self.name_generator
        num_names = 1000
        uniqueness_threshold = 0.95  # 95% uniqueness expected
        
        # Act
        generated_names = set()
        for _ in range(num_names):
            name = generator.generate_name()
            generated_names.add(name)
        
        # Assert
        uniqueness_ratio = len(generated_names) / num_names
        assert uniqueness_ratio >= uniqueness_threshold, (
            f"Expected uniqueness ratio >= {uniqueness_threshold}, "
            f"got {uniqueness_ratio} ({len(generated_names)} unique out of {num_names})"
        )

    def test_name_generation_performance(self):
        """Test that name generation takes less than 1ms."""
        # Arrange
        generator = self.name_generator
        max_time_ms = 1.0
        num_iterations = 100  # Test multiple times for consistency
        
        # Act & Assert
        for _ in range(num_iterations):
            start_time = time.perf_counter()
            generator.generate_name()
            end_time = time.perf_counter()
            
            execution_time_ms = (end_time - start_time) * 1000
            assert execution_time_ms < max_time_ms, (
                f"Name generation took {execution_time_ms:.3f}ms, "
                f"expected < {max_time_ms}ms"
            )

    def test_name_format_two_parts(self):
        """Test that generated name has exactly two parts separated by space."""
        # Arrange
        generator = self.name_generator
        
        # Act
        generated_name = generator.generate_name()
        name_parts = generated_name.split()
        
        # Assert
        assert len(name_parts) == 2, (
            f"Expected exactly 2 parts in name, got {len(name_parts)} "
            f"in '{generated_name}'"
        )

    def test_name_format_proper_capitalization(self):
        """Test that both parts of the name have proper capitalization."""
        # Arrange
        generator = self.name_generator
        
        # Act
        generated_name = generator.generate_name()
        name_parts = generated_name.split()
        
        # Assert
        assert len(name_parts) == 2, f"Expected 2 parts, got {len(name_parts)}"
        
        first_name, last_name = name_parts
        
        # Check first name capitalization
        assert first_name[0].isupper(), (
            f"First name '{first_name}' should start with uppercase letter"
        )
        assert first_name[1:].islower(), (
            f"First name '{first_name}' should have lowercase letters after first"
        )
        
        # Check last name capitalization
        assert last_name[0].isupper(), (
            f"Last name '{last_name}' should start with uppercase letter"
        )
        assert last_name[1:].islower(), (
            f"Last name '{last_name}' should have lowercase letters after first"
        )

    def test_name_format_alphabetic_characters(self):
        """Test that generated names contain only alphabetic characters and spaces."""
        # Arrange
        generator = self.name_generator
        
        # Act
        generated_name = generator.generate_name()
        
        # Assert
        for char in generated_name:
            assert char.isalpha() or char.isspace(), (
                f"Name '{generated_name}' contains invalid character '{char}'. "
                f"Only alphabetic characters and spaces allowed."
            )

    def test_name_generation_consistency(self):
        """Test that name generation is consistent in format across multiple calls."""
        # Arrange
        generator = self.name_generator
        num_tests = 50
        
        # Act & Assert
        for i in range(num_tests):
            name = generator.generate_name()
            
            # Validate string type
            assert isinstance(name, str), f"Iteration {i}: Expected string, got {type(name)}"
            
            # Validate non-empty
            assert len(name) > 0, f"Iteration {i}: Name should not be empty"
            
            # Validate two parts
            parts = name.split()
            assert len(parts) == 2, f"Iteration {i}: Expected 2 parts, got {len(parts)} in '{name}'"
            
            # Validate capitalization
            first_name, last_name = parts
            assert first_name.istitle(), f"Iteration {i}: First name '{first_name}' not properly capitalized"
            assert last_name.istitle(), f"Iteration {i}: Last name '{last_name}' not properly capitalized"

    def test_name_parts_minimum_length(self):
        """Test that both name parts have minimum reasonable length."""
        # Arrange
        generator = self.name_generator
        min_length = 2  # Minimum 2 characters per name part
        
        # Act
        generated_name = generator.generate_name()
        first_name, last_name = generated_name.split()
        
        # Assert
        assert len(first_name) >= min_length, (
            f"First name '{first_name}' too short. Expected >= {min_length} characters"
        )
        assert len(last_name) >= min_length, (
            f"Last name '{last_name}' too short. Expected >= {min_length} characters"
        )