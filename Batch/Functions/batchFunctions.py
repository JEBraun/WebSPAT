# -*- coding: utf-8 -*-
"""
Created on Mon Jun 26 11:21:46 2023

@author: jeb2694
"""

import os
import re
import cv2
import sys
import wget
import json
import pytz
import math
import time
import urllib
import requests
import termcolor
import threading
import numpy as np
import pandas as pd
from tqdm import tqdm
from time import sleep
from tqdm import trange
import noaa_coops as nc
from termcolor import cprint
import matplotlib.pyplot as plt
import Functions.plotFigures as plot
import Functions.findObliqueSl as find
from datetime import datetime, timedelta
from Functions.procImgs import genImgProducts 

#%% Import existing station config files
def getStationInfo(stationName):
    
    ssPath = os.path.join(os.getcwd(), 'Inputs', '.stationConfigs', stationName + '.station_setup.json')
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

#%% Import datum elevations from station's nearest NOAA station

def getDatumElevations(stationInfo, wtLvls):
    
    datum = stationInfo['Datum']
    noaaID = str(stationInfo['NOAA Station ID'])
    
    link = "https://tidesandcurrents.noaa.gov/datums.html?datum=@&units=1&id=$"
    link = link.replace('@', datum)
    link = link.replace('$', noaaID)
    
    
    f = urllib.request.urlopen(link)
    myfile = f.read()
    
    
    html_tables = pd.read_html(myfile)
    df = html_tables[0]
    df.T # transpose to align
    
    datumTable = df.to_numpy()
    idx = np.where(datumTable[:,0]=='GT')[0][0]
    datumTable = np.delete(datumTable, [range(idx,len(datumTable))], 0)
    datumTable =np.delete(datumTable, 2, 1)
       
    tgtWtLvls = []
    for lvl in wtLvls:
        idx = np.where(datumTable[:,0]==lvl)[0][0]
        tgtWtLvls.append(float(datumTable[idx,1]))
        
    return(tgtWtLvls)

#%% Create/Update/Open Inventory of all videos from a given statio

