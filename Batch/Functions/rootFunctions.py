# -*- coding: utf-8 -*-
"""
Created on Fri Aug  6 10:10:23 2021

@author: jeb2694
"""
import os
import cv2
import math
import json
import time
import itertools
import numpy as np
import pandas as pd
import tkinter as tk
import noaa_coops as nc
from pathlib import Path
from termcolor import cprint
from PIL import Image, ImageDraw
import Functions.plotFigures as plot
from matplotlib import pyplot as plt
from skimage.measure import profile_line
from datetime import datetime, timedelta
from statsmodels.nonparametric.kde import KDEUnivariate

def initiationMsg():
    startTime = time.time()
    msgStr = datetime.now().strftime('Process initiated at %I:%M %p on %A %B %d, %Y')
    s ='-'*len(msgStr)
    print('\n' + s)
    cprint(msgStr, 'green', attrs = ['bold'])
    print(s)
    return(startTime)

#######################################

def getStationType():
    
    root = tk.Tk()
    root.title("Import Station Parameters")
    root.eval('tk::PlaceWindow %s center' %root.winfo_toplevel())
    root.attributes("-topmost", True)
    
    label = tk.Label(root, text="Are you using an existing station \n or would you like to set up a new one?")
    label.pack(side="top", fill="both", expand=True, padx=20, pady=20)
    
    def button1():
        global stationType
        stationType = 'new'
        root.destroy()
    
    def button2():
        global stationType
        stationType = 'existing'
        root.destroy()
        
    button1 = tk.Button(root, text="Setup New Station", relief = "raised", 
                        command = button1)
    button1.pack(side = "bottom", pady = 6, fill="none", expand=True)
    
    button2 = tk.Button(root, text="Use Existing Station", relief = "raised", 
                        command = button2)
    button2.pack(side="bottom", pady = 3, fill="none", expand=True)
    
    root.mainloop()
    
    return(stationType)

#######################################

def selectStation():
    cwd = os.getcwd()
    path = (cwd + '\Inputs\\.StationConfigs\\')
    setupFiles = [file for file in os.listdir(path) if file.endswith('.json')]
    
    stations = [0]*(len(setupFiles))
    for i in range(0,len(setupFiles)):
        stations[i],_,_ = setupFiles[i].split('.', 3)
    
    root = tk.Tk()
    root.title("Select Station")
    root.eval('tk::PlaceWindow %s center' %root.winfo_toplevel())
    
    # title = tk.Label(root, text="Are you using an existing station \n or would you like to set up a new one?")
    # title.grid(root, columnspan = 2, row = 1)
    tk.Label(root, text = 'Select an existing station:').grid(row = 0, column = 1, 
                                                    columnspan = 2, padx = 10, pady =10)
    
    for i in range(0,len(stations)):
        
        def button(s):
            global stationname
            stationname = s
            root.destroy()
        
        if i % 2 == 0:
            x = 1
            y = i + 1
        else: 
            x = 2
            y = i
         
        tk.Button(root, text = stations[i], command = lambda s = stations[i]: 
                  button(s)).grid(column = x, row = y, sticky="ew", 
                                  pady=5, padx=5)
            
    root.mainloop()
    
    return(stationname)

#######################################

