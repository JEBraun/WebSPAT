# -*- coding: utf-8 -*-
"""
Created on Wed Aug  4 11:39:48 2021

@author: jeb2694
"""
import math
import numpy as np
from math import isnan
from scipy.interpolate import interp1d

def oceanLeftTransects(stationInfo, snap):
    
    duneInt = stationInfo['Dune Line Info']['Dune Line Interpolation']
    
    xi = duneInt[:,0]
    py = duneInt[:,1]
    
    #Set y values (of the duneline) equal to non-existing (NaN) x values
    for i in range(0,len(xi)):
        if np.isnan(xi[i]):
            py[i] = np.nan

    slX = list(stationInfo['Apx. Shoreline']['slX'])
    slY = list(stationInfo['Apx. Shoreline']['slY'])

    #Find the minimum X value of the duneline
    minX = np.nanmin(xi)
    minY = np.nanmin(py)
    maxY = np.nanmax(py)

    #Find the slope of the aproximate shoreline points
     #Find the slope of the aproximate shoreline points
    m = (slY[1]-slY[0])/(slX[1]-slX[0])
    b = slY[0] - (m*slX[0])
    
    #Rewrite Y = mx + b to solve for x (the point at which the aproximate 
        # shoreline intersects the horizon); set the shorelines endpoint equal to x 
    hznY = stationInfo['Horizon Y Value']
    slY[0] = minY
    
    #Adjust the starting point of the apx. shoreline to best compliment the dune line
        #Set the Y coordinate equal to the largest y value of the dune line
   
    slX[1] = (maxY - b)/m
    slY[1] = maxY
    
    #Create a 2x2 array of horizon endpoints (assumes horixon to be flat)
        #End the horizon line when X= minimum X value of the duneline
    
    hznPts = np.zeros((2,2))
    hznPts[0,1] = minY
    hznPts[1,0] = next(n for n in xi if not isnan(n))
    hznPts[1,1] = minY
    
    stationInfo['Horizon Line Endpoints'] = hznPts.tolist()
    
    #Define how far apart to draw transects (in pixels)
    ds = 10
    
    #Generate an array of every (ds)th point between the aproximate shorelines 
       # two X coordinates 
    slTx = np.arange(int(np.min(slY)),int(np.max(slY)),ds)
    
    #Find how many points were created
    slength = len(slTx)
    
    #Determine the least squares polynomial fit coefficient of X and Y of the 
        # apx. shoreline
    coef = np.polyfit(slY, slY, 1)
    
    #Use the coefficient to determine the initioal Y value for each transect
    slCoef = (coef[0] * slTx) + coef[1]

    #For horizontal transects, set the angle to 90 degrees and convert to radians 
    angD = 90
    angR = math.radians(angD)
    
    #Preallocate the arrays for the transect coordiantes (# of transects x 2) 
    xt = np.zeros((slength,2))
    yt = np.zeros((slength,2))
    
    #Iterate through each transect and set temporary values for the 
    #   onshore/offshore boundaries
    for i in range(slength):
        doffshore = 250
        donshore = 250
    
        x0 = slTx[i] + doffshore * math.sin(angR)
        y0 = slCoef[i] - doffshore * math.cos(angR)
    
        x1 = slTx[i] - donshore *math.sin(angR);
        y1 = slCoef[i] + donshore *math.cos(angR);
       
        #Fill the preallocated arrays with each iteration
        xt[i,0] = x0
        xt[i,1] = x1
        
        yt[i,0] = y0
        yt[i,1] = y1
    
    #Round the arrays to the nearest whole number
    xt = np.round(xt)
    yt = np.round(yt)
    
    #Loop through the X and Y points to further define the transect boundaries
    for i in range(0,len(xt)):
        
        #Have all transects start from the vertical axis (x = 0)
        if xt[i,1] > 0 or xt[i,1] < 0:
            xt[i,1] = 0
            
        #Have all transects terminate when intersecting the dune line
        if yt[i,0] == py[int(yt[i,0])]:
            xt[i,0] = xi[int(yt[i,0])]
            xt[np.isnan(xt)] = 0
            
        #Set the uppermost transect equal to the horizon IF it lies above 
            # the horizon initially
        if yt[i,0] < hznY:
            yt[i,0] = hznY
        
        #IF a transect does not intersect the duneline, set it to terminate
            # at the non-NaN minimum X value of the dune line 
        if yt[i,1] < np.nanmin(py):
            xt[i,0] = round(minX)
    
    #Save the X and Y points in dictionaries for return to station setup
    slTransects = {'x':xt, 'y':yt}
    
    stationInfo['Shoreline Transects'] = slTransects
    
    # Update list of used modules
    mod = ['math' , 'numpy', 'scipy']
    mods = stationInfo['Modules Used']
    for n in range(len(mod)):
        if mod[n] not in mods:
            mods.append(mod[n])
    stationInfo['Modules Used'] = mods
    
    return(stationInfo, hznPts)

