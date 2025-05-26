import pytest
from railtemp.railtemp import Rail, RailMaterial, WeatherData, CNU
import pandas as pd
from railtemp.ParameterValue import UniformParameterValue, RandomParameterMode

import pytz


@pytest.mark.parametrize(
    "modelled_As, distinct",
    [
        (UniformParameterValue(1, 2), True),
        (UniformParameterValue(1, 2).set_mode(RandomParameterMode.FIXED_GLOBAL), False),
        (0.1, False),
    ],
)
def test_random_rail_area(modelled_As, distinct):
    input_data = "./tests/artifacts/input_data.csv"

    df = pd.read_csv(input_data)  # import csv file
    df["Date"] = pd.to_datetime(df["Date"])
    df.set_index("Date", inplace=True)

    steel = RailMaterial(density=7850, solar_absort=0.8, emissivity=0.7)
    UIC54 = Rail(
        name="UIC54",
        azimuth=93,
        lat=41.482628,
        long=-7.183741,
        elev=220,
        cross_area=7.16e-3,
        convection_area=430.46e-3,
        radiation_area=430.46e-3,
        ambient_emissivity=0.5,
        material=steel,
    )

    day1 = WeatherData(
        solar_radiation=df["SR"],
        wind_velocity=df["Wv_avg"],
        ambient_temperature=df["TA"],
        timezone=pytz.timezone("Europe/Lisbon"),
    )

    Area = modelled_As

    simu1 = CNU(rail=UIC54, weather=day1)

    simu1.run_fixed_area(Trail_initial=23, Area=Area)

    # Assert that simu1.df['As'] has distinct values if distinct is True
    if distinct:
        assert simu1.df["As"].nunique() > 1, "Values in simu1.df['As'] are not distinct"
    else:
        assert simu1.df["As"].nunique() == 1, (
            "Values in simu1.df['As'] are distinct when they shouldn't be"
        )