def getStationInventory(stationInfo, startDate, endDate):
    '''{jsonData} = main_request(service, startAfter, startBefore, n)
          service = camera name
          startAfter = date to start search (inclusive - date is included in search)
          startBefore = date to end search (exclusive - date is not included in search) 
          n = page number; used to navigate pages of json file
          returns: json formated inventory of specified camera archive between specified dates'''
    def main_request(service, startAfter, startBefore, n ):
        r = requests.get(
             (f'https://app.webcoos.org/webcoos/api/v1/elements/?page={n}&service=' + 
              service +'-video-archive-s3&starting_after=' + startAfter +
              'T00%3A00%3A00Z&starting_before='+ startBefore + 'T00%3A00%3A00Z'),
             headers={
                 'Authorization': 'Token 972573899bcc2fbe0059a6ac633141544170d493',
                 'Accept': 'application/json',})
        return(r.json()) 

    '''{pages} = get_pages(response)
          response = json object returned by main_request function
          returns: number of pages in the json object (int)'''
    def get_pages(response):
        return(response['pagination']['total_pages'])

    '''{vidList} = parse_json(response) 
          resonse = json object returned by main_request function
          returns: a list of videos w/date,time, and url for each'''  
    def parse_json(response):
        vidList = []
        for item in response['results']:
            video = {
                'name':item['data']['common']['label'],
                'date': item['data']['extents']['temporal']['min'][0:10],
                'time':item['data']['extents']['temporal']['min'][11:19],
                'url':item['data']['properties']['url']}
            
            vidList.append(video)
        return(vidList)
    
    cameraName = stationInfo['Station Name']
    cprint(f' Checking for {cameraName.capitalize()} inventory...', 'blue', attrs = ['bold'])
    
    start = startDate #inclusive
    end = endDate #exclusive 
    outputName = cameraName + '.inventory.json'
    
    cwd = os.getcwd()
    path = os.path.join(cwd, 'Inputs', cameraName)
    
    if not os.path.exists(path):
        os.makedirs((path))
    
    if not os.path.exists(os.path.join(path, outputName)):
        updateArchive = False
        queryResults = []
        apiJson = main_request(cameraName, start, end, 1)
        cprint('   No inventory found, querying WebCOOS Archive...', 'yellow', attrs = ['bold'])
        t = trange(1, get_pages(apiJson) + 1, leave=True)
        for n in t:
            t.set_description(termcolor.colored("   Creating Inventory", 'blue', attrs = ['bold']))
            t.refresh() # to show immediately the update
            sleep(0.01)
            queryResults.extend(parse_json(main_request(cameraName, start, end, n)))
   
        json_object = json.dumps(queryResults)
        with open(os.path.join(path, outputName), "w") as outfile:
            outfile.write(json_object) 
        finMsg = termcolor.colored(f'     @ [{len(queryResults)} Videos Compiled]\n',
               'white', attrs = ['bold'])
        finMsg = finMsg.replace('@', termcolor.colored('Success!', 'green', attrs = ['bold']))
        print(finMsg)
        inventory = queryResults
    else:
        fname = open(os.path.join(path, outputName))
        inventory = json.load(fname)
        
        availableDates = []
        for item in inventory:
            availableDates.append(item['name'][len(cameraName)+1:-12])
            
        sDt = start in availableDates
        eDt = (datetime.strptime(end, '%Y-%m-%d')-timedelta(days=1)).strftime('%Y-%m-%d') in availableDates
        
        if sDt == True and eDt == True:
            queryArchive = False
            updateArchive = False
            cprint(('   Inventory Found!\n'), 'green', attrs = ['bold'])
            pass
        
        elif sDt == True and eDt == False:
            queryArchive = True
            updateArchive = True
            suffix = True
            start = availableDates[-1]

            exc = []
            dates = []
            for i in range(0,len(inventory)):
                dates.append(datetime.strptime(inventory[i]['date'], '%Y-%m-%d'))
                if datetime.strptime(inventory[i]['date'], '%Y-%m-%d') >= datetime.strptime(start, '%Y-%m-%d'):
                    exc.append(i)
            invUpd = inventory[0:exc[0]]
    
            exc = []
            dates = []
            for i in range(0,len(inventory)):
                dates.append(datetime.strptime(inventory[i]['date'], '%Y-%m-%d'))
                if datetime.strptime(inventory[i]['date'], '%Y-%m-%d') >= datetime.strptime(start, '%Y-%m-%d'):
                    exc.append(i)
            invUpd = inventory[0:exc[0]]
            
                
        elif sDt == False and eDt == True:
            queryArchive = True
            updateArchive = True
            suffix = False
            end = availableDates[0]
           
            exc = []
            dates = []
            for i in range(0,len(inventory)):
                dates.append(datetime.strptime(inventory[i]['date'], '%Y-%m-%d'))
                if datetime.strptime(inventory[i]['date'], '%Y-%m-%d') <= datetime.strptime(end, '%Y-%m-%d'):
                    exc.append(i)
            end = datetime.strptime(end, '%Y-%m-%d') + timedelta(days = 1)
            invUpd = inventory[exc[-1]+1:]
            
        elif sDt == False and eDt == False:
            queryArchive = True
            updateArchive = True
            suffix = None
            pass
    
        if queryArchive == True:
            queryResults = []
            apiJson = main_request(cameraName, start, end, 1)
            cprint('   Updating from WebCOOS Archive......', 'yellow', attrs = ['bold'])
            t = trange(1, get_pages(apiJson) + 1, leave=True)
            for n in t:
                t.set_description(termcolor.colored("   Updating Inventory", 'blue', attrs = ['bold']))
                t.refresh() # to show immediately the update
                sleep(0.01)
                queryResults.extend(parse_json(main_request(cameraName, start, end, n)))    
        else:
            pass

    if updateArchive == False:
        u2dInv = inventory
    
    if updateArchive == True:
        if suffix == True:
            u2dInv = invUpd + queryResults
        elif suffix == False:
            u2dInv = queryResults + invUpd 
        elif suffix == None:
            u2dInv = queryResults
        json_object = json.dumps(u2dInv)
        with open(os.path.join(path, outputName), "w") as outfile:
            outfile.write(json_object) 
        finMsg = termcolor.colored(f'     @ [{len(queryResults)} Videos Added]\n',
               'white', attrs = ['bold'])
        finMsg = finMsg.replace('@', termcolor.colored('Success!', 'green', attrs = ['bold']))
        print(finMsg)
        
    return(u2dInv)