#######################################
    
def oceanRightTransects(stationInfo, snap):
    
    duneInt = stationInfo['Dune Line Info']['Dune Line Interpolation']
    
    xi = duneInt[:,0]
    py = duneInt[:,1]
    
    #Set y values (of the duneline) equal to non-existing (NaN) x values
    for i in range(0,len(xi)):
        if np.isnan(xi[i]):
            py[i] = np.nan
    
    slX = list(stationInfo['Apx. Shoreline']['slX'])
    slY = list(stationInfo['Apx. Shoreline']['slY'])
        
    slX.sort() # slX[0] = Upper point & slX[1] = Lower point
    slY.sort() # slY[0] = Upper point & sly[1] =  Lower point
    
    # minX = np.nanmin(xi)
    minY = np.nanmin(py)
    maxY = np.nanmax(py)
    
    #Find the slope of the aproximate shoreline points
    m = (slY[1]-slY[0])/(slX[1]-slX[0])
    b = slY[0] - (m*slX[0])
    
    #Rewrite Y = mx + b to solve for x (the point at which the aproximate 
        # shoreline intersects the horizon); set the shorelines endpoint equal to x
    hznY = stationInfo['Horizon Y Value']

    #Adjust the starting point of the apx. shoreline to best compliment the dune line
    #Set the Y coordinate equal to the largest y value of the dune line
    slX[0] = slX[1]
    slY[0] = minY

    slX[1] = (maxY + b)/m
    slY[1] = maxY
    
    
    maxX = np.nanmax(xi) #Find the minimum X value of the duneline
    
    #width and height of snap in pixels 
    w = len(snap[1])
    
    #Define how far apart to draw transects (in pixels)
    ds = 10

    #Create a 2x2 array of horizon endpoints (assumes horixon to be flat)
    #End the horizon line when X= minimum X value of the duneline
    hznPts = np.zeros((2,2))
    hznPts[0,0] = round(maxX)
    hznPts[0,1] = minY
    hznPts[1,0] = w
    hznPts[1,1] = minY
         
    #Generate an array of every (ds)th point between the aproximate shorelines 
       # two X coordinates 
    slTx = np.arange(int(np.min(slX)),int(np.max(slX)),ds)
    
    slength = len(slTx) #Find how many points were created
    
    #Determine the least squares polynomial fit coefficient of X and Y of the 
        # apx. shoreline
    coef = np.polyfit(slX, slY, 1)
    
    #Use the coefficient to determine the initioal Y value for each transect
    slCoef = (coef[0] * slTx) + coef[1]
    
    #For horizontal transects, set the angle to 90 degrees and convert to radians 
    angD = 90
    angR = math.radians(angD)
    
    #Preallocate the arrays for the transect coordiantes (# of transects x 2) 
    xt = np.zeros((slength,2))
    yt = np.zeros((slength,2))
    
    #Iterate through each transect and set temporary values for the 
    #   onshore/offshore boundaries
    for i in range(slength):
        doffshore = 250
        donshore = 250
    
        x0 = slTx[i] + doffshore * math.sin(angR)
        y0 = slCoef[i] - doffshore * math.cos(angR)
    
        x1 = slTx[i] - donshore *math.sin(angR);
        y1 = slCoef[i] + donshore *math.cos(angR);
       
        #Fill the preallocated arrays with each iteration
        xt[i,0] = x0
        xt[i,1] = x1
        
        yt[i,0] = y0
        yt[i,1] = y1
    
    #Round the arrays to the nearest whole number
    xt = np.round(xt)
    yt = np.round(yt)
    
    #Loop through the X and Y points to further define the transect boundaries
    for i in range(0,len(xt)):
        
        if yt[i,0] > maxY:
            yt[i,0] = maxY
            yt[i,1] = maxY
        
        #Have all transects start from the vertical axis (x = 0)
        if xt[i,1] > w or xt[i,1] < w:
            xt[i,1] = w
            
        #Have all transects terminate when intersecting the dune line
        if yt[i,0] == py[int(yt[i,0])]:
            xt[i,0] = xi[int(yt[i,0])]
            xt[np.isnan(xt)] = 0
            
        #Set the uppermost transect equal to the horizon IF it lies above 
            # the horizon initially
        if yt[i,0] < hznY:
            yt[i,0] = hznY
        
        #IF a transect does not intersect the duneline, set it to terminate
            # at the non-NaN minimum X value of the dune line 
        if yt[i,1] < np.nanmin(py):
            xt[i,0] = round(maxX)
            
    #Save the X and Y points in dictionaries for return to station setup
    slTransects = {'x':xt, 'y':yt, }
    
    stationInfo['Shoreline Transects'] = slTransects
    
    # Update list of used modules
    mod = ['math' , 'numpy', 'scipy']
    mods = stationInfo['Modules Used']
    for n in range(len(mod)):
        if mod[n] not in mods:
            mods.append(mod[n])
    stationInfo['Modules Used'] = mods
    
    return(stationInfo, hznPts)

