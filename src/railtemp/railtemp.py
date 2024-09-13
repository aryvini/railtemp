import pandas as pd
import numpy as np
from math import *
import pytz
import datetime
import pysolar as ps
import time
from scipy import optimize
import os
import sys
import warnings

from railtemp.utils import *

package_directory = os.path.dirname(os.path.abspath(__file__))






class Rail:
    ''' 
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
        
    '''
    def __init__(self,name,azimuth,lat,long,elev,cross_area,convection_area,radiation_area,ambient_emissivity,material):
        
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
        self.position = {'lat':lat,'long':long,'elev':elev}
        self.cross_area = cross_area
        self.convection_area = convection_area
        self.radiation_area = radiation_area
        self.ambient_emissivity = ambient_emissivity
        self.material = material
        self.volume = self.cross_area
        self.profile_coordinates = self.__load_section_coordinates()
        
        return None

    def __load_section_coordinates(self):
        '''
        method to retrieve X,Y,Z coordinates of a 1 meter long rail track
        '''
        # sections_dir = package_directory+'/../../sections/'
        sections_dir = './sections/'
        file = str(sections_dir + self.name + '.csv')
        

        try:
           return pd.read_csv(file)
        except:
            print(file)
            raise(Exception('Rail profile name not found in database'))


class RailMaterial:
    '''
    Create a RailMaterial instance

    Parameters:

    density: density of material [kg/m³] default=7850, float64
    solar_absort: radiation absorptivity of the rail surface [#] (0 to 1), default=0.8 float64
    emissivity: emissivity of the rail material [#] (0 to 1), default=0.7, float64
    specific_heat: function that defines the heat capacity of the material, default=specific heat of steel defined by EN1993-1-2
    '''

    def __init__(self,density=7850,solar_absort=0.8,emissivity=0.7, specific_heat=Cr):

        
        if all([(0 < solar_absort <= 1),(0 < emissivity <= 1)]):
        
            pass
        else:
            raise(Exception('Physical parameter error'))
              
        self.density = density
        self.solar_absort = solar_absort
        self.emissivity = emissivity
        self.specific_heat = specific_heat

                        
class WeatherData:
    '''
    Raw data input
    All data must be pandas.Series objects, with same datetime index.

    Parameters:
    Solar radiation: pandas Series with solar radiation measurements in W/m²;
    Wind velocity: Series with wind velocity in m/s;
    Ambient temperature: Series with ambient temperature in Celsius
    timezone of the datetime index. to verify all the timezone available, run pytz.all_timezones
    '''



    def __init__(self,solar_radiation,ambient_temperature,wind_velocity,timezone):



        inputs = (solar_radiation,ambient_temperature,wind_velocity)

        #Check if inputs are pandas Series
        if all([isinstance(input,pd.Series) for input in inputs]):
            pass
        else:
            raise(Exception('all inputs must be pandas.Series object'))

        if isinstance(timezone,datetime.tzinfo):
            pass
        else:
            raise(Exception('timezone must be an datetime.tzinfo object'))



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

        #changing pd.Series names and indexes
        #In CNU_create delta time column, the index name must be called Date
        solar_radiation.rename('SR',inplace=True)
        solar_radiation.rename_axis('Date',inplace=True)

        ambient_temperature.rename('Tamb',inplace=True)
        ambient_temperature.rename_axis('Date',inplace=True)

        wind_velocity.rename('Wv',inplace=True)
        wind_velocity.rename_axis('Date',inplace=True)

        
        #function to join the series in a dataframe
        def __join_series(series):

            return pd.concat(series,axis=1)    

        self.SR = solar_radiation
        self.Tamb = ambient_temperature
        self.Wv = wind_velocity
        self.tz = timezone 

        series = [self.SR,self.Tamb,self.Wv]

        self.df = __join_series(series)


        return None

        


