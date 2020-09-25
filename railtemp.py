import pandas as pd
import numpy as np
from math import *
import pytz



class Rail:
    ''' 
    Class that defines rail geometric properties and location
     
    Params:
    name: name of the rail cross section, default=UIC42, string;
    azimuth: azimuth of the rail track, between 0 and 180 [degrees], float64;
    lat,long: latitude and longitude of the rail track [degrees], float64;
    elev: sea level altitude of the site [m], float64;
    cross_area: cross section area [m²], float64;
    convection_area: area that exchange heat by convection [m²], flota64;
    radiation_area: area that exchange heat by radiation [m²], float64;
    material: RailMaterial object
        
    '''
    def __init__(self,name,azimuth,lat,long,elev,cross_area,convection_area,radiation_area,material):
        
        if isinstance(material,RailMaterial):
            pass
        else:
            raise(Exception('Invalid rail material'))
        if 0<=azimuth<=180:
            pass
        else:
            raise(Exception('invalid azimuth It must be between 0-180'))
        
        
        
        self.name = name
        self.azimuth = azimuth
        self.position = (lat,long,elev)
        self.cross_area = cross_area
        self.convection_area = convection_area
        self.radiation_area = radiation_area
        self.material = material
        self.volume = self.cross_area
        self.profile_coordinates = self.__load_section_coordinates()
        
        return None

    def __load_section_coordinates(self):
        '''
        method to retrieve X,Y,Z coordinates of a 1 meter long rail track
        '''

        file = str('sections/' + self.name + '.csv')

        try:
           return pd.read_csv(file)
        except:
            raise(Exception('Rail profile name not found in database'))


class RailMaterial:
    '''
    Create a RailMaterial instance

    params:

    density: density of material [kg/m³] default=7850, float64
    solar_absort: radiation absorptivity of the rail surface [#] (0 to 1), default=0.8 float64
    emissivity: emissivity of the rail material [#] (0 to 1), default=0.7, float64
    specific_heat: function that defines the heat capacity of the material, default=specific heat of steel defined by EN1993-1-2
    '''

    def __Cr(temperature):
        '''
        Specific heat depending on the temperature according to EN1993-1-2

        Params:
        temperature [Celsius], float64

        Returns:
        specific heat [J/ (kg K)]
        '''
        t = temperature
        
        if t >= 20:
            
            return (425+7.73e-1*t) - (1.69e-3 * pow(t,2)) + (2.22e-6 * pow(t,3))
        else:
            return Cr(20)


    def __init__(self,density=7850,solar_absort=0.8,emissivity=0.7, specific_heat=__Cr):

        
        if all([(0 < solar_absort <= 1),(0 < emissivity <= 1)]):
        
            pass
        else:
            raise(Exception('Physical parameter error'))
              
        self.density = density
        self.solar_absort = solar_absort
        self.emissivity = emissivity
        self.specific_heat = specific_heat

                        
class InputData:
    '''
    Raw data input
    All data must be pandas.Series objects, with same datetime index.

    Params:
    Solar radiation: pandas Series with solar radiation measurements in W/m²;
    Wind velocity: Series with wind velocity in m/s;
    Ambient temperature: Series with ambient temperature in Celsius

    '''



    def __init__(self,solar_radiation,ambient_temperature,wind_velocity):



        inputs = (solar_radiation,ambient_temperature,wind_velocity)

        #Check if inputs are pandas Series
        if all([isinstance(input,pd.Series) for input in inputs]):
            pass
        else:
            raise(Exception('all inputs must be pandas.Series object'))



        #Function to check if all datetime index are equal
        def __check_index(series):
            '''
            List of Series to check if they have same index
            (series1,series2,seriesN...)

            '''

            indexs = [serie.index for serie in series]

            list = [indexs[0].equals(indexs[i]) for i in range(len(indexs))]

            if all(list):
                pass
                
            else:
                raise(Exception('All index must me equal'))
            return True

        if __check_index((solar_radiation,ambient_temperature,wind_velocity)):
            pass

        #changing pd.Series names
        solar_radiation.rename('SR',inplace=True)
        ambient_temperature.rename('Tamb',inplace=True)
        wind_velocity.rename('Wv',inplace=True)

        
        #function to join the series in a dataframe
        def __join_series(series):

            return pd.concat(series,axis=1)    

        self.SR = solar_radiation
        self.Tamb = ambient_temperature
        self.Wv = wind_velocity

        series = [self.SR,self.Tamb,self.Wv]

        self.df = __join_series(series)


        return None

        


class Simu:

    def __init__(self,rail,weather):
        


        return



