import pytest
from railtemp.ParameterValue import BetaParameterValue, ClippedNormalParameterValue, NormalParameterValue, RandomParameterMode, UniformParameterValue, ConstantParameterValue


@pytest.mark.parametrize("run", range(10))
def test_convert_random_to_constant(run):
    """
    Test the conversion of a random parameter value to a constant parameter value.
    """
    lower_bound = 0
    upper_bound = 10
    random_value = UniformParameterValue(lower_bound, upper_bound)
    random_value.set_mode(RandomParameterMode.FIXED_GLOBAL)


    assert isinstance(random_value, ConstantParameterValue)
    assert lower_bound < random_value.get_value() <= upper_bound

@pytest.mark.parametrize(
    "param_class, args",
    [
        (UniformParameterValue, (0, 10)),
        (ConstantParameterValue, {"value": 10}),
        (BetaParameterValue, {"alpha": 5, "beta": 10}),
        (NormalParameterValue, {"mean": 0, "std": 1}),
        (ClippedNormalParameterValue, {"mean": 0, "std": 1, "low": -1, "high": 1}),
    ],
)
def test_instantiate_parameter_value(param_class, args):
    """
    Test the instantiation of a parameter value.
    """
    if isinstance(args, tuple):
        instance = param_class(*args)
    else:
        instance = param_class(**args)

    assert isinstance(instance, param_class)