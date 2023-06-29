# -*- coding: utf-8 -*-
"""
Created on Mon Jun 26 11:17:47 2023

@author: jeb2694
"""
#Import Modules
import os
import time
import termcolor
import numpy as np
from tqdm import tqdm
from termcolor import cprint
import Functions.batchFunctions as bf

#List desired stations by station name
stations = [  #Assumes stations have already been created using individual script
    'oakisland_west']
    # 'oakisland_east', 
    # 'jennette_north', 
    # 'jennette_south'
    # ]

#Define the desired date range for video processing
startDate = '2023-06-04' #Inclusive
endDate = '2023-06-05' #Exclusive

#Filter available videos by water level? [T/F]
wtLvlFilter = True
#Using multiple water level filters? [T/F]
multiWtLvls = False
#Define datum should water levels be referenced to
wtLvlDatum = 'NAVD88'
#Define the +/- water level range; videos outside this range are filtered out 
wtLvlRange = 0.2

#Mark program start time
runStart = time.time()

#Get console width for print formatting
termW = os.get_terminal_size().columns
if termW > 80:
    termW = 80

#Cycle through video processing and shoreline detection for each listed station
for s in range(len(stations)): 
    stationName = stations[s]
    stMsg = f'PROCESSING {stationName.upper()} VIDEOS'
    print('\n' + (termcolor.colored('=','green', attrs=['bold'])*termW))
    cprint(' '*bf.centerTxt(stMsg)[0] + stMsg + ' '*bf.centerTxt(stMsg)[1],'white', attrs = ['bold'])
    print((termcolor.colored('=','green', attrs=['bold'])*termW)+'\n' )
    stationInfo = bf.getStationInfo(stationName)
    stationInfo['Datum'] = wtLvlDatum
    
    #Apply water level filter if applicable 
    if wtLvlFilter == True:
        #Define an individual water level to be used for filtering if applicable
        if multiWtLvls == False:
            wtLvls = ['MHW']   # Accepts one of: 'MHHW', 'MHW', 'MTL', 'MSL', 'DTL', 'MLW', 'MLLW', 'NAVD88', 'STND'
            tgtWtLvls = bf.getDatumElevations(stationInfo, wtLvls)
        #Define a list of water levels to be used for filtering if applicable
        elif multiWtLvls == True:
            wtLvls = ['MLW', 'MSL', 'MHW'] # Accepts any combination of: 'MHHW', 'MHW', 'MTL', 'MSL', 'DTL', 'MLW', 'MLLW', 'NAVD88', 'STND'
            tgtWtLvls = bf.getDatumElevations(stationInfo, wtLvls)
    elif wtLvlFilter == False:
        pass
    
    #Create array to save processing time info
    runTime = np.zeros((len(wtLvls),len(stations)))
    
    #Open/Update/Create Station Inventory (Based on date range)
    inventory = bf.getStationInventory(stationInfo, startDate, endDate)
    
    #Import water level data from nearest NOAA water level observation station
    wtLvlData = bf.getWtLvlData(stationInfo, startDate, endDate)
    
    #Compile a list available videos
    availableVids = []
    for i in tqdm(range(len(inventory)), 
            desc = termcolor.colored(" Assesing available videos", 
                     'blue', attrs = ['bold']), leave = True, ncols = termW):
        item = inventory[i]
        availableVids.append(item['name'])
        
    time.sleep(0.5)
    cprint('   Success!\n', 'green', attrs=['bold'])

    #Process/Extract shorelines from each target video at each water level input
    for i in range(len(wtLvls)):
        wtLvl = tgtWtLvls[i] 
        elev = wtLvls[i]
        
        #Compile a list of videos to matching given filter parameters
        tgtVids = bf.getTargetVids(stationName, availableVids, wtLvlData, wtLvl, elev, wtLvlRange)
        
        #Process targeted videos and extract shoreline positions        
        runTime[i, s] = bf.procTgtVids(stationInfo, tgtVids, inventory, runTime)
        
        #Print station/water level complete message
        bf.stationCompleteMsg(s, i, stationName, wtLvl, runTime, termW)
        
#Print program complete message
bf.programCompleteMsg(runTime[:,s], termW)
        
    