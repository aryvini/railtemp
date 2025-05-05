# ===================================================================
# Author     : Ary V. N. Frigeri
# Date       : 2025-05
# Purpose    : Mestrado UTFPR-PB
#
# Description: Class that holds parameter value objects to be used in the railtemp simulation objects
#
# Usage      : Class file only
# ===================================================================


from random import uniform
from typing import Union
from abc import ABC,abstractmethod


class AbstractParameterValue(ABC):
    """
    Abstract base class for parameter values.
    """

    @abstractmethod
    def get_value(self) -> float:
        """
        Abstract method to retrieve the parameter value.
        """
        pass


class ConstantParameterValue(AbstractParameterValue):
    """
    Class representing a Constant parameter value.
    """

    def __init__(self, value: Union[float, int]):
        if not isinstance(value, (float, int)):
            raise ValueError("Value must be a float or int.")

        self.value = value

    def get_value(self) -> float:
        return self.value

class RandomParameterValue(AbstractParameterValue):
    """
    Abstract base class for random parameter values.
    Values are drawn from a distribution at each time step.
    Ensures that the `validate` method is called in the `get_value` method to validate the generated value.
    """

    def constant_during_simulation(self, value: bool=False) -> Union[None, ConstantParameterValue]:
        """
        Method to draw a random value from the distribution and set it as a constant during the simulation.
        Otherwise, values are drawn at each time step.
        Converts this instance to a ConstantParameterValue if value is True.
        """
        if not isinstance(value, bool):
            raise ValueError("Value for constant_during_simulation must be a boolean.")

        if value:
            try:
                constant_value = ConstantParameterValue(self.get_value())
                self.__class__ = constant_value.__class__
                self.__dict__ = constant_value.__dict__
                return ConstantParameterValue(self.get_value())
            except (ValueError, TypeError) as e:
                raise ValueError(f"Failed to create ConstantParameterValue: {e}")





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
        return uniform(self.low, self.high)



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
    elif isinstance(value, AbstractParameterValue):
        return value
    else:
        raise TypeError(f"Got {type(value)}")