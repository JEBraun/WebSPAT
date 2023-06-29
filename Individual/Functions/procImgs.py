# -*- coding: utf-8 -*-
"""
Created on Mon Jun  6 12:35:11 2022

@author: jeb2694
"""
import os
import cv2
import math
import numpy as np
from tqdm import tqdm
from time import sleep
from termcolor import cprint
import Functions.rootFunctions as rf
from Functions.udFromMAT import udFromMAT 

def genImgProducts(stationInfo, vid, condition):
    
    termW = os.get_terminal_size().columns
    if termW > 80:
        termW = 80

    '''Define which camera station the video is from and what the name of the input video'''
    stationName = stationInfo['Station Name']
    
    stationInfo, savePaths = rf.getSavePaths(stationInfo, vid)
    
    '''read in the videofile, calculate the fps, number of frames and the length of the video'''
    vidObj = cv2.VideoCapture(vid)
    fps = vidObj.get(cv2.CAP_PROP_FPS)
    totFrameCount = int(vidObj.get(cv2.CAP_PROP_FRAME_COUNT))
    vidLength = math.floor((totFrameCount/fps)-1) #in seconds ;subtract 1 sec to give us some leeway at the end
    
    '''Set a subsample interval to reduce proccessing time'''
    subSampleRate = 2 # 1 frame every __ seconds (e.g., subSampleRate of 2 uses 1 frame every 2 seconds for subsequent processing)  
    
    '''Find how many frames used for image product creation'''
    tgtFrameCount = math.floor(vidLength/subSampleRate) #subtract 1 sec to give us some leeway at the end
    
    '''Set the fraction to multiply by for time-averaged image calculation'''
    w = 1/tgtFrameCount
    end = tgtFrameCount - 1
    
    '''Create reference snapshot from the first frame of the input video'''
    
    vidObj = cv2.VideoCapture(vid)
    vidObj.set(cv2.CAP_PROP_POS_MSEC, 5000)
    success, snapBGR = vidObj.read()
    snap = cv2.cvtColor(snapBGR, cv2.COLOR_BGR2RGB)
    
    if condition == 'Timex & Brt':
        
        timexPath = savePaths['TimeX']
        brtPath = savePaths['Brightest Pixel']
        
        '''Preallocate empty image product arrays to speed up proccessing time''' 
        photoAvg = np.zeros(np.shape(snap))
        photoBrt = np.zeros(np.shape(snap))
        
        '''Generate the time-averaged and brightest pixel Image products'''
        cprint('\n Generating Time-Averaged and Brightest Pixel Image Products...', 'blue', attrs = ['bold'])
        sleep(0.5)
        for i in tqdm(range(end), desc = '   Subsampling Frames', leave = True, ncols = termW):
            sleep(0.1)
            timeSet = i * 1000 * subSampleRate
            vidObj.set(cv2.CAP_PROP_POS_MSEC, timeSet)
            success, snap = vidObj.read()
            # For the first frame save the snapshot and start the average
            if i == 0:
                snapd = np.array(snap)
                snapd = snapd.astype(float)
                photoAvg = w * snapd
                photoBrt = snapd
            # For all remaining steps calculate the average
            if i > 0 or i < end:
                snapd = np.array(snap)
                snapd = snapd.astype(float)
                photoAvg = photoAvg + w * snapd
                # calculate each pixels brightest value
                photoBrt = np.where(snapd > photoBrt, snapd, photoBrt)
            if i == (end-1):
                snapd = np.array(snap)
                snapd = snapd.astype(float)
                photoAvg = photoAvg + w * snapd
                # calculate each pixels brightest value
                photoBrt = np.where(snapd > photoBrt, snapd, photoBrt)
        cprint('   Success!', 'green', attrs = ['bold'])
                
        '''Scale and save the time-averaged image product'''
        avgScale = photoAvg.max()
        photoAvg = np.uint8(254 * (photoAvg / avgScale))
        cv2.imwrite((timexPath + '.png'), photoAvg)
        
        '''Scale and save the time-averaged image product'''
        brtScale = photoBrt.max()
        photoBrt = np.uint8(254 * (photoBrt / brtScale))
        cv2.imwrite((brtPath+ '.png'), photoBrt)
        
        calCam = stationInfo['Camera Calibration']
        if calCam == True: 
            photoBrt = udFromMAT(photoBrt, stationName)
            cv2.imwrite((brtPath + 'UD.fix.png'), photoBrt)
            photoAvg = udFromMAT(photoAvg, stationName)
            cv2.imwrite((timexPath + 'UD.png'), photoAvg)
        else:
            pass
        
        # '''For subsequent image product anlaysis, image products must be converted from BGR to RGB color values;
            # however this is not necessary before saving them'''
            
        photoBrt = cv2.cvtColor(photoBrt, cv2.COLOR_BGR2RGB)
        photoAvg = cv2.cvtColor(photoAvg, cv2.COLOR_BGR2RGB)
    
        # Update list of used modules
        mod = ['opencv' , 'math', 'time', 'tqdm', 'termcolor']
        mods = stationInfo['Modules Used']
        for n in range(len(mod)):
            if mod[n] not in mods:
                mods.append(mod[n])
        stationInfo['Modules Used'] = mods
        
        return(stationInfo, photoAvg, photoBrt)
    
    elif condition == 'All':
        
        snapPath = savePaths['Snapshot']
        timexPath = savePaths['TimeX']
        varPath = savePaths['Time Variance']
        brtPath = savePaths['Brightest Pixel']
        
        '''Preallocate empty image product arrays to speed up proccessing time''' 
        photoAvg = np.zeros(np.shape(snap))
        photoBrt = np.zeros(np.shape(snap))
        photoVar = np.zeros(np.shape(snap))
        frames = []*end
        
        '''Generate the time-averaged and brightest pixel Image products'''
        cprint(('\n Generating Snapshot, Time-Averaged, Brightest Pixel, and ' +
               'Time Variance Image Products...'), 'blue', attrs = ['bold'])
        sleep(0.5)
        for i in tqdm(range(end), desc = '   Subsampling Frames', leave = True, ncols = termW):
            sleep(0.1)
            timeSet = i * 1000 * subSampleRate
            vidObj.set(cv2.CAP_PROP_POS_MSEC, timeSet)
            success, snap = vidObj.read()
            # For the first frame save the snapshot and start the average
            if i == 0:
                snapd = np.array(snap)
                snapd = snapd.astype(float)
                photoAvg = w * snapd
                photoBrt = snapd
                frames[i] = snapd 
            # For all remaining steps calculate the average
            if i > 0 or i < end:
                snapd = np.array(snap)
                snapd = snapd.astype(float)
                photoAvg = photoAvg + w * snapd
                # calculate each pixels brightest value
                photoBrt = np.where(snapd > photoBrt, snapd, photoBrt)
                frames[i] = snapd 
            if i == (end-1):
                snapd = np.array(snap)
                snapd = snapd.astype(float)
                photoAvg = photoAvg + w * snapd
                # calculate each pixels brightest value
                photoBrt = np.where(snapd > photoBrt, snapd, photoBrt)
                frames[i] = snapd 
                for j in range(end):
                    photoVarFrac = w * ((photoAvg - frames[j]) ** 2)
                    photoVar = photoVar + photoVarFrac
        cprint('   Success!', 'green', attrs = ['bold'])
                    
        '''Scale and save the time-averaged image product'''
        avgScale = photoAvg.max()
        photoAvg = np.uint8(254 * (photoAvg / avgScale))
        cv2.imwrite((timexPath + '.png'), photoAvg)
        
        '''Scale and save the time-averaged image product'''
        brtScale = photoBrt.max()
        photoBrt = np.uint8(254 * (photoBrt / brtScale))
        cv2.imwrite((brtPath+ '.png'), photoBrt)
        
        # Scale the variance image and write
        varScale = photoVar.max()
        np.seterr(invalid='ignore')
        photoVar = np.uint8(254 * (photoVar / varScale))
        cv2.imwrite((varPath+ '.png'), photoVar)
        
        calCam = stationInfo['Camera Calibration']
        if calCam == True: 
            snap = udFromMAT(snap, stationName)
            cv2.imwrite((snapPath + 'UD.png'), snap)
            photoBrt = udFromMAT(photoBrt, stationName)
            cv2.imwrite((brtPath + 'UD.fix.png'), photoBrt)
            photoAvg = udFromMAT(photoAvg, stationName)
            cv2.imwrite((timexPath + 'UD.png'), photoAvg)
            photoVar = udFromMAT(photoVar, stationName)
            cv2.imwrite((varPath + 'UD.png'), photoVar)
        else:
            pass
        
        # '''For subsequent image product anlaysis, image products must be converted from BGR to RGB color values;
            # however this is not necessary before saving them'''
            
        snap, photoBrt, photoAvg, photoVar = rf.cvtColors(snap, photoBrt, photoAvg, photoVar)
        
        vidObj.release()
        
        # Update list of used modules
        mod = ['opencv' , 'math', 'time', 'tqdm', 'termcolor']
        mods = stationInfo['Modules Used']
        for n in range(len(mod)):
            if mod[n] not in mods:
                mods.append(mod[n])
        stationInfo['Modules Used'] = mods
        
        return(stationInfo, snap, photoAvg, photoVar, photoBrt)
    