#######################################
    
def oceanForwardTransects(stationInfo, snap):
    
    Di = stationInfo['Dune Line Info']
    duneInt = Di['Dune Line Interpolation']
    
    xi = duneInt[:,0]
    py = duneInt[:,1]
    
    #Set y values (of the duneline) equal to non-existing (NaN) x values
    for i in range(0,len(py)):
        if np.isnan(py[i]):
            xi[i] = np.nan
            
    slApx = stationInfo['Apx. Shoreline']
    slX = list(slApx['slX'])
    slY = list(slApx['slY'])

    #Adjust the starting point of the apx. shoreline to best compliment the dune line
        #Set the Y coordinate equal to the largest y value of the dune line
        #Find the slope of the aproximate shoreline points
    m = (slY[1]-slY[0])/(slX[1]-slX[0])
    b = slY[0] - (m*slX[0])
    
    slX[0] = 0
    slY[0] = (m*slX[0])+b
    slX[1] = np.nanmax(xi)
    slY[1] = (m*slX[1])+b
    
    #Create a 2x2 array of horizon endpoints (assumes horixon to be flat)
        #End the horizon line when X= minimum X value of the duneline
    hznY = stationInfo['Horizon Y Value']
    hznPts = np.zeros((2,2))
    hznPts[0,0] = 0
    hznPts[0,1] = hznY
    hznPts[1,0] = np.nanmax(xi)
    hznPts[1,1] = hznY
    
    
    #Define how far apart to draw transects (in pixels)
    ds = 10
        
    #Generate an array of every (ds)th point between the aproximate shorelines 
       # two X coordinates 
    slTx = np.arange(int(np.min(slX)),int(np.max(slX)),ds)
    
    #Find how many points were created
    slength = len(slTx)
    
    #Determine the least squares polynomial fit coefficient of X and Y of the 
        # apx. shoreline
    coef = np.polyfit(slX, slY, 1)
    
    #Use the coefficient to determine the initioal Y value for each transect
    slCoef = (coef[0] * slTx) + coef[1]

    #For horizontal transects, set the angle to 90 degrees and convert to radians 
    angD = 0
    angR = math.radians(angD)
    
    #Preallocate the arrays for the transect coordiantes (# of transects x 2) 
    xt = np.zeros((slength,2))
    yt = np.zeros((slength,2))
    
    #Iterate through each transect and set temporary values for the 
    #   onshore/offshore boundaries
    for i in range(slength):
        doffshore = 250
        donshore = 250
    
        x0 = slTx[i] + doffshore * math.sin(angR)
        y0 = slCoef[i] - doffshore * math.cos(angR)
    
        x1 = slTx[i] - donshore *math.sin(angR);
        y1 = slCoef[i] + donshore *math.cos(angR);
       
        #Fill the preallocated arrays with each iteration
        xt[i,0] = x0
        xt[i,1] = x1
        
        yt[i,0] = y0
        yt[i,1] = y1
    
    #Round the arrays to the nearest whole number
    xt = np.round(xt)
    yt = np.round(yt)
    
    #Loop through the X and Y points to further define the transect boundaries
    for i in range(0,slength):
        
        #Have all transects start from the vertical axis (x = 0)
        if yt[i,0] > hznY or yt[i,0] < hznY:
            yt[i,0] = hznY
    
        #Have all transects terminate when intersecting the dune line
        if xt[i,0] == xi[int(xt[i,0])]:
            yt[i,1] = py[int(xt[i,0])]
            yt[np.isnan(yt)] = 0
            
        if xt[i,0] < np.nanmin(xi):
            yt[i,1] = np.nanmin(py)
     
    #Save the X and Y points in dictionaries for return to station setup
    slTransects = {'x':xt, 'y':yt}
    
    stationInfo['Shoreline Transects'] = slTransects
    
    # Update list of used modules
    mod = ['math' , 'numpy', 'scipy']
    mods = stationInfo['Modules Used']
    for n in range(len(mod)):
        if mod[n] not in mods:
            mods.append(mod[n])
    stationInfo['Modules Used'] = mods
    
    return(stationInfo, hznPts)

