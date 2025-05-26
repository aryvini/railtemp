import datetime
import time
import warnings
from typing import Dict, Union
import pandas as pd
import pysolar as ps
from scipy import optimize

from railtemp.ParameterValue import (
    AbstractParameterValue,
    ConstantParameterValue,
    RandomParameterValue,
    parameter_value_factory,
)
from railtemp.utils import Cr, Af, Cf, Ef, Kf, hconv, shadowArea_sunArea
from railtemp.utils import shadowArea_sunArea_oringal_CNU
from railtemp.utils import load_section_coordinates


class RailMaterial:
    """
    Create a RailMaterial instance

    Parameters:

    density: density of material [kg/m³] default=7850, float64
    solar_absort: radiation absorptivity of the rail surface [#] (0 to 1),
        default=0.8 float64
    emissivity: emissivity of the rail material [#] (0 to 1), default=0.7,
        float64
    specific_heat: function that defines the heat capacity of the material,
        default=specific heat of steel defined by EN1993-1-2. Around 440
    """

    def __init__(
        self,
        density: AbstractParameterValue = 7850,
        solar_absort: AbstractParameterValue = 0.8,
        emissivity: AbstractParameterValue = 0.7,
        specific_heat: Union[callable, AbstractParameterValue] = Cr,
    ):
        self._density = parameter_value_factory(density)
        self._solar_absort = parameter_value_factory(solar_absort)
        self._emissivity = parameter_value_factory(emissivity)
        self.specific_heat = (
            specific_heat
            if callable(specific_heat)
            else lambda _: parameter_value_factory(specific_heat).get_value()
        )

    @property
    def density(self) -> float:
        value = self._density.get_value()
        if value <= 0:
            raise ValueError("Density must be positive.")
        return value

    @property
    def solar_absort(self) -> float:
        value = self._solar_absort.get_value()
        if not (0 < value <= 1):
            raise ValueError("Solar absorptivity must be between 0 and 1.")
        return value

    @property
    def emissivity(self) -> float:
        value = self._emissivity.get_value()
        if not (0 < value <= 1):
            raise ValueError("Emissivity must be between 0 and 1.")
        return value

    def reinit_parametervalues(self):
        """
        Reinitialize all paramater if they are type RandomParameterValue. Use method RandomParameterValue.reinit()
        """
        for attr in ["_density", "_solar_absort", "_emissivity"]:
            value = getattr(self, attr)
            if isinstance(value, RandomParameterValue):
                value.reinit()
        return None

class Rail:
    """
    Class that defines rail geometric properties and location

    Parameters:
    name: name of the rail cross section, default=UIC42, string;
    azimuth: azimuth of the rail track, between 0 and 180 [degrees], float64;
    lat,long: latitude and longitude of the rail track [degrees], float64;
    elev: sea level altitude of the site [m], float64;
    cross_area: cross section area [m²], float64;
    convection_area: area that exchange heat by convection [m²], flota64;
    radiation_area: area that exchange heat by radiation [m²], float64;
    ambient_emissivity: surroundings emissivity; float64
    material: RailMaterial object

    """

    def __init__(
        self,
        name: str,
        azimuth: AbstractParameterValue,
        lat: AbstractParameterValue,
        long: AbstractParameterValue,
        elev: AbstractParameterValue,
        cross_area: AbstractParameterValue,
        convection_area: AbstractParameterValue,
        radiation_area: AbstractParameterValue,
        ambient_emissivity: AbstractParameterValue,
        material: RailMaterial,
    ):
        if not isinstance(material, RailMaterial):
            raise (Exception("material must be an object of RailMaterial class"))

        self.name = name
        self._azimuth = parameter_value_factory(azimuth)
        self._position = {
            "lat": parameter_value_factory(lat),
            "long": parameter_value_factory(long),
            "elev": parameter_value_factory(elev),
        }
        self._cross_area = parameter_value_factory(cross_area)
        self._convection_area = parameter_value_factory(convection_area)
        self._radiation_area = parameter_value_factory(radiation_area)
        self._ambient_emissivity = parameter_value_factory(ambient_emissivity)
        self._volume = parameter_value_factory(cross_area)
        self.material = material
        self.profile_coordinates = self.__load_section_coordinates()

    @property
    def azimuth(self) -> float:
        value = self._azimuth.get_value()
        if not (0 <= value <= 180):
            raise ValueError("Azimuth must be between 0 and 180 degrees.")
        return value

    @property
    def position(self) -> Dict[str, float]:
        lat = self._position["lat"].get_value()
        long = self._position["long"].get_value()
        elev = self._position["elev"].get_value()
        if not (-90 <= lat <= 90):
            raise ValueError("Latitude must be between -90 and 90 degrees.")
        if not (-180 <= long <= 180):
            raise ValueError("Longitude must be between -180 and 180 degrees.")
        if elev < 0:
            raise ValueError("Elevation must be non-negative.")
        return {"lat": lat, "long": long, "elev": elev}

    @property
    def cross_area(self) -> float:
        value = self._cross_area.get_value()
        if value <= 0:
            raise ValueError("Cross area must be positive.")
        return value

    @property
    def convection_area(self) -> float:
        value = self._convection_area.get_value()
        if value <= 0:
            raise ValueError("Convection area must be positive.")
        return value

    @property
    def radiation_area(self) -> float:
        value = self._radiation_area.get_value()
        if value <= 0:
            raise ValueError("Radiation area must be positive.")
        return value

    @property
    def ambient_emissivity(self) -> float:
        value = self._ambient_emissivity.get_value()
        if not (0 <= value <= 1):
            raise ValueError("Ambient emissivity must be between 0 and 1.")
        return value

    @property
    def volume(self) -> float:
        value = self._volume.get_value()
        if value <= 0:
            raise ValueError("Volume must be positive.")
        return value

    def reinit_parametervalues(self):
        """
        Reinitialize all paramater if they are type RandomParameterValue. Use method RandomParameterValue.reinit()
        """
        for attr in [
            "_azimuth",
            "_cross_area",
            "_convection_area",
            "_radiation_area",
            "_ambient_emissivity",
            "_volume",
        ]:
            value = getattr(self, attr)
            if isinstance(value, RandomParameterValue):
                value.reinit()

        # Handle _position dictionary
        for key, val in self._position.items():
            if isinstance(val, RandomParameterValue):
                val.reinit()

        return None



    def __load_section_coordinates(self):
        """
        method to retrieve X,Y,Z coordinates of a 1 meter long rail track
        """

        return load_section_coordinates(self.name)