#%% Import water level datumns from each camera's nearest NOAA station

def getWtLvlData(stationInfo, startDate, endDate):
    
    datum = stationInfo['Datum']
    if datum == 'NAVD88':
        datum = 'NAVD'
        
    station = nc.Station(stationInfo['NOAA Station ID'])
    
    dtStart = datetime.strptime(startDate, '%Y-%m-%d') #Inclusive
    dtEnd = datetime.strptime(endDate, '%Y-%m-%d') #Exclusive
    
    table = station.get_data(
        begin_date = dtStart.strftime('%Y%m%d'),
        end_date = dtEnd.strftime('%Y%m%d'),
        product = "water_level",
        datum = datum, # Accepts: MHHW, MHW, MTL, MSL, MLW, MLLW*, NAVD*, STND;   *May not be available for all sations 
        units = "metric",
        time_zone = "gmt")
    table.index.names = ['Date Time']
    headers = table.columns.tolist()
    table.rename(columns={
        headers[0]: 'Water Level', 
        headers[1]: 'Sigma',
        headers[2]: 'Data Flags', 
        headers[3]: 'QA/QC Level'
        }, inplace=True)
    table = table.reset_index()
    headers = table.columns.tolist()
    wtLvlData = table.drop(columns=[headers[2],headers[3], headers[4]])
    wtLvlData[headers[0]]=wtLvlData[headers[0]].astype(str)
    return(wtLvlData)

#%% Identify the closest video to the desired water level for each day of the date range 