#######################################

def makeRecTrans(stationInfo, img, rmb, thresh_otsu):
    
    transects = stationInfo['Rectified Transects']
    xt = np.flipud(transects['x'])
    yt = np.flipud(transects['y'])
    
    w = len(img[1])-1
    
    tInterps = [0]*len(xt)
    for i in range(0, len(xt)):
        p1 = (xt[i,0],xt[i,1])
        p2 = (yt[i,0],yt[i,1])
        interp = interp1d(p1, p2, bounds_error = False)
        x = np.arange(0, w , 1)
        y = np.round(interp(x))
        z = np.arange(0, w)
        z[:] = 0
        tInterps[i] = np.vstack((x,y,z)).T
    
    exc = {0}
    for i in range(0, len(tInterps)):
        exc.clear()
        for k in range(0, len(tInterps[i])):
            if math.isnan(tInterps[i][k,1]):
                exc.add(k)
        cut = [v for j, v in enumerate(tInterps[i]) if j not in exc] 
        tInterps[i] = np.asarray(cut)
    
    for i in range(0, len(tInterps)):
        for j in range(0, len(tInterps[i])):
            x = int(tInterps[i][j][0])
            y = int(tInterps[i][j][1])
            tInterps[i][j][2] = rmb[y,x]
    
    
    nearestVal = [0]*len(tInterps)
    absDiff = lambda list_value : abs(list_value - thresh_otsu)
    
    for i in range(0,len(tInterps)):
        nearestVal[i] = min(tInterps[i][:,2], key=absDiff)
    
        
    nearThresh = [0]*len(tInterps)
    buffer1 = (float(thresh_otsu) * 1)
    exc.clear()
    for i in range(0,len(tInterps)):
        if abs((buffer1 + thresh_otsu)) > abs(nearestVal[i]) > abs((buffer1 - thresh_otsu)):
            pass
        else:
            nearThresh[i] = np.nan
            exc.add(i)   
        
    xPts = []
    yPts = []
    for i in range(0, len(nearestVal)):
        for j in range(0, len(tInterps[i])):
            if nearestVal[i] == tInterps[i][j][2]:
                xPts.append(tInterps[i][j][0])
                yPts.append(tInterps[i][j][1])
                
    xPts = [v for j, v in enumerate(xPts) if j not in exc]
    yPts = [v for j, v in enumerate(yPts) if j not in exc]
    exc.clear()           
    
    areaAvg = [0]*len(xPts)
    
    sample = np.zeros((11,11))
    
    for i in range(0,len(xPts)):
        orginX = int(xPts[i])
        orginY = int(yPts[i])
        xBounds = range(orginX - 5, orginX + 6)
        yBounds = range(orginY - 5, orginY + 6)
        try:
            for j in yBounds:
                a = j - orginY
                for k in xBounds:
                    b = k - orginX
                    sample[a][b] = rmb[j][k]
        except:
            exc.add(i)
        areaAvg[i] = np.mean(sample)
    
    buffer2 = (float(thresh_otsu) * 1)        
    for i in range(0,len(xPts)):
        if abs((buffer2 + thresh_otsu)) > abs(areaAvg[i]) > abs((buffer2 - thresh_otsu)):
            pass
        else:
            exc.add(i)
        
    xPts = [v for j, v in enumerate(xPts) if j not in exc]
    yPts = [v for j, v in enumerate(yPts) if j not in exc]    
    
    # Update list of used modules
    mod = ['math' , 'numpy', 'scipy']
    mods = stationInfo['Modules Used']
    for n in range(len(mod)):
        if mod[n] not in mods:
            mods.append(mod[n])
    stationInfo['Modules Used'] = mods
    
    return(xPts, yPts)