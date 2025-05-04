# ===================================================================
# Author     : Ary V. N. Frigeri
# Date       : 2025-05
# Purpose    : Mestrado UTFPR-PB
#
# Description: Class that holds parameter value objects to be used in the railtemp simulation objects
#
# Usage      : Class file only
# ===================================================================


import random
from typing import Union
from abc import ABC,abstractmethod


class ParameterValue(ABC):
    """
    Abstract base class for parameter values.
    """

    @abstractmethod
    def get_value(self) -> float:
        """
        Abstract method to retrieve the parameter value.
        """
        pass


class ConstantParameterValue(ParameterValue):
    """
    Class representing a Constant parameter value.
    """

    def __init__(self, value: Union[float, int]):
        if not isinstance(value, (float, int)):
            raise ValueError("Value must be a float or int.")

        self.value = value

    def get_value(self) -> float:
        return self.value

class RandomParameterValue(ParameterValue):
    """
    Abstract base class for random parameter values.
    Ensures that the `validate` method is called to validate the generated value.
    """

    @abstractmethod
    def validate(self, value: float):
        """
        Abstract method to validate the generated random value.
        Must be implemented by subclasses.
        """
        pass

    @abstractmethod
    def _generate_value(self) -> float:
        """
        Abstract method to generate the random value.
        Must be implemented by subclasses.
        """
        pass

    def get_value(self) -> float:
        """
        Generates the random value and validates it.
        """
        value = self._generate_value()
        self.validate(value)  # Validate the generated value
        return value


class UniformParameterValue(RandomParameterValue):
    """
    Class representing a uniform random parameter value.
    """

    def __init__(self, low: float, high: float):
        self.low = low
        self.high = high

    def validate(self, value: float):
        """
        Validates the generated value to ensure it is within the range [low, high].
        """
        if not (self.low <= value <= self.high):
            raise ValueError(f"Generated value {value} is out of bounds [{self.low}, {self.high}].")

    def _generate_value(self) -> float:
        """
        Generates a random value uniformly between `low` and `high`.
        """
        return random.uniform(self.low, self.high)



def parameter_value_factory(value):
    """
    Validates or converts the input value into a `ConstantParameterValue` or
    ensures it is already a `ParameterValue` instance.

    Parameters:
        value (any): The input value to validate or convert. It can be a float
                     or an instance of `ParameterValue`.

    Returns:
        ConstantParameterValue or ParameterValue: If the input is a float, it
        is converted to a `ConstantParameterValue`. If it is already a
        `ParameterValue` instance, it is returned as-is.

    Raises:
        TypeError: If the input value is neither a float nor a `ParameterValue`
                   instance.
    """
    if isinstance(value, float):
        return ConstantParameterValue(value)
    elif isinstance(value, int):
        return ConstantParameterValue(float(value))
    elif isinstance(value, ParameterValue):
        return value
    else:
        raise TypeError(f"Got {type(value)}")