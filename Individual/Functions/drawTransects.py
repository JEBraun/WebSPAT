# -*- coding: utf-8 -*-
"""
Created on Mon Aug  2 14:03:46 2021

@author: braunj
"""
#Import the required librarys
import ctypes
import numpy as np
import matplotlib.pyplot as plt
import Functions.plotFigures as plot
import Functions.makeTransects as make

#Define script as a function to be called from the station_setup code
def imageTransects(stationInfo, snap):
    
    stationname = stationInfo['Station Name']
    
    #get the dimensions (resolution) of the snapshot
    w = len(snap[1])
    h = len(snap)
    
    #Define the paramaters of an instructional dialogue box
    title = 'Define Horizon'
        
    text = 'Select a point just along/beneath the horizon.'
    
    #"OK" button
    MB_OK = 0x0
    #Information Icon
    ICON_INFO = 0x40
    #Set the box to open above all other windows 
    WIN_TOP = 0x1000
    
    #Call the dialouge box with ctypes; https://docs.python.org/3/library/ctypes.html
    ctypes.windll.user32.MessageBoxW(0, text, title, MB_OK | ICON_INFO | WIN_TOP)
    
    #Display a plot that shows the snapshot
    plt.imshow(snap, interpolation='nearest')
    plt.title('Click a Point Just Below the Horizon', fontweight ="bold")
    #Set axis limts equal to the resolution of the snapshot
    plt.xlim(0, w)
    plt.ylim(h, 0)
    
    #Use matplotlib's ginput function to save "n" number of mouse click coordinates
        #https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.ginput.html
    hznPt = plt.ginput(n = 1, show_clicks = True, mouse_add = 1)
    
    #Round the horizon point to the nearest whole number
    hznY = round(hznPt[0][1])
    
    stationInfo['Horizon Y Value'] = hznY
    
    #show the plot
    plt.show()
    
    #close the plot
    plt.close('all')    
    
    #Define the paramaters of an instructional dialogue box
    title = 'Apx. Shoreline'
        
    line1 = 'Define the two endpoints of the approximate shoreline.'
    line2 = 'The points do not have to be precise, they just provide a reference for the region of interest.'

    #Merge the two lines of text into one variable and add line breaks between them (optional) 
    text = (line1 + "\n\n" + line2 + "\n\n")
    
    #Call the dialouge box with ctypes; https://docs.python.org/3/library/ctypes.html
    ctypes.windll.user32.MessageBoxW(0, text, title, MB_OK | ICON_INFO | WIN_TOP)
    
    #Display a plot that shows the snapshot
    plt.imshow(snap, interpolation='nearest')
    plt.title('Select Two Endpoints of the Approximate Shoreline', fontweight ="bold")
    #Set axis limts equal to the resolution of the snapshot
    plt.xlim(0, w)
    plt.ylim(h, 0)
    
    #Use matplotlib's ginput function to save "n" number of mouse click coordinates
        #https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.ginput.html
    slPts = plt.ginput(n = 2, show_clicks = True, mouse_add = 1)
    plt.close('all')
    
    #Seperate the X and Y points created by plt.ginput into seperate lists 
    slX, slY = zip(*slPts)
    stationInfo['Apx. Shoreline'] = {'station':stationname, 'slX':slX, 'slY':slY}
    
    #Make orientation specific image transects 
    if stationInfo['Orientation'] == 0:
        stationInfo, hznPts = make.oceanForwardTransects(stationInfo, snap)
    elif stationInfo['Orientation'] == 1:
        stationInfo, hznPts = make.oceanRightTransects(stationInfo, snap)
    elif stationInfo['Orientation'] == 2:
        stationInfo, hznPts = make.oceanLeftTransects(stationInfo, snap)
    
    # Use transects to create test points  (Not currently used in current version of toolkit)
    slTransects = stationInfo['Shoreline Transects']
    
    xt = slTransects['x']
    yt = slTransects['y']
    
    tstX = np.zeros((len(xt),1))
    tstY = np.zeros((len(yt),1))
    
    # Create a test point at the lanward end of each image transect
    for i in range(0,len(xt)):
        if stationInfo['Orientation'] == 0:
            tstX[i] = xt[i,1]
            tstY[i] = yt[i,1]
        if stationInfo['Orientation'] > 0:
            tstX[i] = xt[i,0]
            tstY[i] = yt[i,0]
            
    # Export test point coordinates to stationInfo dictionary
    tst = {'x':tstX, 'y':tstY}
    stationInfo['Collision Test Points'] = tst

    # Plot Image Transects
    stationInfo = plot.figImageTransects(snap, hznPts, stationInfo)
    
    # Update list of used modules
    mod = ['ctypes' , 'numpy', 'matplotlib']
    mods = stationInfo['Modules Used']
    for n in range(len(mod)):
        if mod[n] not in mods:
            mods.append(mod[n])
    stationInfo['Modules Used'] = mods
    
    # Output updated stationInfo dictionary
    return(stationInfo)