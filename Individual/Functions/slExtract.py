# -*- coding: utf-8 -*-
"""
Created on Fri Oct  1 12:13:24 2021

@author: jeb2694
"""
import os
import json
import numpy as np

def extract(stationInfo, rmb, maskedImg, threshInfo, imgType):
    
    cwd = os.getcwd()
    
    stationname = stationInfo['Station Name']
    slTransects = stationInfo['Shoreline Transects']
    tideLvl = stationInfo['Tide Level (m)']
 
    
    dtInfo = stationInfo['Datetime Info']
    date = dtInfo['Date']
    
    xt = np.asarray(slTransects['x'])
    yt = np.asarray(slTransects['y'])
    
    orn = stationInfo['Orientation']
    
    thresh = threshInfo['Thresh'] 
    thresh_otsu = threshInfo['Otsu Threshold']
    thresh_weightings = threshInfo['Threshold Weightings']

    dims = ((len(rmb[1]), len(rmb)))
    
    #width and height in pixels 
    w = dims[0]
    h = dims[1]

    length = len(yt) #- 1
    trsct = range(0, length)

    values = [0]*length
    revValues = [0]*length
    yList = [0]*length
    xList = [0]*length
      
    if orn == 0:
        def find_intersect(List, thresh):
            res = [k for k, x in enumerate(List) if x > thresh_otsu]
            return None if res == [] else res[0]
    
        for i in trsct:
            x = int(xt[i][0])
            yMax = round(yt[i][1])
            yMin = round(yt[i][0])
            y = yMax-yMin
            yList[i] = np.zeros(shape=y)
            val = [0]*(yMax-yMin)
            for j in range(0,len(val)):
                k = yMin + j
                val[j] = rmb[k][x]
            val = np.array(val)
            values[i] = val
        
        intersect = [0]*len(xt)  
        idx = [0]*len(xt) 
        Pts = [0]*len(xt) 
        xPt = [0]*len(xt)
        yPt = [0]*len(xt)  
        
        for i in range(0, len(values)):
            intersect[i] = find_intersect(values[i], thresh_otsu)
            idx[i] = np.where(values[i][intersect[i]] == values[i])
            n = len(idx[i][0])-1
            if len(idx[i][0]) == 0:
                yPt[i] = None
                xPt[i] = None
            else:
               yPt[i] = min(yt[i]) + idx[i][0][n]
               xPt[i] = int(xt[i][0])
               Pts[i] = (xPt[i], yPt[i]) 
            
            areaAvg = [0]*len(Pts)
            sample = np.zeros((21,21))
            
            for n in range(0,len(Pts)):
                if Pts[n] == 0:
                    pass
                else:
                    orginX = int(Pts[n][0])
                    orginY = int(Pts[n][1])
                    xBounds = range(orginX - 10, orginX + 11)
                    yBounds = range(orginY - 10, orginY + 11)
                    for j in yBounds:
                        if j >= h:
                            j = h - 1
                        a = j - orginY
                        for k in xBounds:
                            if k >= w:
                                k = w - 1
                            b = k - orginX
                            sample[a][b] = rmb[j][k]
                    areaAvg[n] = np.mean(sample)
        
            buffer = (float(thresh_otsu) * .20)
            exc = {0}
            for i in range(0,len(Pts)):
                if abs((buffer + thresh_otsu)) > abs(areaAvg[i]) > abs((buffer - thresh_otsu)):
                    pass
                else:
                    exc.add(i)
                                            
            truePts = [v for i, v in enumerate(Pts) if i not in exc]  
                
            threshX = [0]*len(truePts)
            threshY = [0]*len(truePts)
            for i in range(0, len(truePts)):
                threshX[i] = truePts[i][0]
                threshY[i] = truePts[i][1]
             
            threshX = np.array(threshX)
            threshY = np.array(threshY)
            
            shoreline = np.vstack((threshX,threshY)).T
    else:
        def find_intersect(List, thresh):
            res = [k for k, x in enumerate(List) if x < thresh_otsu]
            return None if res == [] else res[0]
        
        for i in trsct:
            xMax = round(xt[i][0])
            y = int(yt[i][0])
            yList[i] = np.full(shape=xMax, fill_value= y)
            xList[i] = np.arange(xMax)
            values[i] =rmb[y][0:xMax]
            revValues[i] = rmb[y][::-1]
            
        intersect = [0]*len(yt)  
        idx = [0]*len(yt) 
        Pts = [0]*len(yt) 
        xPt = [0]*len(yt)
        yPt = [0]*len(yt)  
        
        for i in range(0, len(values)):
            intersect[i] = find_intersect(revValues[i], thresh_otsu)
            idx[i] = np.where(revValues[i][intersect[i]] == values[i])
            n = len(idx[i][0])-1
            if len(idx[i][0]) == 0:
                xPt[i] = None
                yPt[i] = None
            else:
               xPt[i] = idx[i][0][n]
               yPt[i] = int(yt[i][0])
               Pts[i] = (xPt[i], yPt[i]) 
            
            areaAvg = [0]*len(Pts)
            sample = np.zeros((21,21))
            
            for i in range(0,len(Pts)):
                if Pts[i] == 0:
                    pass
                else:
                    orginX = Pts[i][0]
                    orginY = Pts[i][1]
                    xBounds = range(orginX - 10, orginX + 11)
                    yBounds = range(orginY - 10, orginY + 11)
                    for j in yBounds:
                        a = j - orginY
                        for k in xBounds:
                            b = k - orginX
                            sample[a][b] = rmb[j][k]
                    areaAvg[i] = np.mean(sample)

            buffer = (float(thresh_otsu) * .20)
            exc = {0}
            for i in range(0,len(Pts)):
                if abs((buffer + thresh_otsu)) > abs(areaAvg[i]) > abs((buffer - thresh_otsu)):
                    pass
                else:
                    exc.add(i)
                                       
            truePts = [v for i, v in enumerate(Pts) if i not in exc]  
                
            threshX = [0]*len(truePts)
            threshY = [0]*len(truePts)
            for i in range(0, len(truePts)):
                threshX[i] = truePts[i][0]
                threshY[i] = truePts[i][1]
             
            threshX = np.array(threshX)
            threshY = np.array(threshY)
            
            shoreline = np.vstack((threshX,threshY)).T
    
    #Package relevant shoreline variables for exportation
    slVars = {
        'Station Name':stationname, 
        'Date':date, 
        'Time Info':dtInfo, 
        'Thresh':thresh, 
        'Otsu Threshold':thresh_otsu,
        'Shoreline Transects': slTransects,
        'Threshold Weightings':thresh_weightings,
        'Shoreline Points':shoreline,
        'Tide Level (m)': tideLvl
        }

    #Objects of type datetime and ndarray are not JSON serializable
    try:
        del slVars['Time Info']['DateTime Object (UTC)']
        del slVars['Time Info']['DateTime Object (LT)']
        del slVars['Time Info']['DateTime Object']
    except:
        pass
    
    if type(slVars['Shoreline Transects']['x']) == np.ndarray:
        slVars['Shoreline Transects']['x'] = slVars['Shoreline Transects']['x'].tolist()
        slVars['Shoreline Transects']['y'] = slVars['Shoreline Transects']['y'].tolist()
    else:
        pass
    
    slVars['Shoreline Points'] = slVars['Shoreline Points'].tolist()
    
    # fig_RecSL = pf.pltFig_recSL(stationInfo, slVars, recImg, imgType)
    fname = (stationname.lower() + '.' + dtInfo['Date Time (utc) String 2'] + '.' + imgType + '.slVars.json')
    
    saveDir = os.path.join(cwd, 'Outputs', stationname, date, dtInfo['Time_utc2'], imgType)
    
    #Export shoreline variables to a .json file
    with open(os.path.join(saveDir, fname), "w") as f:
        json.dump(slVars, f)
            
    # Update list of used modules
    mod = ['os' , 'json', 'numpy']

    mods = stationInfo['Modules Used']
    for n in range(len(mod)):
        if mod[n] not in mods:
            mods.append(mod[n])
    stationInfo['Modules Used'] = mods
    
    return(stationInfo, shoreline)
    