def get_dateTime(vid, source):
        
    if source == 'ftp':
        #Extract datetime from video filename
        vidName = os.path.basename(vid)
        #Separate the stationname and datetime using the "."
        station, exc, dt = vidName.partition('.')
        #Separate the datetime from the file extension using the "."
        dt, exc, ext = dt.partition('.')
        
        dtchar = len(dt)
        #Pull the date (yyyy-mm-dd) from the datetime string
        date = dt[:dtchar-5]
        #Pull the local time (hhmm) from the datetime string
        time_local= dt[dtchar-4:]
       
        #Break the date into individual constituents
        y = date[0:4]
        mo = date[5:7]
        d = date[8:10]
        
        #Break the time into individual constituents
        hr = time_local[0:2]
        mi = time_local[2:4]
        
        #Create a datetime format string (yyyy-mm-dd hh:mm)
        t = hr + ':' + mi
        dt = date +' '+ t
        
        #Create a local datetime object to convert local time to utc 
        dt_obj = datetime.strptime(dt,'%Y-%m-%d %H:%M')
        dt_local = str(dt_obj)
        #Convert local datetime to utc time with timedelta (+ 4 hours = utc)
            #Assuming local time is gmt-4
        dt_utc = str(dt_obj + timedelta(hours = 4)) 
        
        #Create local and utc time strings
        time_utc = dt_utc[11:16]
        time_local = dt_local[11:16]
        #Create local and utc hour strings
        hr_utc = time_utc[0:2]
        hr_local = time_local[0:2]
        #Create a minute string (same for both time zones)
        mi = time_local[3:5]
        
       #Create utc date time strings for file naming and figure titles
        utcT_str0 = str(y + mo + d + '_' + hr_utc + mi)
            #Ex) 20220504_1526
        utcT_str1 = str(y + '-' + mo + '-' + d + '_' + hr_utc + mi)
            # Ex) 2022-05-04_1526
        utcT_str2 = str(y + '-' + mo + '-' + d + ' ' + hr_utc + ':' + mi + ':00')
            #Ex) 2022-05-04 15:26:00
            
        #Create local date time strings for file naming and figure titles
        localT_str0 = str(y + mo + d + '_' + hr_local + mi) 
            #Ex) 20220504_1126
        localT_str1 = str(y + '-' + mo + '-' + d + '_' + hr_local + mi) 
            # Ex) 2022-05-04_1126
        localT_str2 = str(y + '-' + mo + '-' + d + ' ' + hr_local + ':' + mi + ':00') 
            #Ex) 2022-05-04 11:26:00
    
        #Package datetime variables/strings into dictionary to be carrried through other functions
        dtInfo = {'Date':date, 'Time_utc':time_utc, 'Time_utc2':(hr_utc + mi),
                  'Time_local':time_local, 'Time_local2':(hr_local + mi),
                  'Year':y,'Month':mo, 'Day':d, 'Hour_utc':hr_utc,
                  'Hour_local':hr_local, 'Minute':mi,
                  'Date Time (local) String 1':localT_str0, 
                  'Date Time (local) String 2':localT_str1,
                  'Date Time (local) String 3':localT_str2,
                  'Date Time (utc) String 1':utcT_str0,
                  'Date Time (utc) String 2':utcT_str1,
                  'Date Time (utc) String 3':utcT_str2
                  } 

    elif source == 'rtsp':
        #Extract datetime from video filename
        vidName = os.path.basename(vid)
        #Separate the stationname from the rest of the file name using the "-"
        station, exc, dt = vidName.partition('-')
        #Separate the datetime from the file extension using the "."
        dt, exc, ext = dt.partition('.')
        
        dtchar = len(dt)
        #Pull the date (yyyy-mm-dd) from the datetime string
        date = dt[:dtchar-8]
        #Pull the utc time (hhmm) from the datetime string
        time_utc = dt[dtchar-7:dtchar-3]
        
        #Break the date into individual constituents
        y = date[0:4]
        mo = date[5:7]
        d = date[8:10]
        
        #Break the time into individual constituents
        hr = time_utc[0:2]
        mi = time_utc[2:4]
        
        #Create a datetime format string(hh:mm)
        t = hr + ':' + mi
        dt = date +' '+ t
        
        #Create a utc date time object to convert utc to local time 
        dt_obj = datetime.strptime(dt,'%Y-%m-%d %H:%M')
        dt_utc = str(dt_obj)
        #Convert utc datetime to local time with timedelta (-4 hours = utc-4)
            #Assuming local time is gmt-4
        dt_local = str(dt_obj - timedelta(hours = 4)) 
        
        #Create local and utc time strings
        time_utc = dt_utc[11:16]
        time_local = dt_local[11:16]
        #Create local and utc hour strings
        hr_utc = time_utc[0:2]
        hr_local = time_local[0:2]
        #Create a minute string (same for both time zones)
        mi = time_local[3:5]
        
        #Create utc date time strings for file naming and figure titles
        utcT_str0 = str(y + mo + d + '_' + hr_utc + mi)
            #Ex) 20220504_1526
        utcT_str1 = str(y + '-' + mo + '-' + d + '_' + hr_utc + mi)
            # Ex) 2022-05-04_1526
        utcT_str2 = str(y + '-' + mo + '-' + d + ' ' + hr_utc + ':' + mi + ':00')
            #Ex) 2022-05-04 15:26:00
            
        #Create local date time strings for file naming and figure titles
        localT_str0 = str(y + mo + d + '_' + hr_local + mi) 
            #Ex) 20220504_1126
        localT_str1 = str(y + '-' + mo + '-' + d + '_' + hr_local + mi) 
            # Ex) 2022-05-04_1126
        localT_str2 = str(y + '-' + mo + '-' + d + ' ' + hr_local + ':' + mi + ':00') 
            #Ex) 2022-05-04 11:26:00
            #Package datetime variables/strings into dictionary to be carrried through other functions
        dtInfo = {'Date':date, 'Time_utc':time_utc, 'Time_utc2':(hr_utc + mi),
                  'Time_local':time_local, 'Time_local2':(hr_local + mi),
                  'Year':y,'Month':mo, 'Day':d, 'Hour_utc':hr_utc,
                  'Hour_local':hr_local, 'Minute':mi,
                  'Date Time (local) String 1':localT_str0, 
                  'Date Time (local) String 2':localT_str1,
                  'Date Time (local) String 3':localT_str2,
                  'Date Time (utc) String 1':utcT_str0,
                  'Date Time (utc) String 2':utcT_str1,
                  'Date Time (utc) String 3':utcT_str2
                  } 

    return(dtInfo)
    
