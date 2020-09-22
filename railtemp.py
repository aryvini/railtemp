import pandas as pd
import numpy as np
from math import *



class Rail:
    ''' 
    Class that defines rail geometric properties and location
    '''
    def __init__(self):
        return


class RailMaterial:
    '''
    Class to define rail material properties
    '''

    def __Cr(temperature):
        '''
        Specific heat deppeding on the temperature according to EN1993-1-2

        params:
        temperature [Celsius], float64

        returns:
        specific heat [J/ (kg K)]
        '''
        t = temperature
        
        if t >= 20:
            
            return (425+7.73e-1*t) - (1.69e-3 * pow(t,2)) + (2.22e-6 * pow(t,3))
        else:
            return Cr(20)

    def __init__(self,density=7850,solar_absort=0.8,emissivity=0.7, specific_heat=__Cr):
        '''
        Initiante a RailMaterial instance

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

