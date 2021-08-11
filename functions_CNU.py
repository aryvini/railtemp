
import numpy as np
import pandas as pd
from math import *
from scipy.spatial import ConvexHull, convex_hull_plot_2d
import scipy.constants


#Projection of the points based on solar azimuth and elevation

def project_point(x,y,z,azi,elev):
    """ Project on XY plane a spatial point considering a azimuth and elevation of the sun

    params: 
    x,y,z (float) spatial coordinate of the point
    azi (degree) azimuth of the projection vector
    elev (degree) evation of the projection vector

    returns: [xp,yp] projected coordinates
    """
    
    #transform the angle to radians
    azi = radians(azi)
    elev = radians(elev)
    
    xp = -(sin(azi)/tan(elev))*z+x
    yp = -(cos(azi)/tan(elev))*z+y
    
    return [xp,yp]


def shadowArea_sunArea(input_df,sunAzimuth,sunElevation,railAzimuth):
    """
    Evaluate the shadowArea and the sunArea based on the spatial coordinates of the rail, azimuth and elevation of the sun
    The area of projected points is calculated using scipy.spatial.ConvexHull 
    args:
    input_df (Pandas Dataframe) containing ['X','Y','Z'] columns as coordinates of 1 meter of railway profile
    sunAzimuth (degrees) of the sun
    sunElevation (degrees) of the sun
    railAzimuth (degrees) of the rail

    returns:
    [shadowArea, sunArea]

    """
    coord = input_df

    eqAzimtuth = sunAzimuth - railAzimuth
    
    coord['xp'] = coord.apply(lambda k: project_point(k['X'],k['Y'],k['Z'],eqAzimtuth,sunElevation)[0],axis=1)
    coord['yp'] = coord.apply(lambda k: project_point(k['X'],k['Y'],k['Z'],eqAzimtuth,sunElevation)[1],axis=1)
    
    points = coord[['xp','yp']].to_numpy()
    
    hull = ConvexHull(points)
    
    shadowArea = hull.volume
    sunArea = shadowArea*sin(radians(sunElevation))
    
    return [shadowArea,sunArea]

## Defining the standard Hconv equation
def hconv(Wv):
    '''
    Equation to calculate the convection coefficient based on the wind velocity.

    params:
    Wv: wind velocity [m/s], float64.

    returns:
    Hc, float64

    '''

    if Wv<=5:
        return (5.6+4*Wv)
    else:
        return (7.2*pow(Wv,0.78))


## Decomposing the model into part-functions so help the solving process

def Af(SA,As,SR):
    ''' 
    Incoming Energy part of the balance equation

    Params:
    SA: Solar Absorptivity of the material [#], float64
    As: Area that receive energy from the sun, [m²], float64
    SR: Incoming solar radiation [W/m²], float64

    Return:

    SA*As*SR
    '''

    return SA*As*SR

def Cf(hc,Ac,Trail,Tamb):
    '''
    Convection part of the balance equation

    Params:
    hc: Convection coefficient [W/m²K] float64
    Ac: Area that exchange heat by convections [m²]
    Trail: Rail temperature to be solved [C]
    Tamb: Ambient temperature [C]
    
    Returns:
    hc*Ac*(Trail-Tamb)
    '''

    return hc*Ac*(Trail-Tamb)
    
def Ef(Ar,Trail,Tamb,Er):
    '''
    Emitting radiation part of the balance equation

    Params:
    Ar: Area that emitts radiation [m²]
    Trail: Rail temperature to be solved [C]
    Tamb: Ambient temperature [C]
    Er: Resultand Emissivity

    Returns:

    Er*Sig*Ar*(pow(Trail,4)-pow((Tamb),4))
    '''
    Sig = scipy.constants.Stefan_Boltzmann

    return Er*Sig*Ar*(pow(Trail,4)-pow((Tamb),4))
    

def Kf(pho,Cr,Trail,Vr):
    '''
    Right part of the balance equation
    Params:
    pho: Density of the rail material
    Cr: Heat capacity function of the material
    Trail: Rail temperature to be solved [C]
    Vr: Volume of the rail segment
    
    Returns:
    pho*Cr(Trail)*Vr
    '''

    return pho*Cr(Trail)*Vr

def Cr(temperature):
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