########################################################################    

def extractRec(stationInfo, rmb, maskedImg, thresh):
        
    recTransects = stationInfo['Rectified Transects']
    
    xtRec = recTransects['x']
    ytRec = recTransects['y']
    
    h = stationInfo['RecImg Dimensions']['h'] - 1
         
    values = [0]*len(ytRec)
    revValues = [0]*len(ytRec)
    yList = [0]*len(ytRec)

    def find_intersect(List, thresh):
        res = [k for k, x in enumerate(List) if x > thresh]
        return None if res == [] else res[0]

    for i in range(0, len(ytRec)):
        x = int(xtRec[i][0])
        yMin = round(ytRec[i][0])
        yMax = round(ytRec[i][1])
        y = yMax-yMin
        yList[i] = np.zeros(shape=y)
        val = [0]*(yMax-yMin)
        for j in range(0,len(val)):
            k = yMin + j
            val[j] = rmb[k][x]
        val = np.array(val)
        values[i] = val
        revValues[i] = values[i][::-1]
        
    intersect = [0]*len(xtRec)  
    idx = [0]*len(xtRec) 
    Pts = [0]*len(xtRec) 
    xPt = [0]*len(xtRec)
    yPt = [0]*len(xtRec)  
    
    for i in range(0, len(values)):
        intersect[i] = find_intersect(values[i], thresh)
        idx[i] = np.where(values[i][intersect[i]] == values[i])
        n = len(idx[i][0])-1
        if len(idx[i][0]) == 0:
            yPt[i] = None
            xPt[i] = None
        else:
           yPt[i] = min(ytRec[i]) + idx[i][0][n]
           xPt[i] = int(xtRec[i][0])
           Pts[i] = (xPt[i], yPt[i]) 
        
        areaAvg = [0]*len(Pts)
        sample = np.zeros((21,21))
        
        for i in range(0,len(Pts)):
            if Pts[i] == 0:
                pass
            else:
                orginX = int(Pts[i][0])
                orginY = int(Pts[i][1])
                if orginY + 11 > h:
                    xBounds = range(orginX - 10, orginX + (h-orginY))
                    yBounds = range(orginY - 10, orginY + (h-orginY))
                else:
                    xBounds = range(orginX - 10, orginX + 11)
                    yBounds = range(orginY - 10, orginY + 11)
                
                
                for j in yBounds:
                    a = j - orginY
                    for k in xBounds:
                        b = k - orginX
                        sample[a][b] = rmb[j][k]
                areaAvg[i] = np.mean(sample)
    
        buffer = (float(thresh) * .25)
        exc = {0}
        for i in range(0,len(Pts)):
            if abs((buffer + thresh)) > abs(areaAvg[i]) > abs((buffer - thresh)):
                pass
            else:
                exc.add(i)
                                        
        truePts = [v for i, v in enumerate(Pts) if i not in exc]  
            
        threshX = [0]*len(truePts)
        threshY = [0]*len(truePts)
        for i in range(0, len(truePts)):
            threshX[i] = truePts[i][0]
            threshY[i] = truePts[i][1]
         
        threshX = np.array(threshX)
        threshY = np.array(threshY)
        
        shoreline = np.vstack((threshX,threshY)).T
        
        # Update list of used modules
        mod = ['os' , 'json', 'numpy']

        mods = stationInfo['Modules Used']
        for n in range(len(mod)):
            if mod[n] not in mods:
                mods.append(mod[n])
        stationInfo['Modules Used'] = mods
        
    return(stationInfo, shoreline)       

 