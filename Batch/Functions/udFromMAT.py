# -*- coding: utf-8 -*-
"""
Created on Fri Jul 30 12:26:37 2021

@author: braunj
"""
import os
import cv2 as cv
import numpy as np
from scipy.io import loadmat

def udFromMAT(img, stationname):
    
    cwd = os.getcwd()
    path = os.path.join(cwd, 'Inputs', stationname)
    fname = (stationname + '_camCal_PyParams.mat')
    cameraParams = loadmat(os.path.join(path, fname))
    
    radDist = cameraParams['radDist']
    tanDist = cameraParams['tanDist']
    intrinMtx = cameraParams['intrinMtx']
    
    x0 = intrinMtx[0,0]
    y0 = intrinMtx[0,1]
    z0 = intrinMtx[0,2]
    
    x1 = intrinMtx[1,0]
    y1 = intrinMtx[1,1]
    z1 = intrinMtx[1,2]
    
    x2 = intrinMtx[2,0]
    y2 = intrinMtx[2,1]
    z2 = intrinMtx[2,2]
    
    k1 = radDist[0, 0]
    k2 = radDist[0, 1]
    k3 = radDist[0, 2]
    p1 = tanDist[0, 0]
    p2 = tanDist[0, 1]
    
    def undistort(img):
        
        mtx = np.array([
            [x0, x1, x2],
            [y0, y1, y2],
            [z0, z1, z2]])
        
        # Distortion coefficient
        dist = np.array([k1, k2, p1, p2, k3])
    
        h,  w = img.shape[:2]
        dims = (w, h)
        
    
        mapx, mapy = cv.initUndistortRectifyMap(mtx, dist, None, mtx, dims, 5)
        udImg = cv.remap(img, mapx, mapy, cv.INTER_LINEAR)
        return (udImg)
     
    udImg = undistort(img)
    # imgID = ['udSnap', 'Undistorted Snapshot']
    
    # plotFig(udSnap, imgID, stationname)
    
    return (udImg)
    
    
    