def getTargetVids(stationName, availableVids, wtLvlData, wtLvl, elev, buff):         
    drop = []
    
    termW = os.get_terminal_size().columns
    if termW > 80:
        termW = 80
    
    for i in tqdm(range(len(wtLvlData)),
          desc = termcolor.colored(' Filtering by water level', 
                   'blue', attrs = ['bold']), leave = True, ncols = termW):
        if not wtLvl - buff < wtLvlData.iloc[i][1] < wtLvl + buff:
            drop.append(i)
        else:
            pass
    sleep(0.5)  
    cprint('   Success!\n', 'green', attrs=['bold'])
    
    adjDf = wtLvlData.drop(drop).reset_index(drop=True)
    
    tgtDates=[]
    drop = []
    for i in tqdm(range(len(adjDf)), desc = termcolor.colored(' Filtering by date', 
                   'blue', attrs = ['bold']), leave = True, ncols = termW):
        if '-' in adjDf.iloc[i][0]:
            if  adjDf.iloc[i][0][0:4] == '2023' or adjDf.iloc[i][0][0:4] == '2022' or adjDf.iloc[i][0][0:4] == '2021':
                dt = datetime.strptime(adjDf.iloc[i][0],'%Y-%m-%d %H:%M:%S')
            else: 
                dt = datetime.strptime(adjDf.iloc[i][0],'%m-%d-%Y %H:%M:%S')
        elif '/' in adjDf.iloc[i][0]:
            if adjDf.iloc[i][0][0:4] == '2023' or adjDf.iloc[i][0][0:4] == '2022' or adjDf.iloc[i][0][0:4] == '2021':
                dt = datetime.strptime(adjDf.iloc[i][0],'%Y/%m/%d %H:%M:%S')
            else:
                dt = datetime.strptime(adjDf.iloc[i][0],'%m/%d/%Y %H:%M:%S')
        
        hr = int(dt.strftime('%H'))
        if not 10 < hr < 24:
            drop.append(i)
        else:
            tgtDates.append([dt.strftime('%Y-%m-%d'),dt.strftime('%H%M'),])
    
    sleep(0.5)   
    cprint('   Success!\n', 'green', attrs=['bold'])
    
    tgtDf = adjDf.drop(drop).reset_index(drop=True)
    
    tgtVideos = []
    for i in tqdm(range(len(tgtDf)),desc = termcolor.colored(' Assesing remaining videos', 
                   'blue', attrs = ['bold']), leave = True, ncols = termW):
        date = tgtDates[i][0]
        year = tgtDates[i][0][0:4]
        month = tgtDates[i][0][5:7]
        day = tgtDates[i][0][8:10]
        t = tgtDates[i][1]
        dt_obj = datetime.strptime((tgtDates[i][0] + ' ' + t), '%Y-%m-%d %H%M')
        waterLvl = tgtDf.iloc[i]['Water Level']
        subStr = stationName + '-' + date + '-' + t[0:3]
        vid1 = [v for v in availableVids if subStr in v]
        if len(vid1) == 0:
            pass
        if len(vid1) == 1:
            if not vid1[0] in [tgtVideos[n][2] for n in range(len(tgtVideos))]:
                tgtVideos.append([date,'/'+year+'/'+month+'/'+day+'/'+vid1[0], vid1[0], dt_obj, waterLvl, abs(wtLvl - waterLvl)])
            else:
                pass
        if len(vid1) > 1:
            newSubStr = stationName + '-' + date + '-' + t[0:4]
            vid2 = [v for v in vid1 if newSubStr in v]
            if len(vid2) == 1:
                if not vid2[0] in [tgtVideos[n][2] for n in range(len(tgtVideos))]:
                    tgtVideos.append([date,'/'+year+'/'+month+'/'+day+'/'+vid2[0], vid2[0], dt_obj, waterLvl, abs(wtLvl - waterLvl)])
                else:
                    pass
            if len(vid2) == 0:
                m = int(newSubStr[-1])
                mi = []
                for video in vid1:
                    mi.append(int(video[-8]))
                def closest(mi, m):
                    return mi[min(range(len(mi)), key = lambda n: abs(mi[n]-m))]
                closestMin = str(closest(mi,m)) 
                newSubStr = stationName + '-' + date + '-' + t[0:3] + closestMin
                vid3 = [v for v in vid1 if newSubStr in v]
                if not vid3[0] in [tgtVideos[n][2] for n in range(len(tgtVideos))]:
                    tgtVideos.append([date,'/'+year+'/'+month+'/'+day+'/'+vid3[0], vid3[0], dt_obj, waterLvl, abs(wtLvl - waterLvl)]) 
                else:
                    pass
    sleep(0.5)
    cprint('   Success!\n', 'green', attrs=['bold'])
     
    idxName = '|'+ elev +'-waterLvl|'
    #Export target video names to a .json file       
    vidList=[]
    for item in tgtVideos:
        vidList.append(dict({'date':item[0],'videoName':item[2],'waterLvl':item[4], idxName:item[5]}))
    path = os.path.join(os.getcwd(), 'Inputs', stationName, '.tgtVids')
    
    if not os.path.exists(path):
        os.makedirs(path)
    
    fname = stationName + '.' + elev + '.tgtVids[' + str(len(vidList)) + '].json'
    with open(os.path.join(path,fname), "w") as f:
        json.dump(vidList, f)
       
    tgtVids = np.asarray(tgtVideos)
    sort = tgtVids[tgtVids[:, 5].argsort()]
    tgtVids = np.asarray(sorted(sort,key=lambda l: (l[0])))
    
    return(tgtVids)

#%% Define progress bar for rtsp video downloads

def pbar(current, total, width=80):  
  progress_message = "   In Progress: %d%% [%d / %d mb]..." % (current / total*100, current/1048576, total/1048576) # 1 Megabyte is equal to 1048576 bytes (binary)
  # Don't use print() as it will print in new line every time.
  sys.stdout.write("\r" + progress_message)
  if current == total:
      updateMsg = "   Download Complete: %d%% [%d / %d mb]... @ " % (current / total*100, current/1048576, total/1048576)
      updateMsg = updateMsg.replace('@', termcolor.colored('Done!', 'green' , attrs = ['bold']))
      sys.stdout.write("\r" + updateMsg)
      sys.stdout.flush()
  else:
      sys.stdout.flush()
  
#%% Extracts and converts file name time string into both local and UTC time information

