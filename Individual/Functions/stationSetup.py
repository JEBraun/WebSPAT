# -*- coding: utf-8 -*-
"""
Created on Wed Jun 14 10:17:47 2023

@author: jeb2694
"""

import os
import json
from termcolor import cprint
import Functions.setupFunctions as sf
import Functions.drawTransects as draw
from Functions.udFromMAT import udFromMAT

def stationSetup():
    cprint((' Station Setup Initiated\n'), 'green', attrs=['bold'])
    
    sf.setup_msg()
    stationname, stationFod = sf.define_station()
    rtspURL = sf.getRTSP()
    mods = ['os' , 'json', 'termcolor']
    stationInfo = {'Station Name':stationname, 
                   'Setup Video':True, 
                   'RTSP URL': rtspURL,
                   'Modules Used': mods}
    
    stationInfo, noaaID = sf.getNOAAstationID(stationInfo) 
    stationInfo['NOAA Station ID'] = noaaID
    
    cwd = os.getcwd()
    path = (cwd + '\Inputs\\.StationConfigs\\')
    
    if not os.path.exists(path):
        os.makedirs(path)
        
    stationType = sf.getStationType()
    
    if stationType == 'video':
        stationInfo,vid, source = sf.selectVid(stationInfo)
        stationInfo['Source'] = source
        snap = sf.getVidSnap(vid)
        
        stationname_str = str(rtspURL.split('/')[-2:-1][0]) #assumes camera name is last subdirectory in link (ex. https://hostserver/webcoos/{camera name}/')
        stationInfo['Station Name String'] = stationname_str
        
    elif stationType == 'still':
        snap = sf.getSnapshot()
        
    stationInfo['Orientation'] = sf.setOrientation() 
    
    camCal_opt = sf.getCamCalabration()
    
    if camCal_opt == True: 
        snapUD = udFromMAT(snap, stationname)
        snap = snapUD
    else:
        pass
        
    # refImg = sf.makeRefImg(stationname, stationFod, snap)
    
    stationInfo['Camera Calibration'] = camCal_opt
    stationInfo['Dune Line Info']  = sf.getDuneLine(stationInfo, snap)  
    
    stationInfo = draw.imageTransects(stationInfo, snap)
    
    # Objects of type ndarray are not JSON serializable
    stationInfo['Collision Test Points']['x'] = stationInfo['Collision Test Points']['x'].tolist()
    stationInfo['Collision Test Points']['y'] = stationInfo['Collision Test Points']['y'].tolist()
    stationInfo['Dune Line Info']['Dune Line Points'] = stationInfo['Dune Line Info']['Dune Line Points'].tolist()
    stationInfo['Dune Line Info']['Dune Line Interpolation'] =  stationInfo['Dune Line Info']['Dune Line Interpolation'].tolist()
    stationInfo['Shoreline Transects']['x'] = stationInfo['Shoreline Transects']['x'].tolist()
    stationInfo['Shoreline Transects']['y'] = stationInfo['Shoreline Transects']['y'].tolist()
    
    fname = (stationname + '.station_setup.json')
    
    #Export shoreline variables to a .json file
    with open((path + fname), "w") as f:
        json.dump(stationInfo, f)
    
    cprint(('\n The ' + stationname + ' station setup was successful!/n'), 'green', attrs=['bold'])
    stationInfo = sf.showSetupImg(stationInfo)
        
    return(stationInfo)