import pytest
from railtemp.ParameterValue import UniformParameterValue, ConstantParameterValue


@pytest.mark.parametrize("run", range(10))
def test_convert_random_to_constant(run):
    """
    Test the conversion of a random parameter value to a constant parameter value.
    """
    lower_bound = 0
    upper_bound = 10
    random_value = UniformParameterValue(lower_bound, upper_bound)
    random_value.constant_during_simulation(value=True)

    assert isinstance(random_value, ConstantParameterValue)
    assert lower_bound < random_value.get_value() <= upper_bound