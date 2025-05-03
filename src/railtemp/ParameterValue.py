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
    Class representing a random parameter value.
    """
    @abstractmethod
    def validate(self):
        pass


def validate_or_convert(value):
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