#######################################

def getStationInfo(ssPath):
    
    setupFile = open(ssPath)
    stationInfo = json.load(setupFile)
    
    stationInfo['Apx. Shoreline']['slX'] = np.asarray(stationInfo['Apx. Shoreline']['slX'])
    stationInfo['Apx. Shoreline']['slY'] = np.asarray(stationInfo['Apx. Shoreline']['slY'])
    
    stationInfo['Collision Test Points']['x'] = np.asarray(stationInfo['Collision Test Points']['x'])
    stationInfo['Collision Test Points']['y'] = np.asarray(stationInfo['Collision Test Points']['y'])
    
    stationInfo['Dune Line Info'] = (
        {'Dune Line Interpolation':np.asarray(stationInfo['Dune Line Info']['Dune Line Interpolation']),
         'Dune Line Points':np.asarray(stationInfo['Dune Line Info']['Dune Line Points']),
         'Dune Line Orientation':stationInfo['Dune Line Info']['Duneline Orientation']})

    stationInfo['Shoreline Transects']['x'] = np.asarray(stationInfo['Shoreline Transects']['x'])
    stationInfo['Shoreline Transects']['y'] = np.asarray(stationInfo['Shoreline Transects']['y'])
    
    return(stationInfo)

#######################################

def getSavePaths(stationInfo, vid):
    
    stationname = stationInfo['Station Name']
    dtInfo = stationInfo['Datetime Info']
    # dtInfo = sf.get_dateTime(vid)
    date = dtInfo['Date']
    time = dtInfo['Time_utc2']
    
    filename_w_ext = os.path.basename(vid)
    fileName, fileExtension = os.path.splitext(filename_w_ext)
    
    cwd = os.getcwd()
    savedir = os.path.join(cwd, 'Outputs', stationname) 
    
    # Create the directories and file names to store the images
    p = Path(savedir + '\\' + date + '\\' + time)
    
    # Snapshot directory
    snapPath = p  # / 'snapshot'
    os.makedirs(snapPath, exist_ok=True)
    # Snapshot file name
    snapName = fileName + '.snap' 
    snapNameStr = str(snapPath / snapName)
    
    # Timex directory
    timexPath = p  # / 'timex'
    os.makedirs(timexPath, exist_ok=True)
    # Timex file name
    timexName = fileName + '.timex'
    timexNameStr = str(timexPath / timexName)
    
    # Variance directory
    varPath = p  # / 'timevar'
    os.makedirs(varPath, exist_ok=True)
    # Variance file name
    varName = fileName + '.var'
    varNameStr = str(varPath / varName)
    
    # Brightest directory
    brtPath = p  # / 'brightest'
    os.makedirs(brtPath, exist_ok=True)
    # Brightest file name
    brtName = fileName + '.brt'
    brtNameStr = str(brtPath / brtName)
     
    savePaths = {'Snapshot':snapNameStr, 'TimeX':timexNameStr,
                    'Time Variance':varNameStr, 'Brightest Pixel':brtNameStr}
    
    # Update list of used modules
    mod = ['os' , 'opencv', 'math', 'json', 'time', 'termcolor', 
           'itertools', 'numpy', 'pandas', 'tkinter', 'noaa_coops', 
           'pathlib', 'termcolor', 'PIL', 'matplotlib', 'skimage', 
           'datetime', 'statsmodels']

    mods = stationInfo['Modules Used']
    for n in range(len(mod)):
        if mod[n] not in mods:
            mods.append(mod[n])
    stationInfo['Modules Used'] = mods
    
    return(stationInfo, savePaths)

