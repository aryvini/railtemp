from typing import List
import random
import pytest
import numpy.random  # noqa: F811
from deepdiff import DeepDiff
import pandas as pd

from railtemp.Montecarlo import Montecarlo, SimuRun  # noqa: E402
from railtemp.ParameterValue import (  # noqa: E402
    BetaParameterValue,
    ClippedNormalParameterValue,
    RandomParameterMode,
    UniformParameterValue,
)  # noqa: E402

from railtemp.railtemp import Rail, RailMaterial  # noqa: E402
import json  # noqa: E402


class SpecificHeatWrapper:
    def __init__(self):
        SpecificHeatD = UniformParameterValue(439, 487).set_mode(RandomParameterMode.FIXED_GLOBAL)
        self.constant = SpecificHeatD.get_value()

    def get(self, _):
        return self.constant


def create_rail_object() -> Rail:
    # Distribuições específicas
    DensityD = UniformParameterValue(7840, 7860).set_mode(RandomParameterMode.VARIABLE)
    SolarAbsD = BetaParameterValue(alpha=5, beta=2).set_mode(RandomParameterMode.FIXED_PER_RUN)
    RailEmiss = BetaParameterValue(mean=0.7, sigma=0.1).set_mode(RandomParameterMode.FIXED_GLOBAL)
    ConvectionAreaD = ClippedNormalParameterValue(0.43046, 0.05, 0, 0.43046).set_mode(
        RandomParameterMode.FIXED_PER_RUN
    )
    RadiationAreaD = ClippedNormalParameterValue(0.43046, 0.05, 0, 0.43046).set_mode(
        RandomParameterMode.FIXED_GLOBAL
    )
    AmbientEmiss = BetaParameterValue(mean=0.5, sigma=0.1).set_mode(
        RandomParameterMode.FIXED_GLOBAL
    )

    steel = RailMaterial(
        density=DensityD,
        solar_absort=SolarAbsD,
        emissivity=RailEmiss,
        specific_heat=SpecificHeatWrapper().get,
    )

    rail = Rail(
        name="UIC54",
        azimuth=93,
        lat=41.482628,
        long=-7.183741,
        elev=220,
        cross_area=7.16e-3,
        convection_area=ConvectionAreaD,
        radiation_area=RadiationAreaD,
        ambient_emissivity=AmbientEmiss,
        material=steel,
    )
    return rail


@pytest.mark.parametrize(
    "run_id, weather_file, expected_diff",
    [
        (0, "./tests/artifacts/input_montecarlo.csv", {}),
        (1, "./tests/artifacts/invalid_montecarlo.csv", "not_empty"),
    ],
)
@pytest.mark.parametrize("iteration", range(2))  # Each case runs 2 times
def test_montecarlo(run_id, weather_file, expected_diff, iteration):
    # Set the seed for reproducibility
    SEED = 42
    random.seed(SEED)
    numpy.random.seed(SEED)
    rail_model: Rail = create_rail_object()
    weather_file_list: List[str] = [weather_file]

    mtcarlo = Montecarlo(
        rail_object=rail_model,
        weather_input_list=weather_file_list,
        num_variations=2,
        name="Campaing",
    )
    simu_objs: dict[str, List[SimuRun]]
    simu_objs = mtcarlo.generate_simulation_objects()
    simu_objs: List[SimuRun] = [sr for _, sr in simu_objs]

    [sr.run() for sr in simu_objs]

    rst_dict = {"results": [sr.get_results_as_dict() for sr in simu_objs]}

    rst_dict = {"results": [entry["simu_results"] for entry in rst_dict["results"]]}

    # with open("./tests/artifacts/monte_carlo_result_fixing.json", "w+") as file:
    #     loaded = json.dumps(rst_dict, indent=4)
    #     file.write(loaded)

    # read json artifact to compare against
    with open("./tests/artifacts/monte_carlo_result.json", "r") as file:
        loaded = json.load(file)

    diff = DeepDiff(rst_dict, loaded, significant_digits=5)

    if expected_diff == {}:
        assert diff == {}
    else:
        assert diff != {}

    # check if the defined mode is respected
    # 1. FIXED_GLOBAL: all simulations should have the same value

    fixed_global_attributes = ["material_emissivity", "radiation_area"]

    for attr in fixed_global_attributes:
        # check if all simulations have the same value for this attribute
        # Collect all values for the given attribute across all simulations and all rows
        vals = []
        for sr in simu_objs:
            lst = sr.result_df[attr].dropna().to_list()
            vals.extend(lst)

        set_vals = set(vals)
        assert len(set_vals) == 1, (
            f"Attribute {attr} has different values across simulations: {set_vals}"
        )

    # 2. FIXED_PER_RUN: each simulation run should have a different value
    fixed_per_run_attributes = ["solar_absort", "convection_area"]

    for attr in fixed_per_run_attributes:
        # check if all simulations have the same value for this attribute
        # Collect all values for the given attribute across all simulations and all rows
        vals = []
        for sr in simu_objs:
            lst = sr.result_df[attr].dropna().to_list()
            vals.extend(lst)

        set_vals = set(vals)
        assert len(set_vals) == 2, (
            f"Attribute {attr} has different values across simulations: {set_vals}"
        )

    # 3. VARIABLE: each timestep should have a different value
    variable_attributes = ["density"]

    for attr in variable_attributes:
        # check if all simulations have the same value for this attribute
        # Collect all values for the given attribute across all simulations and all rows
        vals = []
        for sr in simu_objs:
            lst = sr.result_df[attr].dropna().to_list()
            vals.extend(lst)

        set_vals = set(vals)
        # 100 is higher than the timesteps.
        assert len(set_vals) >= 100, (
            f"Attribute {attr} has different values across simulations: {set_vals}"
        )


@pytest.mark.parametrize(
    "weather_file",
    [
        "./tests/artifacts/input_montecarlo_with_trail_initial.csv",
        "./tests/artifacts/input_montecarlo.csv",
    ],
)
def test_initial_temperature_handling(weather_file):
    # This test checks if the initial temperature is handled correctly in Montecarlo simulations

    # Set the seed for reproducibility
    SEED = 42
    random.seed(SEED)
    numpy.random.seed(SEED)
    rail_model: Rail = create_rail_object()
    weather_file_list: List[str] = [weather_file]

    mtcarlo = Montecarlo(
        rail_object=rail_model,
        weather_input_list=weather_file_list,
        num_variations=2,
        name="Campaing",
    )
    simu_objs: dict[str, List[SimuRun]]
    simu_objs = mtcarlo.generate_simulation_objects()
    simu_objs: List[SimuRun] = [sr for _, sr in simu_objs]

    [sr.run() for sr in simu_objs]

    rst_dict = {"results": [sr.get_results_as_dict() for sr in simu_objs]}

    rst_dict = {"results": [entry["simu_results"] for entry in rst_dict["results"]]}

    with open("./tests/artifacts/monte_carlo_result_with_trail_initial.json", "w+") as file:
        loaded = json.dumps(rst_dict, indent=4)
        file.write(loaded)

    df = pd.read_csv(weather_file)
    if "trail_initial" in df.columns:
        expected_trail_initial = df["trail_initial"].iloc[0]
    else:
        expected_trail_initial = df["ambient_temperature"].iloc[0]

    for sr in simu_objs:
        # The initial temperature used in the simulation should match the trail_initial from the weather data
        # Tr_simu at time 0 must be the trail_initial used
        actual_trail_initial = sr.result_df["Tr_simu"].iloc[0]
        diff = DeepDiff(expected_trail_initial, actual_trail_initial, significant_digits=5)
        assert diff == {}
