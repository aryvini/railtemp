# ===================================================================
# Author     : Ary V. N. Frigeri
# Date       : 2025-05
# Purpose    : Mestrado UTFPR-PB
#
# Description: Monte Carlo simulation class for railtemp simulations
#
# Usage      : Class file only
# ===================================================================


import json
import time
from railtemp.railtemp import CNU, Rail, WeatherData
from typing import List
from copy import deepcopy
from pandas._typing import DataFrame



class SimuRun:

    """
    Class representing a simulation run.
    """

    def __init__(self, simulation_object:CNU):
        if not isinstance(simulation_object, CNU):
            raise ValueError("simulation_object must be an instance of CNU.")

        self.simulation_object: CNU = simulation_object
        self.start_time = None
        self.end_time = None
        self.result_df: DataFrame = None  # Placeholder for DataFrame to be populated during simulation

    def run(self, Trail_initial: float=None):
        """
        Run the simulation with the given initial temperature.
        If initial temperature not given, the first value of the ambient temperature from weather obeject is used.
        """
        if Trail_initial is None:
            Trail_initial = self.__get_initial_temperature()
        if not isinstance(Trail_initial, (float, int)):
            raise ValueError("Trail_initial must be a float or int.")
        self.start_time = time.time()
        self.simulation_object.run(Trail_initial=Trail_initial)
        self.end_time = time.time()
        self.result_df = self.simulation_object.results

    def __get_initial_temperature(self)-> float:
        """
        Get the initial temperature of the simulation based on the first input of the weather object.
        """
        return self.simulation_object.weather.Tamb.iloc[0]

    def get_results_as_dict(self) -> dict:
        """
        Get the results of the simulation as a dictionary.
        """
        if self.result_df is None:
            raise ValueError("Simulation has not been run yet.")
        return self.result_df.to_dict(orient='index')




class Montecarlo:
    """
    Handles Montecarlo simulations.
    """

    def __init__(self, rail_object: Rail, weather_objects: List[WeatherData], num_simulations=2, name:str="Campaing"):

        if not isinstance(rail_object, Rail):
            raise ValueError("rail_object must be an instance of Rail.")
        if not all(isinstance(obj, WeatherData) for obj in weather_objects):
            raise ValueError("All weather_objects must be instances of WeatherData.")
        if not isinstance(num_simulations, int) or num_simulations <= 0:
            raise ValueError("num_simulations must be a positive integer.")

        self.name = name
        self.rail_object: Rail = rail_object
        self.weather_objects: List[WeatherData] = weather_objects
        self.num_simulations = num_simulations


    def generate_simulation_objects(self) -> List[SimuRun]:
        """
        Generate a list of simulation run objects.
        """
        simulations = []
        for weather_data in self.weather_objects:
            for _ in range(self.num_simulations):
                rail =  deepcopy(self.rail_object) # Use the input rail object as template
                simulation_object = CNU(rail, weather_data)
                simulations.append(SimuRun(simulation_object))
        return simulations


    def save_simulation_as_json(self, simulation, file_path):
        """
        Save an individual simulation run as a JSON file.
        """
        data = {
            "start_time": simulation.start_time,
            "end_time": simulation.end_time,
            "duration": simulation.end_time - simulation.start_time,
            "results": simulation.df.to_dict(),  # Assuming simulation.df is a DataFrame
        }
        with open(file_path, "w") as json_file:
            json.dump(data, json_file, indent=4)
