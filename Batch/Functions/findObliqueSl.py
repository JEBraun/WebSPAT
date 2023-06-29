# -*- coding: utf-8 -*-
"""
Created on Mon Aug  9 10:46:15 2021

@author: jeb2694
"""

import os
import numpy as np
import scipy.signal as signal
import Functions.slExtract as sl
import Functions.plotFigures as plot
import Functions.rootFunctions as rf
from skimage.filters import threshold_otsu

def obliqueShoreline(stationInfo, photo, imgType):
    
    stationname = stationInfo['Station Name']
    
    dtInfo = stationInfo['Datetime Info']
    
    date = dtInfo['Date']
    time = dtInfo['Time_utc2']
    
    cwd = os.getcwd()
    
    saveDir = os.path.join(cwd, 'Outputs', stationname, date, time, imgType)
    
    if not os.path.exists(saveDir):
        os.makedirs(saveDir)

    #get the dimensions (resolution) of the snapshot
    dims = ((len(photo[1]), len(photo)))
    
    #width and height in pixels 
    w = dims[0]
    h = dims[1]
    
    xgrid = np.round(np.linspace(0, w, w))
    ygrid = np.round(np.linspace(0, h, h))
 
    X, Y = np.meshgrid(xgrid, ygrid, indexing = 'xy')

    stationInfo, maskedImg, figROI = rf.mapROI(stationInfo, photo, imgType)
    
    rmb = maskedImg[:,:,0] - maskedImg[:,:,2] 
    
    P = rf.improfile(rmb, stationInfo) #RMB after?
    P = P.reshape(-1,1)
    
    pdfVals, pdfLocs = rf.ksdensity(P)
    
    thresh_weightings = [(1/3), (2/3)]
    
    peaks = signal.find_peaks(pdfVals)
    peakVals = np.asarray(pdfVals[peaks[0]])
    peakLocs = np.asarray(pdfLocs[peaks[0]])
   
    thresh_otsu = threshold_otsu(P)
    
    I1 = np.asarray(np.where(peakLocs < thresh_otsu))
    J1, = np.where(peakVals[:] == np.max(peakVals[I1]))
    I2 = np.asarray(np.where(peakLocs > thresh_otsu))
    J2, = np.where(peakVals[:] == np.max(peakVals[I2]))
    
    peakX = np.asarray([(peakLocs[J1]), (peakLocs[J2])])
    peakY = np.asarray([(peakVals[J1]), (peakVals[J2])])
    
    thresh = (thresh_weightings[0]*peakLocs[J1] +
              thresh_weightings[0]*peakLocs[J2])
    
    thresh = float(thresh)
    
    threshInfo = {
        'Thresh':thresh, 
        'Otsu Threshold':thresh_otsu,
        'Threshold Weightings':thresh_weightings
        }
    
    stationInfo, figThresh = plot.figThresh(stationInfo, pdfLocs, pdfVals, 
                                  peakX, peakY, thresh, thresh_otsu, imgType)
  
    stationInfo, tranSl = sl.extract(stationInfo, rmb, maskedImg, threshInfo, imgType)
    
    stationInfo, figTranSl = plot.figTranSl(stationInfo, photo, tranSl, imgType)
    
    levels = np.asarray([thresh])
    contour = rf.contourMTWL(X, Y, rmb, levels)
    
    # Update list of used modules
    mod = ['os' , 'numpy', 'scipy', 'skimage']
    mods = stationInfo['Modules Used']
    for n in range(len(mod)):
        if mod[n] not in mods:
            mods.append(mod[n])
    stationInfo['Modules Used'] = mods
    
    return(stationInfo, figROI, figThresh, contour, figTranSl, tranSl)    


   
    



  
    