def rtsp_datetime(saveName, date):
    
    y = saveName[-22:-18]
    mo = saveName[-17:-15]
    d = saveName[-14:-12]
    hr = saveName[-11:-9]
    m = saveName[-9:-7]
    
    dt = y + '/' + mo + '/' + d + ' '+ hr + ':' + m

    def utc2ltz(tgtDate):
        
        time_zone = pytz.timezone('US/Eastern')
        dst_date = time_zone.localize(tgtDate, is_dst=None)
        
        if bool(dst_date.dst()) is True:
            tzCode = 'EDT'
            tzAdj = timedelta(hours = -4)
            dtObjLT = tgtDate + tzAdj
        else:
            tzCode = 'EST'
            tzAdj = timedelta(hours = -5)
            dtObjLT = tgtDate + tzAdj
            
        return(dtObjLT, tzCode)
    
    #Create a utc date time object to convert utc to local time 
    dtObjUTC = datetime.strptime(dt,'%Y/%m/%d %H:%M')
    dtObjLT, tzCode = utc2ltz(dtObjUTC)

    dtInfo = {'DateTime Object (UTC)': dtObjUTC,
              'DateTime Object (LT)': dtObjLT,
              'Date':dtObjUTC.strftime('%Y-%m-%d'),
              'Time_utc':dtObjUTC.strftime('%H:%M'),
              'Time_utc2':dtObjUTC.strftime('%H%M'),
              'Time_local':dtObjLT.strftime('%H:%M'),
              'Time_local2':dtObjLT.strftime('%H%M'),
              'Year':dtObjUTC.strftime('%Y'),
              'Month':dtObjUTC.strftime('%m'),
              'Day':dtObjUTC.strftime('%d'),
              'Hour_utc':dtObjUTC.strftime('%H'), 
              'Hour_local':dtObjLT.strftime('%H'), 
              'Minute':dtObjUTC.strftime('%M'),
              'Local Timezone': tzCode,
              'Date Time (local) String 1':dtObjLT.strftime('%Y%m%d_%H%M'), 
              'Date Time (local) String 2':dtObjLT.strftime('%Y-%m-%d_%H%M'), 
              'Date Time (local) String 3':dtObjLT.strftime('%Y-%m-%d %H:%M:00'),
              'Date Time (utc) String 1':dtObjUTC.strftime('%Y%m%d_%H%M'),
              'Date Time (utc) String 2':dtObjUTC.strftime('%Y-%m-%d_%H%M'),
              'Date Time (utc) String 3':dtObjUTC.strftime('%Y-%m-%d %H:%M:00')
              } 
    
    return(dtInfo)

#%% Analizes successfully processed image products for shorelines and finds beach transect pixel widths  

def procShorelines(stationInfo, photo, imgType):
    
    if imgType == 'avg':
        msg = '   Time-Averaged: '
    elif imgType == 'brt':
        msg = '   Brightest-Pixel: '
    
    class Spinner():
        busy = False
        delay = 0.1
        
        @staticmethod
        def spinning_cursor():
            while 1: 
                for cursor in '|/-\\': yield cursor
    
        def __init__(self, delay=None):
            self.spinner_generator = self.spinning_cursor()
            if delay and float(delay): self.delay = delay
            self.msg = msg
    
        def spinner_task(self):
            while self.busy:
                sys.stdout.write('\r'+ msg + next(self.spinner_generator))
                sys.stdout.flush()
                time.sleep(self.delay)
                sys.stdout.write('\b')
                sys.stdout.flush()
    
        def __enter__(self):
            self.busy = True
            threading.Thread(target=self.spinner_task).start()
    
        def __exit__(self, exception, value, tb):
            self.busy = False
            time.sleep(self.delay)
            if exception is not None:
                return False
    

    with Spinner():
        try:
            stationInfo, roi, thresh, contour, figTranSl, tranSl = find.obliqueShoreline(
                stationInfo, photo, imgType)
            stationInfo, figBPW_avg, bpwAvg = plot.figBPW(stationInfo, tranSl, photo, imgType)
            cprint('\bSuccess!', 'green', attrs = ['bold'])
        except:
            cprint('\bFailed.', 'red', attrs = ['bold'])
            pass
        
    plt.close('all')
        
    return(stationInfo, roi, thresh, contour, figTranSl, tranSl, figBPW_avg, bpwAvg)

#%% Downloads and processes targeted video files