class WeatherData:
    """
    Raw data input
    All data must be pandas.Series objects, with same datetime index.

    Parameters:
    Solar radiation: pandas Series with solar radiation measurements in W/m²;
    Wind velocity: Series with wind velocity in m/s;
    Ambient temperature: Series with ambient temperature in Celsius
    timezone of the datetime index. to verify all the timezone available,
        run pytz.all_timezones
    """

    def __init__(
        self,
        solar_radiation,
        ambient_temperature,
        wind_velocity,
        timezone,
    ):
        inputs = (solar_radiation, ambient_temperature, wind_velocity)

        # Check if inputs are pandas Series
        if all([isinstance(input, pd.Series) for input in inputs]):
            pass
        else:
            raise (Exception("all inputs must be pandas.Series object"))

        if isinstance(timezone, datetime.tzinfo):
            pass
        else:
            raise (Exception("timezone must be an datetime.tzinfo object"))

        # Function to check if all datetime index are equal
        def __check_index(series):
            """
            List of Series to check if they have same index
            (series1,series2,seriesN...)

            """

            indexs = [serie.index for serie in series]

            list = [indexs[0].equals(indexs[i]) for i in range(len(indexs))]

            if all(list):
                pass

            else:
                raise (Exception("All index must me equal"))
            return True

        if __check_index((solar_radiation, ambient_temperature, wind_velocity)):
            pass

        # changing pd.Series names and indexes
        # In CNU_create delta time column, the index name must be called Date
        solar_radiation.rename("SR", inplace=True)
        solar_radiation.rename_axis("Date", inplace=True)

        ambient_temperature.rename("Tamb", inplace=True)
        ambient_temperature.rename_axis("Date", inplace=True)

        wind_velocity.rename("Wv", inplace=True)
        wind_velocity.rename_axis("Date", inplace=True)

        # function to join the series in a dataframe
        def __join_series(series):
            return pd.concat(series, axis=1)

        self.SR = solar_radiation
        self.Tamb = ambient_temperature
        self.Wv = wind_velocity
        self.tz = timezone

        series = [self.SR, self.Tamb, self.Wv]

        self.df = __join_series(series)

        return None


