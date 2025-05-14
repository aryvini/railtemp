from typing import List
import random
import pytest
import numpy.random  # noqa: F811
from deepdiff import DeepDiff



from railtemp.Montecarlo import Montecarlo, SimuRun  # noqa: E402
from railtemp.ParameterValue import (  # noqa: E402
    BetaParameterValue,
    ClippedNormalParameterValue,
    UniformParameterValue,
)  # noqa: E402

from railtemp.railtemp import Rail, RailMaterial  # noqa: E402
import json  # noqa: E402


class SpecificHeatWrapper:
    def __init__(self):
        SpecificHeatD = UniformParameterValue(439, 487).constant_during_simulation(True)
        self.constant = SpecificHeatD.get_value()

    def get(self, _):
        return self.constant


def create_rail_object() -> Rail:
    # Distribuições específicas
    DensityD = UniformParameterValue(7840, 7860).constant_during_simulation(False)
    SolarAbsD = BetaParameterValue(5, 2).constant_during_simulation(True)
    RailEmiss = BetaParameterValue(0.7, 0.1).constant_during_simulation(True)
    ConvectionAreaD = ClippedNormalParameterValue(
        0.43046, 0.05, 0, 0.43046
    ).constant_during_simulation(True)
    RadiationAreaD = ClippedNormalParameterValue(
        0.43046, 0.05, 0, 0.43046
    ).constant_during_simulation(True)
    AmbientEmiss = BetaParameterValue(0.5, 0.1).constant_during_simulation(True)

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


@pytest.mark.parametrize("run_id, weather_file, expected_diff", [
    (0, "./tests/artifacts/input_montecarlo.csv", {}),
    (1, "./tests/artifacts/invalid_montecarlo.csv", "not_empty"),
])
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

    [sr.run() for ilist in simu_objs.values() for sr in ilist]

    rst_dict = {
        "results": [sr.get_results_as_dict() for ilist in simu_objs.values() for sr in ilist]
    }

    rst_dict = {"results": [entry["simu_results"] for entry in rst_dict["results"]]}

    # read json artifact to compare against
    with open("./tests/artifacts/monte_carlo_result.json", "r") as file:
        loaded = json.load(file)

    diff = DeepDiff(rst_dict, loaded, significant_digits=5)

    if expected_diff == {}:
        assert diff == {}
    else:
        assert diff != {}
