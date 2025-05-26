import pytest
from railtemp.railtemp import Rail, RailMaterial, WeatherData, CNU
import pandas as pd
from railtemp.ParameterValue import RandomParameterMode, UniformParameterValue, ConstantParameterValue
import pytz


@pytest.mark.parametrize(
    "input_data, expected_result",
    [
        ("./tests/artifacts/input_data.csv", True),
        ("./tests/artifacts/invalid_data.csv", False),
    ],
)
def test_simulation(input_data, expected_result):
    results_data = "./tests/artifacts/results.csv"

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

    simu1 = CNU(rail=UIC54, weather=day1)

    simu1.run(Trail_initial=23)

    source_truth_df = pd.read_csv(results_data)
    source_truth_df["Date"] = pd.to_datetime(source_truth_df["Date"])
    source_truth_df.set_index("Date", inplace=True)

    assert set(source_truth_df.columns.to_list()).issubset(set(simu1.result.columns.tolist()))

    # Conditions list
    conditions_list = []
    for col in source_truth_df.columns:
        conditions_list.append(
            simu1.result[col].to_list() == pytest.approx(source_truth_df[col].to_list())
        )

    # Check if all conditions Matches expected result
    assert all(conditions_list) == expected_result


@pytest.mark.parametrize(
    "input_data, expected_result",
    [
        ("./tests/artifacts/input_data.csv", True),
        ("./tests/artifacts/invalid_data.csv", False),
    ],
)
def test_simulation_with_parameter_value_objects(input_data, expected_result):
    results_data = "./tests/artifacts/results.csv"

    df = pd.read_csv(input_data)  # import csv file
    df["Date"] = pd.to_datetime(df["Date"])
    df.set_index("Date", inplace=True)

    density = ConstantParameterValue(value=7850)
    solar_absort = ConstantParameterValue(value=0.8)
    emissivity = ConstantParameterValue(value=0.7)
    azimuth = ConstantParameterValue(value=93)
    lat = ConstantParameterValue(value=41.482628)
    long = ConstantParameterValue(value=-7.183741)
    elev = ConstantParameterValue(value=220)
    cross_area = ConstantParameterValue(value=7.16e-3)
    convection_area = ConstantParameterValue(value=430.46e-3)
    radiation_area = ConstantParameterValue(value=430.46e-3)
    ambient_emissivity = ConstantParameterValue(value=0.5)

    steel = RailMaterial(density=density, solar_absort=solar_absort, emissivity=emissivity)
    UIC54 = Rail(
        name="UIC54",
        azimuth=azimuth,
        lat=lat,
        long=long,
        elev=elev,
        cross_area=cross_area,
        convection_area=convection_area,
        radiation_area=radiation_area,
        ambient_emissivity=ambient_emissivity,
        material=steel,
    )

    day1 = WeatherData(
        solar_radiation=df["SR"],
        wind_velocity=df["Wv_avg"],
        ambient_temperature=df["TA"],
        timezone=pytz.timezone("Europe/Lisbon"),
    )

    simu1 = CNU(rail=UIC54, weather=day1)

    simu1.run(Trail_initial=23)

    source_truth_df = pd.read_csv(results_data)
    source_truth_df["Date"] = pd.to_datetime(source_truth_df["Date"])
    source_truth_df.set_index("Date", inplace=True)

    assert set(source_truth_df.columns.to_list()).issubset(set(simu1.result.columns.tolist()))

    # Conditions list
    conditions_list = []
    for col in source_truth_df.columns:
        conditions_list.append(
            simu1.result[col].to_list() == pytest.approx(source_truth_df[col].to_list())
        )
    # Check if all conditions Matches expected result
    assert all(conditions_list) == expected_result


@pytest.mark.parametrize(
    "input_data, expected_result",
    [
        ("./tests/artifacts/input_data.csv", False),
        ("./tests/artifacts/invalid_data.csv", False),
    ],
)
@pytest.mark.parametrize("run", range(10))  # Run the test 10 times
def test_simulation_with_random_value_object(input_data, expected_result, run):
    results_data = "./tests/artifacts/results.csv"

    df = pd.read_csv(input_data)  # import csv file
    df["Date"] = pd.to_datetime(df["Date"])
    df.set_index("Date", inplace=True)

    density = UniformParameterValue(7800, 7900)
    density = density.set_mode(RandomParameterMode.FIXED_GLOBAL)
    solar_absort = UniformParameterValue(0.7, 0.9)
    emissivity = UniformParameterValue(0.6, 0.8)

    convection_area = UniformParameterValue(430.46e-3, 450.46e-3)
    azimuth = UniformParameterValue(90, 100)
    lat = UniformParameterValue(41.48, 41.49)
    long = UniformParameterValue(-7.2, -7.1)
    elev = UniformParameterValue(200, 250)
    cross_area = UniformParameterValue(7.0e-3, 7.5e-3).set_mode(RandomParameterMode.FIXED_GLOBAL)
    radiation_area = UniformParameterValue(430.46e-3, 450.46e-3)
    ambient_emissivity = UniformParameterValue(0.4, 0.6)
    convection_area = UniformParameterValue(430.46e-3, 450.46e-3)

    steel = RailMaterial(density=density, solar_absort=solar_absort, emissivity=emissivity, specific_heat=ConstantParameterValue(value=500))
    UIC54 = Rail(
        name="UIC54",
        azimuth=azimuth,
        lat=lat,
        long=long,
        elev=elev,
        cross_area=cross_area,
        convection_area=convection_area,
        radiation_area=radiation_area,
        ambient_emissivity=ambient_emissivity,
        material=steel,
    )

    day1 = WeatherData(
        solar_radiation=df["SR"],
        wind_velocity=df["Wv_avg"],
        ambient_temperature=df["TA"],
        timezone=pytz.timezone("Europe/Lisbon"),
    )

    simu1 = CNU(rail=UIC54, weather=day1)

    simu1.run(Trail_initial=23.0)

    source_truth_df = pd.read_csv(results_data)
    source_truth_df["Date"] = pd.to_datetime(source_truth_df["Date"])
    source_truth_df.set_index("Date", inplace=True)

    assert set(source_truth_df.columns.to_list()).issubset(set(simu1.result.columns.tolist()))

    # Conditions list
    conditions_list = []
    for col in source_truth_df.columns:
        conditions_list.append(
            simu1.result[col].to_list() == pytest.approx(source_truth_df[col].to_list())
        )

    # Check if all conditions Matches expected result
    assert all(conditions_list) == expected_result

    #check if given columns has distinct values
    distinct_columns = [ "solar_absort", "convection_area"]

    for col in distinct_columns:
        distinct_values = set([x for x in simu1.result[col].to_list() if pd.notna(x)])
        assert len(distinct_values) > 5, f"Column {col} has no distinct values"

    # check if given columns has UNIQUE values
    unique_columns = ["density","volume"] #volume value comes from cross_area
    for col in unique_columns:
        distinct_values = set([x for x in simu1.result[col].to_list() if pd.notna(x)])
        assert len(distinct_values) == 1, f"Column {col} HAS distinct values"