class CNU:
    '''
    Create a Simu object

    Parameters:
    rail: Rail object
    weather: Weather object

    Methods:
    run: Run the simulation

    '''

    def __init__(self,rail,weather):


        if all([isinstance(rail,Rail),isinstance(weather,WeatherData)]):
            pass
        else:
            raise(Exception('The inputs must be an object of classes Rail and WeatherData'))



        self.rail = rail
        self.weather = weather
        
        return None

    def run(self,Trail_initial):
        '''
        Run the simulation
        
        Parameters:
        Trail_initial: Initial temperature of the rail [C]

        Returns:

        CNU.result dataframe

        '''
        self.df = self.weather.df.copy()
        start_time = time.time()


        print('Converting the temperatures to Kelvin')
        self.__celsius_to_kelvin()
        print('Done')

        print('Calculating Hconv')
        self.__calculate_hconv()
        print('Done')

        print('Fetching solar data')
        self.__fetch_solar_data()
        print('Done')

        print('Calculating As')
        self.__calculate_As()
        print('Done')

        print('Creating Delta time Columns')
        self.__create_delta_time_columns()
        print('Done')

        print('Setting initial conditions')
        self.__initial_conditions(Trail_initial)
        print('Done')


        print('Solving model')
        self.__solve()
        print('Done')

        print('Converting temperatures to Celsius')
        self.__kelvin_to_celsius()
        print('Done')


        print(f'Finished in: {datetime.datetime.now()}')
        print(f'Execution time: {time.time() - start_time}')
        print('------------------------------------')
        #print("--- %s seconds ---" % (time.time() - start_time))
        

        self.result = self.df.copy()
        self.result.set_index('Date',inplace=True)


        return None

    
    def __celsius_to_kelvin(self):
        
        data = self.df
        data['Tamb'] = data.apply(lambda x: x['Tamb']+273.15, axis=1)

        return None

    def __kelvin_to_celsius(self):
        
        data = self.df
        data['Tamb'] = data.apply(lambda x: x['Tamb']-273.15, axis=1)
        data['Tr_simu'] = data.apply(lambda x: x['Tr_simu']-273.15, axis=1)

        return None

    
    def __calculate_hconv(self):

        data = self.df
        data['Hconv'] = data.apply(lambda x: hconv(x['Wv']),axis=1)

        return None

    def __fetch_solar_data(self):

        data = self.df
        tz = self.weather.tz
        lat = self.rail.position['lat']
        long = self.rail.position['long']
        elev = self.rail.position['elev']
        data['Date_time'] = data.index.tz_localize(tz)
        data['Sun_azimuth'] = data.apply(lambda x: ps.solar.get_azimuth(lat,long,x['Date_time'],elev),axis=1)
        data['Sun_altitude'] = data.apply(lambda x: ps.solar.get_altitude(lat,long,x['Date_time'],elev),axis=1)

        data.drop(['Date_time'],axis=1,inplace=True)

        return None
    
    def __calculate_As(self):

        data = self.df
        profile = self.rail.profile_coordinates
        rail_azimuth = self.rail.azimuth
        data['As'] = data.apply(lambda x: shadowArea_sunArea(profile,x['Sun_azimuth'],x['Sun_altitude'],rail_azimuth)[1] if x['Sun_altitude']>0 else 0,axis=1)

        return None

    def __calculate_original_CNU_As(self):

        data = self.df
        profile = self.rail.profile_coordinates
        rail_azimuth = self.rail.azimuth
        data['As'] = data.apply(lambda x: shadowArea_sunArea_oringal_CNU(profile,x['Sun_azimuth'],x['Sun_altitude'],rail_azimuth)[1] if x['Sun_altitude']>0 else 0,axis=1)

        return None

    def __create_delta_time_columns(self):

        data = self.df
        data.reset_index(inplace=True)
        data['Delta_time'] = 0
        data['Simu_time'] = 0

        for i in range(0,len(list(data.index))):
            if i == 0:
                pass
            else:
                t0 = data.loc[(i-1)]['Date']
                ti = data.loc[i]['Date']
                data.loc[i,'Delta_time'] = (ti-t0).seconds
                data.loc[i,'Simu_time'] = (ti-data.loc[0,'Date']).seconds

        if len(data['Delta_time'].unique()) > 2:
            warnings.warn('CAUTION: Datetime index error, time steps are not evenly spaced. The simulation will continue, but attention is required')
            #pass
            #raise(Exception('Datetime index error, time steps are not evenly spaced'))

        return None

    def __initial_conditions(self,Trail_initial):

        data = self.df
        #Create Tr_simu column
        data['Tr_simu'] = 0

        #Set initial condition to the Rail Temperature
        #Convert the input from Celsius to Kelvin
        data.loc[0,'Tr_simu'] = (Trail_initial+273.15)

        return None

    def __solve(self):

        data = self.df
        solar_absort = self.rail.material.solar_absort
        Ac = self.rail.convection_area
        Ar = self.rail.radiation_area
        Er = self.rail.material.emissivity * self.rail.ambient_emissivity
        pho = self.rail.material.density
        Cr = self.rail.material.specific_heat
        Vr = self.rail.volume


        for i in range(1,len(list(data.index))):
            
            def find_Trail_i(Tr_i):
                row = data.loc[i]
                
                A = Af(solar_absort,row['As'],row['SR'])
                C = Cf(row['Hconv'],Ac,Tr_i,row['Tamb'])
                E = Ef(Ar,Tr_i,row['Tamb'],Er)
                K = Kf(pho,Cr,(Tr_i-273.15),Vr) #Cr equation is in Celsius, transformation is needed 
                fres = (1/K)*(A-C-E)

                return (((row['Delta_time']*fres) + data.loc[i-1]['Tr_simu'])-Tr_i)

            #Minimize the function to find real Tr_simu 

            try:
                data.loc[i,'Tr_simu'] = optimize.newton(func=find_Trail_i,x0=273,maxiter=30000,tol=1e-5,x1=400)
            except:
                raise(Exception('Not converged to a solution'))



        return None


    def __fixed_As(self,Area):
        data = self.df

        data['As'] = Area

        return None

    def run_fixed_area(self, Trail_initial,Area=0.1):
        '''
        Run the simulation with fixed value of As parameter
        
        Parameters:
        Trail_initial: Initial temperature of the rail [C]
        Area: Area exposed to the sun's incoming radiation [m²]

        Returns:
        
        None

        '''
        self.df = self.weather.df.copy()
        start_time = time.time()


        print('Converting the temperatures to Kelvin')
        self.__celsius_to_kelvin()
        print('Done')

        print('Calculating Hconv')
        self.__calculate_hconv()
        print('Done')

        print('Fetching solar data')
        self.__fetch_solar_data()
        print('Done')

        print('Calculating As')
        self.__fixed_As(Area)
        print('Done')

        print('Creating Delta time Columns')
        self.__create_delta_time_columns()
        print('Done')

        print('Setting initial conditions')
        self.__initial_conditions(Trail_initial)
        print('Done')


        print('Solving model')
        self.__solve()
        print('Done')

        print('Converting temperatures to Celsius')
        self.__kelvin_to_celsius()
        print('Done')


        print(f'Finished in: {datetime.datetime.now()}')
        print(f'Execution time: {time.time() - start_time}')
        print('------------------------------------')
        #print("--- %s seconds ---" % (time.time() - start_time))
        

        self.result = self.df.copy()
        self.result.set_index('Date',inplace=True)


        return None

    def run_original_CNU_area(self, Trail_initial):
        '''
        Run the simulation with fixed value of As parameter
        
        Parameters:
        Trail_initial: Initial temperature of the rail [C]
        Area: Area exposed to the sun's incoming radiation [m²]

        Returns:
        
        None

        '''
        self.df = self.weather.df.copy()
        start_time = time.time()


        print('Converting the temperatures to Kelvin')
        self.__celsius_to_kelvin()
        print('Done')

        print('Calculating Hconv')
        self.__calculate_hconv()
        print('Done')

        print('Fetching solar data')
        self.__fetch_solar_data()
        print('Done')

        print('Calculating As')
        self.__calculate_original_CNU_As()
        print('Done')

        print('Creating Delta time Columns')
        self.__create_delta_time_columns()
        print('Done')

        print('Setting initial conditions')
        self.__initial_conditions(Trail_initial)
        print('Done')


        print('Solving model')
        self.__solve()
        print('Done')

        print('Converting temperatures to Celsius')
        self.__kelvin_to_celsius()
        print('Done')


        print(f'Finished in: {datetime.datetime.now()}')
        print(f'Execution time: {time.time() - start_time}')
        print('------------------------------------')
        #print("--- %s seconds ---" % (time.time() - start_time))
        

        self.result = self.df.copy()
        self.result.set_index('Date',inplace=True)


        return None