#######################################

def cvtColors(snap, photoBrt, photoAvg, photoVar):
    snap_RGB = cv2.cvtColor(snap, cv2.COLOR_BGR2RGB)
    photoBrt_RGB = cv2.cvtColor(photoBrt, cv2.COLOR_BGR2RGB)
    photoAvg_RGB = cv2.cvtColor(photoAvg, cv2.COLOR_BGR2RGB)
    photoVar_RGB = cv2.cvtColor(photoVar, cv2.COLOR_BGR2RGB)
    return(snap_RGB, photoBrt_RGB, photoAvg_RGB, photoVar_RGB)

#######################################

def mapROI(stationInfo, photo, imgType):
    
    #get the dimensions (resolution) of the snapshot
    dims = ((len(photo[1]), len(photo)))
    
    #width and height in pixels 
    w = dims[0]
    h = dims[1]
    
    if imgType == 'avg' or imgType == 'brt' or imgType == 'snap':
        
        transects = stationInfo['Shoreline Transects']
        xt = np.asarray(transects['x'])
        yt = np.asarray(transects['y'])
        
    elif imgType == 'rec':
        transects = stationInfo['Rectified Transects']
        xt = np.asarray(transects['x'])
        yt = np.asarray(transects['y'])
        
    cords = []
    
    for i in range(0,len(xt)):
        pts = [int(xt[i,1]),int(yt[i,1])]
        cords.append(pts)
        
    for i in range(len(xt)-1,-1,-1):
        pts = [int(xt[i,0]),int(yt[i,0])]
        cords.append(pts)
    cords.append(cords[0])
    
    xs, ys = zip(*cords)
    poly = list(itertools.chain.from_iterable(cords))
    
    img = Image.new('L', (w, h), 0)
    ImageDraw.Draw(img).polygon(poly, outline=1, fill=1)
    
    if imgType == 'rec':
        mask = np.array(np.flipud(img))
    else:
        mask = np.array(img)
        
    maskedImg = photo.astype(np.float64)
    for i in range(0,w):
        for j in range(0,h):
            if mask[j,i] == 0:
                maskedImg[j,i] = np.NaN
            else:
                maskedImg[j,i] = (maskedImg[j,i]/255)
  
    stationInfo, figROI = plot.figROI(stationInfo, photo, maskedImg, xs, ys, imgType)
    
    # Update list of used modules
    mod = ['os' , 'opencv', 'math', 'json', 'time', 'termcolor', 
           'itertools', 'numpy', 'pandas', 'tkinter', 'noaa_coops', 
           'pathlib', 'termcolor', 'PIL', 'matplotlib', 'skimage', 
           'datetime', 'statsmodels']

    mods = stationInfo['Modules Used']
    for n in range(len(mod)):
        if mod[n] not in mods:
            mods.append(mod[n])
    stationInfo['Modules Used'] = mods
    
    return (stationInfo, maskedImg, figROI)