def procTgtVids(stationInfo, tgtVids, inventory, runTime):
    
    termW = os.get_terminal_size().columns
    if termW > 80:
        termW = 80

    stationName = stationInfo['Station Name']
    procTimes = []
    failedVids = []
    successfulVids = np.empty((0,2))
    done = False
    firstVid = False
    n = 0       
    group = inventory[0]['url'].split('/')[8]
    archiveUrl = ('https://s3.us-west-2.amazonaws.com/webcoos/media/sources/webcoos/groups/' + group + '/assets/'+ 
                         stationName + '/feeds/raw-video-data/products/video-archive/elements')         
    
    outputDir = os.path.join(os.getcwd(), 'Inputs', stationName, '.vids')
    if not os.path.exists(outputDir):
        os.makedirs(outputDir)
    
    # for i in range(0,len(tgtVids)):
    for i in range(0,1):
        startTime = time.time()
        vidName = tgtVids[i][2]
        dt_obj = tgtVids[i][3]
        stationInfo['Tide Level (m)'] = tgtVids[i][4]      
        url = archiveUrl + tgtVids[i][1]
        flag = False
        
        if firstVid == False:
            pass
        elif firstVid == True:
            if vidName in successfulVids[:,0]:
                flag = True
            else:
                dt_comp =  dt_obj - successfulVids[len(successfulVids)-1,1]
                if abs(dt_comp.total_seconds()) < 10800:
                    flag = True
                else:
                    pass
        
        res = [r for r in failedVids if vidName[:-12] in r]
        if len(res) >= 3:
            flag = True
        
        if flag == True:
            pass
        elif flag == False:
            n = n + 1
            msg = ('Processing Video #' + str(n) + ': ' + vidName + ' [' + str(round((i/len(tgtVids))*100,3)) + '%]')
            print('\n' + ('-'*termW))     
            cprint(' '*centerTxt(msg)[0] + msg + ' '*centerTxt(msg)[1],'green', attrs = ['bold'])
            print(('-'*termW)+'\n' )   
            
            try:        
                cprint(' Downloading video...', 'blue', attrs=['bold'])
                vid = wget.download(url, out=outputDir, bar = pbar)
                cprint('\n   Checking File...', 'yellow', attrs=['bold'])
                vidTest = cv2.VideoCapture(vid)
                if not vidTest.isOpened():
                    cprint('   File corrupted... skipping video.', 'red', attrs=['bold'])
                    vidTest.release()
                    os.remove(vid)
                elif vidTest.get(cv2.CAP_PROP_FRAME_COUNT)/vidTest.get(cv2.CAP_PROP_FPS) < 1:
                    cprint('   File corrupted... skipping video.', 'red', attrs=['bold'])              
                    vidTest.release()
                    os.remove(vid)
                else:
                    cprint('   Success!', 'green', attrs=['bold'])
                    vidTest.release()
                
                date = dt_obj.strftime('%Y-%m-%d')
                dtInfo = rtsp_datetime(vidName, date)
                
                stationType = 'existing'
                stationInfo['Datetime Info'] = dtInfo
                stationInfo['Station Type'] = stationType
                stationInfo['Rectified Image'] = False
                
                if done == False:
                    #snap, photoAvg, photoVar, photoBrt = get_procImgs(stationInfo, vid, 'All')
                    snap, photoAvg, photoBrt = genImgProducts(stationInfo, vid, 'Timex & Brt') 
                else:
                    pass
                
                cprint('\n Extracting Shorelines...', 'blue', attrs=['bold'])
                time.sleep(1)
                
                (stationInfo, avgROI, avgThresh, 
                avgContour, figAvgTranSl, avgTranSl,
                figBPW_avg, bpwAvg) = procShorelines(stationInfo, photoAvg, 'avg')
                
                (stationInfo, brtROI, brtThresh, 
                brtContour, figBrtTranSl, brtTranSl,
                figBPW_brt, bpwBrt) = procShorelines(stationInfo, photoAvg, 'brt')
                
                    
                if firstVid == False:
                    firstVid = True
                else:
                    pass
                    
                procTime = round((time.time() - startTime)/60,2)
                procTimes.append(procTime)
        
                msg = '\n Video Successfully Processed! %\n'
                msg = msg.replace('%', termcolor.colored('[' + str(procTime) + ' minutes]', 'white', attrs = ['bold']))
                cprint((msg + ' '*(centerTxt(msg)[0] + centerTxt(msg)[1] -1) + '|'),'green', attrs=['bold'])
            
                if done == False:
                    os.remove(vid)
                else:
                    pass
                
            except Exception as ex:
                try:
                    exTxt = (type(ex).__name__ + ': ' + ex.args[0] + '.')
                    failedVids.append(vidName)
                    try:
                        os.remove(vid)
                    except:
                        pass
                except:
                    exTxt = 'Unknown'
                    failedVids.append(vidName)
                    try:
                        os.remove(vid)
                    except:
                        pass
                cprint('\n   An Error has occured!\n', 'red', attrs = ['bold'])
                print(exTxt)
                cprint('\n   Deleting video and moving on...\n', 'yellow', attrs = ['bold'])  
                
    return(procTime)
    
