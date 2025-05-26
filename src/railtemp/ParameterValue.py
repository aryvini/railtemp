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

from numpy.random import beta, normal
from scipy.stats import truncnorm
from enum import Enum, auto

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

    @abstractmethod
    def __str__(self)-> str:
        return super().__str__()


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

    def __str__(self) -> str:
        """
        Returns a string representation of the ConstantParameterValue.
        """
        return f"ConstantParameterValue(value={self.value})"

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

class RandomParameterMode(Enum):
    """
    Enum representing the behavior modes for random parameter values.

    Attributes:
        VARIABLE: The parameter value changes every time `get_value()` is called.
        FIXED_GLOBAL: The parameter value is set once and remains constant across all simulations.
        FIXED_PER_RUN: The parameter value is constant during a single simulation run, but is reinitialized for each new run.
                        Reinitialization is done by calling the `re_initialize` method. railtemp.py will call this method when the simulation is restarted.
    """
    VARIABLE = auto()  # Value changes every call to get_value()
    FIXED_GLOBAL = auto()  # Value is converted to a ConstantParameterValue and remains constant across ALL simulations
    FIXED_PER_RUN = auto()  # Value is constant during a simulation run, but reinitialized for each new run

class RandomParameterValue(AbstractParameterValue):
    """
    Abstract base class for random parameter values.
    Values are drawn from a distribution at each time step.
    Ensures that the `validate` method is called in the `get_value` method to validate the generated value.
    """


    def __init__(self):
        """
        Initializes the RandomParameterValue class.
        This class is intended to be subclassed, so it does not have any parameters.
        """
        super().__init__()
        self.mode = RandomParameterMode.VARIABLE  # Default mode is VARIABLE

        val = self._generate_value()
        self.validate(val)
        self.init_value = val

        pass

    def reinit(self):
        """
        Re-initializes the RandomParameterValue by generating a new value and validating it.
        This is useful when the mode is FIXED_PER_RUN.
        This will be called by railtemp.py
        """
        if self.mode is RandomParameterMode.FIXED_PER_RUN:
            # Reinitialize the value only if the mode is FIXED_PER_RUN
            val = self._generate_value()
            self.validate(val)
            self.init_value = val
        return self


    def set_mode(self, mode: RandomParameterMode) -> Union["RandomParameterValue", ConstantParameterValue]:
        """
        Sets the mode for the RandomParameterValue.

        Args:
            mode (RandomParameterMode): The mode to set.

        Raises:
            ValueError: If mode is not an instance of RandomParameterMode.
        """
        if not isinstance(mode, RandomParameterMode):
            raise ValueError("mode must be an instance of RandomParameterMode.")

        if mode == RandomParameterMode.FIXED_GLOBAL:
            try:
                constant_value = ConstantParameterValue(self.get_value())
                self.__class__ = constant_value.__class__
                self.__dict__ = constant_value.__dict__
                return ConstantParameterValue(self.get_value())
            except (ValueError, TypeError) as e:
                raise ValueError(f"Failed to create ConstantParameterValue: {e}")

        self.mode = mode
        return self


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
        if self.mode is not RandomParameterMode.VARIABLE:
            return self.init_value
        else:
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
        super().__init__()

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

    def __str__(self) -> str:
        """
        Returns a string representation of the UniformParameterValue.
        """
        return f"UniformParameterValue(low={self.low}, high={self.high})"


class BetaParameterValue(RandomParameterValue):
    """
    A class to represent a Beta distribution for rail temperature.
    """

    def __init__(self, *, alpha: float = None, beta: float = None, mean: float = None, sigma: float = None):
        """Init the BetaDistribution with either alpha and beta parameters or mean and sigma parameters.

        Args:
            alpha (float, optional): alpha parameter of the Beta distribution.
            beta (float, optional): beta parameter of the Beta distribution.
            mean (float, optional): mean value of the Beta distribution.
            sigma (float, optional): deviation of the Beta distribution.

        Raises:
            ValueError: If neither (alpha, beta) nor (mean, sigma) are provided.
        """

        if alpha is not None and beta is not None:
            self.alpha = alpha
            self.beta = beta
            pass
        elif mean is not None and sigma is not None:
            n = (mean * (1 - mean)) / (sigma**2)
            self.alpha = mean * n
            self.beta = (1 - mean) * n
            pass
        else:
            raise ValueError("You must provide either (alpha, beta) or (mean, sigma).")

        super().__init__()

    def validate(self, value: float):
        pass

    def _generate_value(self) -> float:
        return beta(self.alpha, self.beta)

    def __str__(self) -> str:
        """
        Returns a string representation of the BetaParameterValue.
        """
        return f"BetaParameterValue(alpha={self.alpha}, beta={self.beta})"


class NormalParameterValue(RandomParameterValue):
    """
    Class representing a normal random parameter value.
    """

    def __init__(self, mean: float, std: float):
        self.mean = mean
        self.std = std
        super().__init__()

    def validate(self, value: float):
        pass

    def _generate_value(self) -> float:
        return normal(self.mean, self.std)

    def __str__(self) -> str:
        """
        Returns a string representation of the NormalParameterValue.
        """
        return f"NormalParameterValue(mean={self.mean}, std={self.std})"

class ClippedNormalParameterValue(RandomParameterValue):

    def __init__(self, mean: float, std: float, low: float, high: float):
        self.mean = mean
        self.std = std
        self.low = low
        self.high = high
        super().__init__()

    def validate(self, value: float):
        pass

    def _generate_value(self):
        a, b = (self.low - self.mean) / self.std, (self.high - self.mean) / self.std
        return truncnorm.rvs(a, b, loc=self.mean, scale=self.std)

    def __str__(self) -> str:
        """
        Returns a string representation of the ClippedNormalParameterValue.
        """
        return f"ClippedNormalParameterValue(mean={self.mean}, std={self.std}, low={self.low}, high={self.high})"