import pytest
from railtemp.railtemp import *



@pytest.mark.parametrize("input_data, expected_result", [
    ('./tests/artifacts/input_data.csv', True),
    ('./tests/artifacts/invalid_data.csv', False),
])
def test_simulation(input_data, expected_result):

    results_data = f'./tests/artifacts/results.csv'


    df = pd.read_csv(input_data)  # import csv file
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)

    steel = RailMaterial(density=7850, solar_absort=0.8, emissivity=0.7)
    UIC54 = Rail(name='UIC54',
                    azimuth=93, lat=41.482628, long=-7.183741, elev=220,
                    cross_area=7.16e-3, convection_area=430.46e-3, radiation_area=430.46e-3,
                    ambient_emissivity=0.5, material=steel)

    day1 = WeatherData(solar_radiation=df['SR'],
                        wind_velocity=df['Wv_avg'],
                        ambient_temperature=df['TA'],
                        timezone=pytz.timezone('Europe/Lisbon'))

    simu1 = CNU(rail=UIC54, weather=day1)

    simu1.run(Trail_initial=23)

    res_df = pd.read_csv(results_data)
    res_df['Date'] = pd.to_datetime(res_df['Date'])
    res_df.set_index('Date', inplace=True)

    assert set(res_df.columns.to_list()) == set(simu1.result.columns.tolist())

    # Conditions list
    conditions_list = []
    for col in simu1.result.columns:
        conditions_list.append(simu1.result[col].to_list() == pytest.approx(res_df[col].to_list()))

    # Check if all conditions Matches expected result
    assert all(conditions_list) == expected_result