#######################################

def improfile(rmb, stationInfo):
    
    if stationInfo['Rectified Image'] == False:
        transects = stationInfo['Shoreline Transects']
        xt = np.asarray(transects['x'])
        yt = np.asarray(transects['y'])
        
    elif stationInfo['Rectified Image'] == True:
        transects = stationInfo['Rectified Transects']
        xt = np.asarray(transects['x'])
        yt = np.asarray(transects['y'])
        
    n = len(xt)
    imProf = [0]*n   
    for i in range(0,n):
        imProf[i] = profile_line(rmb, (yt[i,1], xt[i,1]), (yt[i,0], xt[i,0]),
                                 mode = 'constant')
        
    tot = [imProf[0].tolist()]
    
    for i in range(0,n): 
        cvt = imProf[i].tolist()
        tot.append(cvt)

    improfile = []
    for i in range(0,n): 
        for j in range(0, len(tot[i])):
            if math.isnan(tot[i][j]):
                pass
            else:
                improfile.append(tot[i][j])   
            
    P = np.asarray(improfile)   
    return(P)

#######################################

def ksdensity(P, **kwargs):
    """Univariate Kernel Density Estimation with Statsmodels"""
    x_grid = np.linspace(P.max(), P.min(), 1000)
    kde = KDEUnivariate(P)
    kde.fit(**kwargs)
    pdf = kde.evaluate(x_grid)
    return (pdf, x_grid)

#######################################

def contourMTWL(X, Y, rmb, levels):
    figContour = plt.figure()
    c = plt.contour(X, Y, rmb, levels, colors = 'red')
    plt.close(figContour)
    
    contours = []
    for line in c.collections[0].get_paths():
        contours.append(line.vertices)

    size = 0
    index = 0
    for i in range(0, len(contours)):
        if np.size(contours[i]) > size:
            size = np.size(contours[i])
            index = i 
            
    cLine = contours[index]
    return(cLine)

#######################################

def getWtLvl(tgtDate, stationInfo):
    
    station = nc.Station(stationInfo['NOAA Station ID'])
    
    dtObj = datetime.strptime(tgtDate, '%Y%m%d_%H%M')
    
    startDate = dtObj.strftime('%Y%m%d')
    endDate = (dtObj + timedelta(days=1)).strftime('%Y%m%d')
    
    df = station.get_data(
        begin_date = startDate,
        end_date = endDate,
        product = "water_level",
        datum = "NAVD",
        units = "metric",
        time_zone = "gmt")
    df.index.names = ['DateTime']
    headers = df.columns.tolist()
    df.rename(columns={
        headers[0]: 'Water Level', 
        headers[1]: 'Sigma',
        headers[2]: 'Data Flags', 
        headers[3]: 'QA/QC Level'
        }, inplace=True)
    
    dt = pd.to_datetime(dtObj.strftime('%Y-%m-%d %H:%M:%S'))
    idx = df.index.get_indexer([dt], method='nearest')[0]
    
    wtLvl = df.iloc[idx]['Water Level']
    
    return(wtLvl)

#######################################

def completionMsg(startTime):
    endTime = time.time()
    mi, sec = divmod((endTime - startTime), 60)
    hr, mi = divmod(mi, 60)
    now = datetime.now()
    dtFinal = datetime(now.year, now.month, now.day, int(hr), int(mi), int(round(sec)))
    msgStr = (
        datetime.now().strftime(('Process completed '
                 'at %I:%M %p on %A %B %d, %Y ')) + dtFinal.strftime('[%H hr %M min %S sec]'))
    s ='-'*len(msgStr)
    print('\n' + s)
    cprint(msgStr, 'green', attrs = ['bold'])
    print(s)
    return(endTime)
    


