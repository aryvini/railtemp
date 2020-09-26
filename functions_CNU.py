
import numpy as np
import pandas as pd
from math import *
from scipy.spatial import ConvexHull, convex_hull_plot_2d


#Projection of the points based on solar azimute and elevation

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
    Evaluate the shadowArea and the sunArea based on the spatial coordinates of the rail, azimtuh and elevation of the sun
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

def Af(SA,As,SolarRadiation):
   
    return SA*As*SolarRadiation

def Cf(hc,Ac,Trail,Tsky):
    return hc*Ac*(Trail-Tsky)
    
def Ef(Ar,Trail,Tamb):
    Tsky = Tamb
    return Er*Sig*Ar*(pow(Trail,4)-pow((Tsky),4))
    

def Kf(Trail):
    return pho*Cr(Trail)*Vr







