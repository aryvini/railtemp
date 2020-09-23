import pandas as pd
import numpy as np
from math import *



class Rail:
    ''' 
    Class that defines rail geometric properties and location
     
    Params:
    name: name of the rail cross section, default=UIC42, string;
    azimuth: azimuth of the rail track, between 0 and 180 [degrees], float64;
    lat,long: latitude and longitude of the rail track [degrees], float64;
    cross_area: cross section area [m²], float64;
    convection_area: area that exchange heat by convection [m²], flota64;
    radiation_area: area that exchange heat by radiation [m²], float64;
    material: RailMaterial object
        
    '''
    def __init__(self,name,azimuth,lat,long,cross_area,convection_area,radiation_area,material):
        
        if isinstance(material,RailMaterial):
            pass
        else:
            print('invalid rail material')
            return
        if 0<=azimuth<=180:
            pass
        else:
            print('invalid azimuth. It must be between 0-180')
            return
        
        
        
        self.name = name
        self.azimuth = azimuth
        self.position = (lat,long)
        self.cross_area = cross_area
        self.convection_area = convection_area
        self.radiation_area = radiation_area
        self.material = material
        self.volume = self.cross_area
        
        pass

    


        


class RailMaterial:
    '''
    Class to define rail material properties
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
        '''
        Create a RailMaterial instance

        params:

        density: density of material [kg/m³] default=7850, float64
        solar_absort: radiation absorptivity of the rail surface [#] (0 to 1), default=0.8 float64
        emissivity: emissivity of the rail material [#] (0 to 1), default=0.7, float64
        specific_heat: function that defines the heat capacity of the material, default=specific heat of steel defined by EN1993-1-2
        '''

       
        if all([(0 < solar_absort <= 1),(0 < emissivity <= 1)]):
        
            pass
        else:
            print('Physical parameter error')

            return

  
        self.density = density
        self.solar_absort = solar_absort
        self.emissivity = emissivity
        self.specific_heat = specific_heat

             
            



class Simu:

    def __init__(self):
        return

class InputData:


    def __init__(self):

        return