class CNU:
    """
    Create a Simu object

    Parameters:
    rail: Rail object
    weather: Weather object

    Methods:
    run: Run the simulation

    """

    def __init__(self, rail: Rail, weather: WeatherData):
        if all([isinstance(rail, Rail), isinstance(weather, WeatherData)]):
            pass
        else:
            raise (Exception("The inputs must be an object of classes Rail and WeatherData"))

        self.rail = rail
        self.weather = weather

        return None
    def reinit_parametervalues(self):
        """
        Reinitialize all paramater if they are type RandomParameterValue. Use method RandomParameterValue.reinit()
        """



    def run(self, Trail_initial):
        """
        Run the simulation

        Parameters:
        Trail_initial: Initial temperature of the rail [C]

        Returns:

        CNU.result dataframe

        """
        self.df = self.weather.df.copy()
        start_time = time.time()

        print("Converting the temperatures to Kelvin")
        self.__celsius_to_kelvin()
        print("Done")

        print("Calculating Hconv")
        self.__calculate_hconv()
        print("Done")

        print("Fetching solar data")
        self.__fetch_solar_data()
        print("Done")

        print("Calculating As")
        self.__calculate_As()
        print("Done")

        print("Creating Delta time Columns")
        self.__create_delta_time_columns()
        print("Done")

        print("Setting initial conditions")
        self.__initial_conditions(Trail_initial)
        print("Done")

        print("Solving model")
        self.__solve()
        print("Done")

        print("Converting temperatures to Celsius")
        self.__kelvin_to_celsius()
        print("Done")

        print(f"Finished in: {datetime.datetime.now()}")
        print(f"Execution time: {time.time() - start_time}")
        print("------------------------------------")
        # print("--- %s seconds ---" % (time.time() - start_time))

        self.result = self.df.copy()
        self.result.set_index("Date", inplace=True)

        return None

    def __celsius_to_kelvin(self):
        data = self.df
        data["Tamb"] = data.apply(lambda x: x["Tamb"] + 273.15, axis=1)

        return None

    def __kelvin_to_celsius(self):
        data = self.df
        data["Tamb"] = data.apply(lambda x: x["Tamb"] - 273.15, axis=1)
        data["Tr_simu"] = data.apply(lambda x: x["Tr_simu"] - 273.15, axis=1)

        return None

    def __calculate_hconv(self):
        data = self.df
        data["Hconv"] = data.apply(lambda x: hconv(x["Wv"]), axis=1)

        return None

    def __fetch_solar_data(self):
        data = self.df
        tz = self.weather.tz
        lat = self.rail.position["lat"]
        long = self.rail.position["long"]
        elev = self.rail.position["elev"]
        data["Date_time"] = data.index.tz_localize(tz)
        data["Sun_azimuth"] = data.apply(
            lambda x: ps.solar.get_azimuth(lat, long, x["Date_time"], elev), axis=1
        )
        data["Sun_altitude"] = data.apply(
            lambda x: ps.solar.get_altitude(lat, long, x["Date_time"], elev), axis=1
        )

        data.drop(["Date_time"], axis=1, inplace=True)

        return None

    def __calculate_As(self):
        data = self.df
        profile = self.rail.profile_coordinates
        rail_azimuth = self.rail.azimuth
        data["As"] = data.apply(
            lambda x: (
                shadowArea_sunArea(profile, x["Sun_azimuth"], x["Sun_altitude"], rail_azimuth)[1]
                if x["Sun_altitude"] > 0
                else 0
            ),
            axis=1,
        )

        return None

    def __calculate_original_CNU_As(self):
        data = self.df
        profile = self.rail.profile_coordinates
        rail_azimuth = self.rail.azimuth
        data["As"] = data.apply(
            lambda x: (
                shadowArea_sunArea_oringal_CNU(
                    profile, x["Sun_azimuth"], x["Sun_altitude"], rail_azimuth
                )[1]
                if x["Sun_altitude"] > 0
                else 0
            ),
            axis=1,
        )

        return None

    def __create_delta_time_columns(self):
        data = self.df
        data.reset_index(inplace=True)
        data["Delta_time"] = 0
        data["Simu_time"] = 0

        for i in range(0, len(list(data.index))):
            if i == 0:
                pass
            else:
                t0 = data.loc[(i - 1)]["Date"]
                ti = data.loc[i]["Date"]
                data.loc[i, "Delta_time"] = (ti - t0).seconds
                data.loc[i, "Simu_time"] = (ti - data.loc[0, "Date"]).seconds

        if len(data["Delta_time"].unique()) > 2:
            warnings.warn(
                "CAUTION: Datetime index error, "
                "time steps are not evenly spaced. "
                "The simulation will continue, but attention is required"
            )

        return None

    def __initial_conditions(self, Trail_initial):
        data = self.df
        # Create Tr_simu column
        data["Tr_simu"] = 0.0

        # Set initial condition to the Rail Temperature
        # Convert the input from Celsius to Kelvin
        data.loc[0, "Tr_simu"] = Trail_initial + 273.15

        return None

    def __solve(self):
        data = self.df

        for i in range(1, len(list(data.index))):
            solar_absort = self.rail.material.solar_absort
            Ac = self.rail.convection_area
            Ar = self.rail.radiation_area
            Er_material = self.rail.material.emissivity
            Er_ambient = self.rail.ambient_emissivity
            Er = Er_material * Er_ambient
            pho = self.rail.material.density
            Cr = self.rail.material.specific_heat
            Vr = self.rail.volume

            def find_Trail_i(Tr_i):
                row = data.loc[i]

                A = Af(solar_absort, row["As"], row["SR"])
                C = Cf(row["Hconv"], Ac, Tr_i, row["Tamb"])
                E = Ef(Ar, Tr_i, row["Tamb"], Er)
                K = Kf(
                    pho, Cr, (Tr_i - 273.15), Vr
                )  # Cr equation is in Celsius, transformation is needed
                fres = (1 / K) * (A - C - E)

                return ((row["Delta_time"] * fres) + data.loc[i - 1]["Tr_simu"]) - Tr_i

            # Minimize the function to find real Tr_simu

            try:
                data.loc[i, "Tr_simu"] = optimize.newton(
                    func=find_Trail_i, x0=273, maxiter=30000, tol=1e-5, x1=400
                )
                # At this point, solution is found.
                # Append the parameter values to the dataframe
                data.loc[i, "solar_absort"] = solar_absort
                data.loc[i, "convection_area"] = Ac
                data.loc[i, "radiation_area"] = Ar
                data.loc[i, "material_emissivity"] = Er_material
                data.loc[i, "ambient_emissivity"] = Er_ambient
                data.loc[i, "density"] = pho
                data.loc[i, "specific_heat"] = Cr(data.loc[i, "Tr_simu"] - 273.15)
                data.loc[i, "volume"] = Vr

            except RuntimeError as e:
                raise Exception(
                    f"Not converged to a solution forTr_simu at index {i} with error: {e}"
                )
        # # reset parameter values
        # self.rail.reinit_parametervalues()
        # self.rail.material.reinit_parametervalues()
        return None

    def __fixed_As(self, Area):
        data = self.df

        if isinstance(Area, ConstantParameterValue):
            data["As"] = Area.get_value()
            return None
        elif isinstance(Area, RandomParameterValue):
            # Apply Area.get_value() for each row in the DataFrame
            data["As"] = data.apply(lambda row: Area.get_value(), axis=1)
        else:
            raise (TypeError)

        return None

    def run_fixed_area(self, Trail_initial, Area: AbstractParameterValue = 0.1):
        """
        Run the simulation with custom definition of As parameter

        Parameters:
        Trail_initial: Initial temperature of the rail [C]
        Area: Area exposed to the sun's incoming radiation [m²]

        Returns:

        None

        """

        Area = parameter_value_factory(Area)

        self.df = self.weather.df.copy()
        start_time = time.time()

        print("Converting the temperatures to Kelvin")
        self.__celsius_to_kelvin()
        print("Done")

        print("Calculating Hconv")
        self.__calculate_hconv()
        print("Done")

        print("Fetching solar data")
        self.__fetch_solar_data()
        print("Done")

        print("Calculating As")
        self.__fixed_As(Area)
        print("Done")

        print("Creating Delta time Columns")
        self.__create_delta_time_columns()
        print("Done")

        print("Setting initial conditions")
        self.__initial_conditions(Trail_initial)
        print("Done")

        print("Solving model")
        self.__solve()
        print("Done")

        print("Converting temperatures to Celsius")
        self.__kelvin_to_celsius()
        print("Done")

        print(f"Finished in: {datetime.datetime.now()}")
        print(f"Execution time: {time.time() - start_time}")
        print("------------------------------------")
        # print("--- %s seconds ---" % (time.time() - start_time))

        self.result = self.df.copy()
        self.result.set_index("Date", inplace=True)

        return None

    def run_original_CNU_area(self, Trail_initial):
        """
        Run the simulation with fixed value of As parameter

        Parameters:
        Trail_initial: Initial temperature of the rail [C]
        Area: Area exposed to the sun's incoming radiation [m²]

        Returns:

        None

        """
        self.df = self.weather.df.copy()
        start_time = time.time()

        print("Converting the temperatures to Kelvin")
        self.__celsius_to_kelvin()
        print("Done")

        print("Calculating Hconv")
        self.__calculate_hconv()
        print("Done")

        print("Fetching solar data")
        self.__fetch_solar_data()
        print("Done")

        print("Calculating As")
        self.__calculate_original_CNU_As()
        print("Done")

        print("Creating Delta time Columns")
        self.__create_delta_time_columns()
        print("Done")

        print("Setting initial conditions")
        self.__initial_conditions(Trail_initial)
        print("Done")

        print("Solving model")
        self.__solve()
        print("Done")

        print("Converting temperatures to Celsius")
        self.__kelvin_to_celsius()
        print("Done")

        print(f"Finished in: {datetime.datetime.now()}")
        print(f"Execution time: {time.time() - start_time}")
        print("------------------------------------")
        # print("--- %s seconds ---" % (time.time() - start_time))

        self.result = self.df.copy()
        self.result.set_index("Date", inplace=True)

        return None
