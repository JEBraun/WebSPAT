# -*- coding: utf-8 -*-
"""
Created on Thu Aug  5 16:57:36 2021

@author: jeb2694
"""

import os
import time 
from termcolor import cprint
import matplotlib.pyplot as plt
import Functions.stationSetup as ss
import Functions.rootFunctions as rf
import Functions.setupFunctions as sf
from Functions.procImgs import genImgProducts

startTime = rf.initiationMsg()

cwd = os.getcwd()

stationType = rf.getStationType()

if stationType == 'existing':
   stationname = rf.selectStation()
   
   ssDir = (cwd + '\Inputs\\.stationConfigs\\')
   ssPath = (ssDir + stationname + '.station_setup.json')
   
   stationInfo = rf.getStationInfo(ssPath) 
        
elif stationType == 'new':
    stationInfo = ss.stationSetup()

stationInfo['Station Type'] = stationType
stationInfo['Setup Video'] = False

stationInfo, vid, source = sf.selectVid(stationInfo)
stationInfo['Source'] = source

dtInfo = rf.get_dateTime(vid, source)

stationInfo['Datetime Info'] = dtInfo
stationInfo['Rectified Image'] = False

stationInfo['Tide Level (m)'] = rf.getWtLvl(dtInfo['Date Time (utc) String 1'], stationInfo)


condition = 'Timex & Brt' #'Timex & Brt to produce only timex and brt products; 'all' to produce snap, variance, timex, and brt products

if condition == 'Timex & Brt':
    stationInfo, photoAvg, photoBrt = genImgProducts(stationInfo, vid, condition) 
elif condition == 'all':
    stationInfo, snap, photoAvg, photoVar, photoBrt = genImgProducts(stationInfo, vid, condition)

cprint('\n Extracting Shorelines...', 'blue', attrs=['bold'])
time.sleep(1)

(stationInfo, avgROI, avgThresh, 
avgContour, figAvgTranSl, avgTranSl,
figBPW_avg, bpwAvg) = rf.procShorelines(stationInfo, photoAvg, 'avg')

(stationInfo, brtROI, brtThresh, 
brtContour, figBrtTranSl, brtTranSl,
figBPW_brt, bpwBrt) = rf.procShorelines(stationInfo, photoAvg, 'brt')
            
plt.close('all')

endTime = rf.completionMsg(startTime) 

mod = ['os' , 'time', 'tqdm', 'termcolor', 'matplotlib']
mods = stationInfo['Modules Used']
for n in range(len(mod)):
    if mod[n] not in mods:
        mods.append(mod[n])
stationInfo['Modules Used'] = mods

# print(stationInfo['Modules Used'])