#%% Used to center text in console output

def centerTxt(string):
    
    string = re.sub(
            r'[\u001B\u009B][\[\]()#;?]*((([a-zA-Z\d]'
            '*(;[-a-zA-Z\d\/#&.:=?%@~_]*)*)?\u0007)|('
            '(\d{1,4}(?:;\d{0,4})*)?[\dA-PR-TZcf-ntqr'
            'y=><~]))', '', string)
     
    termW = os.get_terminal_size().columns
    if termW > 80:
        termW = 80
        
    space = termW - len(string)
    txtSpacers = (math.floor(space/2), math.ceil(space/2))  
    return (txtSpacers)

#%% Prints station complete message

def stationCompleteMsg(s, i, stationName, wtLvl, runTime, termW):
    print('\n\n' + (termcolor.colored('=','red', attrs=['bold'])*termW))
    msgStr = f"{stationName.capitalize()} [{wtLvl}] finished in % and @."    
    msgStr = msgStr.replace('%', termcolor.colored(str(round(divmod(runTime[i,s],60)[0])) + ' hours', 'green', attrs = ['bold']))
    msgStr = msgStr.replace('@', termcolor.colored(str(round(divmod(runTime[i,s],60)[1],2)) + ' minutes', 'green', attrs = ['bold']))
    cprint(' '*centerTxt(msgStr)[0] + msgStr + ' '*centerTxt(msgStr)[1], 'white', attrs=['bold'])
    print((termcolor.colored('=','red', attrs=['bold'])*termW))

#%% Prints program complete messagePrints station complete message

def programCompleteMsg(runTime, termW):
    finMsg = termcolor.colored('PROGRAM COMPLETED', 'white', attrs = ['bold','underline'])
    finMsg = termcolor.colored('|','white') +' '*(centerTxt(finMsg)[0]-1) + finMsg  + ' '*centerTxt(finMsg)[1]
    print('\n ' + '_'*(termW-2))
    print('|' + ' '*(termW-2) +'|')
    cprint((finMsg[:-1] + '|'),'green', attrs = ['bold'])
    print('|' + ' '*(termW-2) +'|')
    totTime = divmod(np.sum(runTime),60)
    msg = "| Program finished in: % and @"    
    msg = msg.replace('%', termcolor.colored((str(round(totTime[0]))+' hours'), 'green', attrs = ['bold']))
    msg = msg.replace('@', termcolor.colored((str(round(totTime[1],2))+' minutes'), 'green', attrs = ['bold']))
    cprint((msg + ' '*(centerTxt(msg)[0] + centerTxt(msg)[1] -1) + '|'),'white', attrs=['bold'])
    print('|' + ' '*(termW-2) +'|')
    tmsg = '| It is currently: %'
    tmsg = tmsg.replace('%', termcolor.colored((datetime.now().strftime("%I:%M %p LST on %A %B %d, %Y")), 'blue', attrs = ['bold']))
    cprint((tmsg + ' '*(centerTxt(tmsg)[0] + centerTxt(tmsg)[1] -1) + '|'), 'white', attrs=['bold'])
    print('|' + ' '*(termW-2) +'|')
    print('|' + '_'*(termW-2) +'|')