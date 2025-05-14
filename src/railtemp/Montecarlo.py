# ===================================================================
# Author     : Ary V. N. Frigeri
# Date       : 2025-05
# Purpose    : Mestrado UTFPR-PB
#
# Description: Monte Carlo simulation class for railtemp simulations
#
# Usage      : Class file only
# ===================================================================


import time

import pytz
from railtemp.railtemp import CNU, Rail, WeatherData
from typing import List, Dict
from copy import deepcopy
from pandas import DataFrame
import pandas as pd
from enum import Flag, auto
import uuid


class SimuRunStatus(Flag):
    """
    Enum for simulation run status.
    """

    NOT_STARTED = auto()
    COMPLETED = auto()
    FAILED = auto()


class SimuRun:
    """
    Class representing a simulation run.
    """

    def __repr__(self):
        return f"SimuRun({self._uuid},status:{self.status.name})"

    def __init__(self, simulation_object: CNU):
        if not isinstance(simulation_object, CNU):
            raise ValueError("simulation_object must be an instance of CNU.")

        self._uuid = uuid.uuid4().hex[:8]  # Generate a short UUID (8 characters)
        self.status: SimuRunStatus = SimuRunStatus.NOT_STARTED
        self.simulation_object: CNU = simulation_object
        self.start_time: float = None
        self.end_time: float = None
        self.result_df: DataFrame = (
            None  # Placeholder for DataFrame to be populated during simulation
        )

    def run(self, Trail_initial: float = None):
        """
        Run the simulation with the given initial temperature.
        If initial temperature not given, the first value of the ambient temperature from weather obeject is used.
        """
        if Trail_initial is None:
            Trail_initial = self.__get_initial_temperature()
        if not isinstance(Trail_initial, (float, int)):
            self.status = SimuRunStatus.FAILED
            raise ValueError("Trail_initial must be a float or int.")

        try:
            self.start_time = time.time()
            self.simulation_object.run(Trail_initial=Trail_initial)
            self.end_time = time.time()
            self.result_df = self.simulation_object.result
            self.set_simulation_status(SimuRunStatus.COMPLETED)
            print(f"Finished simulation: {self.status}")
        except Exception as e:
            self.set_simulation_status(SimuRunStatus.FAILED)
            self.end_time = time.time()
            raise RuntimeError(f"Simulation failed: {e}")

    def set_simulation_status(self, status: SimuRunStatus):
        self.status = status

    def __get_initial_temperature(self) -> float:
        """
        Get the initial temperature of the simulation based on the first input of the weather object.
        """
        return self.simulation_object.weather.Tamb.iloc[0]

    def get_summary(self) -> dict:
        summary = {}

        pars = {
            "material_density": str(self.simulation_object.rail.material._density),
            "material_solar_absortion": str(self.simulation_object.rail.material._solar_absort),
            "material_emissivity": str(self.simulation_object.rail.material._emissivity),
            "rail_convection_area": str(self.simulation_object.rail._convection_area),
            "rail_radiation_area": str(self.simulation_object.rail._radiation_area),
            "rail_ambient_emissivity": str(self.simulation_object.rail._ambient_emissivity),
        }
        if callable(self.simulation_object.rail.material.specific_heat):
            pars["material_specific_heat"] = str(
                self.simulation_object.rail.material.specific_heat.__self__.__class__
            )
        else:
            pars["material_specific_heat"] = "custom function"

        duration = {
            "id": self._uuid,
            "start_time": str(self.start_time),
            "end_time": str(self.end_time),
            "duration_time": str(self.end_time - self.start_time),
            "status": str(self.status),
        }

        summary["parameters"] = pars
        summary["duration"] = duration

        return summary

    def get_results_as_dict(self) -> dict:
        """
        Get the results of the simulation as a dictionary.
        """
        if self.status is not SimuRunStatus.COMPLETED:
            raise ValueError("Simulation has not been run yet.")
        if not isinstance(self.result_df, pd.DataFrame):
            raise ValueError("Error getting simulation resulting dataframe.")
        simu_results = self.result_df.to_dict(orient="index")
        # transform timestamp indexes into str
        simu_results = {str(k): v for k, v in simu_results.items()}
        summary = self.get_summary()
        return {"summary": summary, "simu_results": simu_results}


class Montecarlo:
    """
    Handles Montecarlo simulations.
    """

    def __init__(
        self,
        rail_object: Rail,
        weather_input_list: List[str],
        weather_time_zone: str = "Europe/Lisbon",
        num_simulations=2,
        name: str = "Campaing",
    ):
        if not isinstance(rail_object, Rail):
            raise ValueError("rail_object must be an instance of Rail.")
        if weather_input_list == []:
            raise ValueError("weather_input_data list cannot be empty.")
        if not all(isinstance(input, str) for input in weather_input_list):
            raise ValueError("weather_input_data must be a list of strings.")
        if not isinstance(num_simulations, int) or num_simulations <= 0:
            raise ValueError("num_simulations must be a positive integer.")

        self.name = name
        self.rail_object: Rail = rail_object
        self.weather_time_zone = weather_time_zone
        self.weather_objects: Dict[str, WeatherData] = Montecarlo.__parse_weather_data(
            input_list=weather_input_list, tz=self.weather_time_zone
        )
        self.num_simulations = num_simulations

    @staticmethod
    def __parse_weather_data(input_list, tz) -> Dict[str, WeatherData]:
        """
        Parse the weather data from the input list of strings.
        Create a WeatherData object for each input string.
        """
        weather_objects: Dict[str, WeatherData] = {}
        for file_path in input_list:
            try:
                df = pd.read_csv(file_path, parse_dates=["record_date"], index_col="record_date")
                weather_data = WeatherData(
                    solar_radiation=df["solar_radiation"],
                    wind_velocity=df["wv_avg"],
                    ambient_temperature=df["ambient_temperature"],
                    timezone=pytz.timezone(tz),
                )
                weather_objects[file_path] = weather_data
            except Exception as e:
                raise ValueError(f"Error parsing weather data: {e}")
        return weather_objects

    def generate_simulation_objects(self) -> dict[str, List[SimuRun]]:
        """
        Generate a list of simulation run objects.
        Create a new simulation object for each weather data object.
        """
        return {
            input_file: [
                SimuRun(CNU(deepcopy(self.rail_object), weather_data))
                for _ in range(self.num_simulations)
            ]
            for input_file, weather_data in self.weather_objects.items()
        }
