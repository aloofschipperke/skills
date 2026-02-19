"""Example test module showing proper structure for spec-driven development."""
import pytest


@pytest.mark.requirement("FR-1")
def test_example():
    """
    Example test demonstrating proper structure.

    Given: [Initial condition]
    When: [Action taken]
    Then: [Expected result]

    Requirements: FR-1
    """
    # Arrange
    expected = True

    # Act
    actual = True

    # Assert
    assert actual == expected, "Example test should pass"
