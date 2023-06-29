# -*- coding: utf-8 -*-
"""
Created on Thu Oct  7 11:28:09 2021

@author: jeb2694
"""
import os
import csv
import math
import numpy as np
import matplotlib.pyplot as plt
# import matplotlib.patheffects as pe
from win32api import GetSystemMetrics
from scipy.interpolate import interp1d
from mpl_toolkits.axes_grid1 import make_axes_locatable

#%%

def figImageTransects(snap, hznPts, stationInfo):
    
    stationname = stationInfo['Station Name']
    
    slTransects = stationInfo['Shoreline Transects']
    xt = slTransects['x']
    yt = slTransects['y']
    
    plt.ioff()
    fig, ax = plt.subplots(figsize=(14, 9.5))
    ax.imshow(snap, interpolation='nearest')
    ax.set_title((stationname + ' - Station Setup\n09/05/2021 at 11:00 AM'),
          fontsize = 16)
    ax.set_xlabel("Image Width (pixels)", fontsize = 14)
    ax.set_ylabel("Image Height (pixels)", fontsize = 14)
    ax.tick_params(axis = 'both', which = 'major', labelsize = 12)
    ax.tick_params(axis = 'both', which = 'minor', labelsize = 12)
    ax.set_xlim(0, len(snap[1]))
    ax.set_ylim(len(snap)-1, 0)
    
    #Plot the transects
    for i in range(0,len(xt)):
        if i == 0: #Plot only one transect with a label (for the legend)  
            ax.plot(xt[i,:], yt[i,:], color = 'black', linewidth = 1, 
                     label = 'Shorline Transects', zorder = 0 )   
        else:
            ax.plot(xt[i,:], yt[i,:], color = 'black', linewidth = 1, 
                 label = '_nolegend_', zorder = 2)
    
    #Plot the dune line
    xi = stationInfo['Dune Line Info']['Dune Line Points'][:,0]
    py = stationInfo['Dune Line Info']['Dune Line Points'][:,1]
    ax.plot(xi, py, color = 'blue', linewidth = 1.5, label = 'Dune Line', 
             zorder = 4)
    
    #Plot the horizon line
    hzn1 = hznPts[0]
    hzn2 = hznPts[1]
    ax.plot((hzn1[0],hzn2[0]),(hzn1[1],hzn2[1]), color = 'red', 
             linewidth = 1.5, label = 'Horizon')
    
    # #Plot the test points
    # for i in range(0,len(tstX)):
    #     if i == 0: #Plot only test point with a label (for the legend)   
    #         plt.scatter(tstX[i], tstY[i], 5, color = 'lime', linewidths = 0.5,
    #                 label = 'Test Point(s)', edgecolors ='k', zorder = 10 )
    #     else:
    #         plt.scatter(tstX[i], tstY[i], 5, color = 'lime', linewidths = 0.5,
    #             label = '_nolegend_', edgecolors ='k', zorder = 10 )
            
    #Add the legend
    ax.legend(prop={'size': 14}, numpoints = 1)
    
    #Save the plot as a .png file 
    cwd = os.getcwd()
    savePath = os.path.join(cwd, 'Inputs', '.StationConfigs', '.setupImgs')   
    
    if not os.path.exists(savePath):
        os.mkdir(savePath)
    
    saveName = (stationname + ".setup.png")
    
    plt.savefig(os.path.join(savePath, saveName), bbox_inches = 'tight', dpi=400)
    #Show/Close the plot
    plt.show()
    plt.close('all')
    plt.ion()
    
    # Update list of used modules
    mod = ['os' , 'csv', 'math', 'numpy', 'matplotlib','win32api', 'scipy', 'mpl_toolkits']
    mods = stationInfo['Modules Used']
    for n in range(len(mod)):
        if mod[n] not in mods:
            mods.append(mod[n])
    stationInfo['Modules Used'] = mods
    
    return(stationInfo)

#%%
def figROI(stationInfo, photo, maskedImg, xs, ys, imgType):
        
    stationname = stationInfo['Station Name']
    snameStr = stationInfo['Station Name String']
    
    dtInfo = stationInfo['Datetime Info']
   
    date = dtInfo['Date']
    dateStr = (date[5:7]+ '/' + date[8:10]+ '/' + date[0:4])
    time = dtInfo['Time_utc2']
    
    if imgType == 'avg':
        source = 'Time Averaged'
    if imgType == 'brt': 
        source = 'Brightest Pixel'
    if imgType == 'rec':
        source = 'Rectified Image'
    if imgType == 'snap':
        source = 'Snapshot'
    
    if imgType == 'avg' or imgType == 'brt' or imgType == 'snap':
        rmb = maskedImg[:,:,0] - maskedImg[:,:,2]
        
        plt.ioff()
        figROI, (ax1, ax2) = plt.subplots(1, 2, figsize=(12,9))
        figROI.canvas.set_window_title('ROI Masking')
        ax1.imshow(photo)
        ax1.plot(xs,ys, 'r--', label = 'ROI Boundaries') 
        ax1.set_title(('Region of Interest (ROI)'), fontsize = 14)
        ax1.set_xlabel('Image Width (pixels)')
        ax1.set_ylabel('Image Height (pixels)')
        ax1.legend(prop={'size': 9}, loc=2)
        ax1.tick_params(axis = 'both', which = 'major', labelsize = 10)
        ax1.tick_params(axis = 'both', which = 'minor', labelsize = 10)
        im2 = ax2.imshow(rmb, cmap=plt.get_cmap('viridis'))
        ax2.plot(xs,ys, 'r--', label = 'ROI Boundaries') 
        ax2.set_title(('Red - Blue ROI Masking'), fontsize = 14)
        ax2.set_xlabel('Image Width (pixels)')
        ax2.set_ylabel('Image Height (pixels)')
        ax2.legend(prop={'size': 9}, loc=2)
        ax2_divider = make_axes_locatable(ax2)
        ax2.tick_params(axis = 'both', which = 'major', labelsize = 10)
        ax2.tick_params(axis = 'both', which = 'minor', labelsize = 10)
        cax2 = ax2_divider.append_axes("right", size="5%", pad="2%")
        figROI.colorbar(im2, cax=cax2)
        figROI.suptitle(('Region of Interest (' + source + ')\n' + snameStr + 
                         ' - ' + dateStr + ' at ' + time[:2] + ':' + time[2:] + 
                         ' UTC'), fontsize = 16, y = 0.77)
        plt.tight_layout()
    
    elif imgType == 'rec':
        
        rmb = maskedImg[:,:,0] - maskedImg[:,:,2]
        
        plt.ioff()
        figROI, (ax1, ax2) = plt.subplots(1, 2, figsize=(12,9))
        figROI.canvas.set_window_title('ROI Masking')
        ax1.imshow(np.flipud(photo),origin='lower')
        ax1.plot(xs,ys, 'r--', label = 'ROI Boundaries') 
        ax1.set_title(('Region of Interest (ROI)'), fontsize = 14)
        ax1.set_xlabel('Alongshore Distance (meters)')
        ax1.set_ylabel('Crossshore Distance (meters)')
        ax1.legend(prop={'size': 9}, loc=2)
        ax1.tick_params(axis = 'both', which = 'major', labelsize = 10)
        ax1.tick_params(axis = 'both', which = 'minor', labelsize = 10)
        im2 = ax2.imshow(np.flipud(rmb), cmap=plt.get_cmap('viridis'),origin='lower')
        ax2.plot(xs,ys, 'r--', label = 'ROI Boundaries') 
        ax2.set_title(('Red - Blue ROI Masking'), fontsize = 14)
        ax2.set_xlabel('Alongshore Distance (meters)')
        ax2.set_ylabel('Crossshore Distance (meters)')
        ax2.legend(prop={'size': 9}, loc=2)
        ax2_divider = make_axes_locatable(ax2)
        ax2.tick_params(axis = 'both', which = 'major', labelsize = 10)
        ax2.tick_params(axis = 'both', which = 'minor', labelsize = 10)
        cax2 = ax2_divider.append_axes("right", size="5%", pad="2%")
        figROI.colorbar(im2, cax=cax2)
        figROI.suptitle(('Region of Interest (' + source + ')\n' + snameStr + 
                         ' - ' + dateStr + ' at ' + time[:2] + ':' + time[2:] + 
                         ' UTC'), fontsize = 16, y = 0.77)
        plt.tight_layout()  

    cwd = os.getcwd()
    savePath = os.path.join(cwd, 'Outputs', stationname, date, time, imgType)
    
    if not os.path.exists(savePath):
        os.makedirs(savePath)
    
    saveName = (stationname + '.' + date + '_' + time + '.' + 'ROI-'
                + imgType + '.png')
    plt.savefig(os.path.join(savePath, saveName), bbox_inches = 'tight', dpi=400)
    
    plt.close()
    
    # Update list of used modules
    mod = ['os' , 'csv', 'math', 'numpy', 'matplotlib','win32api', 'scipy', 'mpl_toolkits']
    mods = stationInfo['Modules Used']
    for n in range(len(mod)):
        if mod[n] not in mods:
            mods.append(mod[n])
    stationInfo['Modules Used'] = mods
    
    return(stationInfo, figROI)

#######################################

def figThresh(stationInfo, pdfLocs, pdfVals, peakX, 
              peakY, thresh, thresh_otsu, imgType):
    
    stationname = stationInfo['Station Name']
    snameStr = stationInfo['Station Name String']
    
    dtInfo = stationInfo['Datetime Info']
    
    date = dtInfo['Date']
    dateStr = (date[5:7]+ '/' + date[8:10]+ '/' + date[0:4])
    time = dtInfo['Time_utc2']
    
    if imgType == 'avg':
        source = 'Time Averaged'
    if imgType == 'brt': 
        source = 'Brightest Pixel'
    if imgType == 'snap':
        source = 'Snapshot'
    
    plt.ioff()
    figThresh, ax = plt.subplots()
    ax.set_box_aspect(1)
    figThresh.canvas.set_window_title('Thresholds')
    
    plt.title(('Pixel Value Density and Threshold Values (' + source + ')\n' 
               + snameStr + ' - ' + dateStr + ' at ' + time[:2] + ':' + 
               time[2:] + ' UTC'), fontsize = 11 )
    
    plt.plot(pdfLocs, pdfVals, color='k', lw=1, label = 'Pixel Distribution')
    plt.scatter(peakX, peakY, color = 'None', edgecolors = 'r',
                label = 'Peaks')
    plt.xlabel("Pixel Value", fontsize = 10)
    plt.ylabel("Density", fontsize = 10)
    plt.tick_params(axis = 'both', which = 'major', labelsize = 8)
    plt.tick_params(axis = 'both', which = 'minor', labelsize = 8)
    bottom, top = plt.ylim()
    #plt.plot((thresh, thresh), (bottom, top), 'g--', label = 'Thresh' )
    plt.plot((thresh_otsu, thresh_otsu), (bottom, top), 'b--',
             label = 'Otsu Threshold' )
    plt.legend(prop={'size': 8})
    plt.tight_layout()

    cwd = os.getcwd()
    savePath = os.path.join(cwd, 'Outputs', stationname, date, time, imgType)
    saveName = (stationname + '.' + date + '_' + time + '.' + 'Thresh-'
                + imgType + '.png')
    plt.savefig(os.path.join(savePath, saveName), bbox_inches = 'tight', dpi=400)
    
    plt.close()
    
    # Update list of used modules
    mod = ['os' , 'csv', 'math', 'numpy', 'matplotlib','win32api', 'scipy', 'mpl_toolkits']
    mods = stationInfo['Modules Used']
    for n in range(len(mod)):
        if mod[n] not in mods:
            mods.append(mod[n])
    stationInfo['Modules Used'] = mods
    
    return(stationInfo, figThresh)

#######################################

def figTranSl(stationInfo, photo, tranSL, imgType):
    
    stationname = stationInfo['Station Name']
    snameStr = stationInfo['Station Name String']
    
    dtInfo = stationInfo['Datetime Info']
    
    date = dtInfo['Date']
    time = dtInfo['Time_utc2']
        
    Di = stationInfo['Dune Line Info']
    duneInt = np.asarray(Di['Dune Line Interpolation'])
    
    xi = duneInt[:,0]
    py = duneInt[:,1]
        
    plt.ioff()
    figTranSl = plt.figure()
    figTranSl.canvas.set_window_title('Transect Shorline Detection')
    plt.imshow(photo, interpolation = 'nearest')
    plt.xlabel("Image Width (pixels)", fontsize = 10)
    plt.ylabel("Image Height (pixels)", fontsize = 10)
    plt.tick_params(axis = 'both', which = 'major', labelsize = 8)
    plt.tick_params(axis = 'both', which = 'minor', labelsize = 8)
    plt.plot(tranSL[:,0], tranSL[:,1], color = 'r', linewidth = 2, 
         label = 'Detected Shoreline')

    plt.plot(xi, py, color = 'blue', linewidth = 2, label = 'Baseline', 
         zorder = 4)  
 
    #plt.scatter(tstX[:-2], tstY[:-2], 3, color = 'lime', linewidths = 0.5,
    #            label = 'Test Points', edgecolors ='k', zorder = 10 )
    
    if imgType == 'avg':
        source = 'Time Averaged'
    if imgType == 'brt': 
        source = 'Brightest Pixel'
    if imgType == 'snap':
        source = 'Snapshot'
        
    dateStr = (date[5:7]+ '/' + date[8:10]+ '/' + date[0:4])
    
    plt.title(('Transect Based Shoreline Detection (' + source + ')\n' + snameStr + 
               ' - ' + dateStr + ' at ' + time[:2] + ':' + 
               time[2:] + ' UTC'), fontsize = 12)
    plt.legend(prop={'size': 9})
    plt.tight_layout()
    
    cwd = os.getcwd()
    savePath = os.path.join(cwd, 'Outputs', stationname, date, time, imgType)
    saveName = (stationname + '.' + date + '_' + time + '.' + 'tranSL-'
                + imgType + '.png')
    plt.savefig(os.path.join(savePath, saveName), bbox_inches = 'tight', dpi=400)
    
    plt.close()
    
    # Update list of used modules
    mod = ['os' , 'csv', 'math', 'numpy', 'matplotlib','win32api', 'scipy', 'mpl_toolkits']
    mods = stationInfo['Modules Used']
    for n in range(len(mod)):
        if mod[n] not in mods:
            mods.append(mod[n])
    stationInfo['Modules Used'] = mods
    
    return(stationInfo, figTranSl)

#######################################

def figBPW(stationInfo, tranSL, photo, imgType):
    
    stationname = stationInfo['Station Name']
    snameStr = stationInfo['Station Name String']
        
    slIntC = interp1d(tranSL[:,0], tranSL[:, 1], bounds_error = False)
       
    #get the dimensions (resolution) of the snapshot
    dims = ((len(photo[1]), len(photo)))
    
    #width and height in pixels 
    w = dims[0]
        
    slX = np.arange(0, w , 1)
    slY = slIntC(slX)
    slY = np.round(slY)
    slC = np.vstack((slX,slY)).T
    
    slTransects = stationInfo['Shoreline Transects']
    
    xt = np.asarray(slTransects['x'])
    yt = np.asarray(slTransects['y'])
    
    beachwidths = [0]*len(xt)
    
    orn = stationInfo['Orientation']
    
    if orn == 0:
        Di = stationInfo['Dune Line Info']
        duneInt = np.asarray(Di['Dune Line Interpolation'])
        
        xi = duneInt[:,0]
        py = duneInt[:,1]
        
        exc = []
        
        #Index Transects that do not intercept the extracted shoreline
        for i in range(0, len(xt)):
            if xt[i,0] < np.min(tranSL[:,0]) or xt[i,0] > np.max(tranSL[:,0]):
                exc.append(i)
        
        exc.sort(reverse = True)  
        
        #Remove transects that do not intercept the extracted shoreline
        for i in range(len(exc)):
            xt = np.delete(xt, exc[i], 0)
            yt = np.delete(yt, exc[i], 0)
        
        idx = [0]*len(xt)
        for i in range(0, len(xt)):
            if yt[i,0] > np.nanmax(slC[:,1]):
                idx[i] = np.NaN
            else:
                yt[i,0] = slC[int(xt[i,0])][1]  
            
        slWx = np.vstack((xt[:,0],xt[:,1])).T 
        slWy = np.vstack((yt[:,0],yt[:,1])).T
        
    else:
        Di = stationInfo['Dune Line Info']
        duneInt = np.asarray(Di['Dune Line Interpolation'])
        
        xi = duneInt[:,0]
        py = duneInt[:,1]
      
        exc = []
        
        #Index Transects that do not intercept the extracted shoreline
        for i in range(0, len(xt)):
            if np.min(yt[i,0]) < np.min(tranSL[:,1]):
                exc.append(i)
        
        exc.sort(reverse = True) 
        
        #Remove transects that do not intercept the extracted shoreline
        for i in range(len(exc)):
            xt = np.delete(xt, exc[i], 0)
            yt = np.delete(yt, exc[i], 0)
        
        idx = [0]*len(xt)
        for i in range(0, len(xt)):
            if yt[i,0] > np.nanmax(slC[:,1]):
                idx[i] = np.NaN
            else:
                xLoc = np.asarray(np.where(np.logical_and(yt[i,0]>= (slC[:,1]-1),
                                                          yt[i,0]<=(slC[:,1]+1))))
                if xLoc.size == 0:
                    j = i - 1
                    idx[i] = idx[j]
                else:
                    idx[i] = np.asarray(np.mean(xLoc))
                    
        idy = [0]*len(idx)
        for i in range(0, len(idx)):
            idy[i] = yt[i,0]
            
        slWx = np.vstack((idx,xt[:,0])).T 
        slWy = np.vstack((yt[:,0],yt[:,1])).T  
    
    dtInfo = stationInfo['Datetime Info']
    date = dtInfo['Date']
    dateStr = (date[5:7]+ '/' + date[8:10]+ '/' + date[0:4])
     
    time = dtInfo['Time_utc2']    
    
    # plt.ioff()          
    figBPW, ax = plt.subplots(1, 1)
    figBPW.canvas.set_window_title('Beach Pixel Width')   
    plt.imshow(photo, interpolation = 'nearest')
    plt.xlabel("Image Width (pixels)", fontsize = 10)
    plt.ylabel("Image Height (pixels)", fontsize = 10)
    plt.tick_params(axis = 'both', which = 'major', labelsize = 8)
    plt.tick_params(axis = 'both', which = 'minor', labelsize = 8)
    
    plt.plot(tranSL[:,0], tranSL[:,1], color = 'r', linewidth = 2, 
             label = 'Detected Shoreline', zorder = 6)
    plt.plot(xi, py, color = 'b', linewidth = 2, label = 'Dune Line', 
             zorder = 8)
    
    if orn == 0:
        t1 = 0
        for i in range(0,len(xt)):
            checkX = slWx[i, 0]*slWx[i, 1]
            checkY = slWy[i, 0]*slWy[i, 1]
            if math.isnan(checkX) or math.isnan(checkY):
                pass
            elif i == t1:
                ax.plot(slWx[i,:], slWy[i,:], color = 'k', linewidth = 1, 
                        label = 'Beach Transects', zorder = 4)
                for j in range(0,len(ax.get_lines())):
                    ln = ax.get_lines()
                    a = np.asarray(ln[j].get_ydata())
                    p1 = min(a)
                    p2 = max(a)
                    # midpt = (p1+p2)/2
                    beachwidths[i] = p2-p1
                    
                # text = plt.text(midpt, slWy[i,0], s = str(i), ha='center',
                #                 va='center', color="w", size = 5, zorder = 8)
                # text.set_path_effects([pe.Stroke(linewidth = 1,
                #                                   foreground='black'),pe.Normal()])
            else:
                ax.plot(slWx[i,:], slWy[i,:], color = 'k', linewidth = 1, 
                        label = '_nolegend_', zorder = 4)
                
                for j in range(0,len(ax.get_lines())):
                    ln = ax.get_lines()
                    a = np.asarray(ln[j].get_ydata())
                    p1 = min(a)
                    p2 = max(a)
                    # midpt = (p1+p2)/2
                    beachwidths[i] = p2-p1
                
            # text = plt.text(midpt, slWy[i,0], s = str(i), ha='center',
            #                 va='center', color="w", size = 5, zorder = 8)
            # text.set_path_effects([pe.Stroke(linewidth = 1,
            #                                   foreground='black'),pe.Normal()])
    else:
        t1 = np.where(np.isnan(slWx[:,0]))[0][-1] + 1
    
        for i in range(0,len(xt)):
            checkLR = slWx[i, 0]*slWx[i, 1]
            checkF = slWy[i, 0]*slWy[i, 1]
            if math.isnan(checkLR) or math.isnan(checkF):
                pass
            elif i == t1:
                ax.plot(slWx[i,:], slWy[i,:], color = 'k', linewidth = 1, 
                        label = 'Beach Transects', zorder = 4)
                for j in range(0,len(ax.get_lines())):
                    ln = ax.get_lines()
                    a = np.asarray(ln[j].get_xdata())
                    p1 = min(a)
                    p2 = max(a)
                    # midpt = (p1+p2)/2
                    beachwidths[i] = p2-p1
                    
                # text = plt.text(midpt, slWy[i,0], s = str(i), ha='center',
                #                 va='center', color="w", size = 5, zorder = 8)
                # text.set_path_effects([pe.Stroke(linewidth = 1,
                #                                   foreground='black'),pe.Normal()])
            else:
                ax.plot(slWx[i,:], slWy[i,:], color = 'k', linewidth = 1, 
                        label = '_nolegend_', zorder = 4)
                
                for j in range(0,len(ax.get_lines())):
                    ln = ax.get_lines()
                    a = np.asarray(ln[j].get_xdata())
                    p1 = min(a)
                    p2 = max(a)
                    # midpt = (p1+p2)/2
                    beachwidths[i] = p2-p1
                
            # text = plt.text(midpt, slWy[i,0], s = str(i), ha='center',
            #                 va='center', color="w", size = 5, zorder = 8)
            # text.set_path_effects([pe.Stroke(linewidth = 1,
            #                                   foreground='black'),pe.Normal()])
    
    if imgType == 'avg':
        source = 'Time Averaged'
    if imgType == 'brt': 
        source = 'Brightest Pixel'
    if imgType == 'snap':
        source = 'Snapshot'
        
    plt.title(('Beach Pixel-Width Transects (' + source + ')\n' + snameStr +
              ' - ' + dateStr + ' at ' + time[:2] + ':' + time[2:] + ' UTC'),
              fontsize = 12, ha = 'center')
    plt.legend(prop={'size': 9})
    
    cwd = os.getcwd()
    savePath = os.path.join(cwd, 'Outputs', stationname, date, time, imgType)
    saveName = (stationname + '.' + date + '_' + time + '.' + 'PixWidth.' +
                imgType + '.png')
    plt.savefig(os.path.join(savePath, saveName), bbox_inches = 'tight', dpi=1200)
    
    plt.close()
    
    for i in range(0,len(stationInfo['Shoreline Transects']['x'])):
        try:
            if beachwidths[i] == 0:
                beachwidths[i] = np.nan
        except:
            pass

    dtStr = dtInfo['Date Time (utc) String 1']
    
    bpwPath = os.path.join(cwd, 'Outputs', stationname, '.pixWidth', imgType)  
    
    if not os.path.exists(bpwPath):
        os.makedirs(bpwPath)
        
    fname = (stationname + '.' + imgType +'PixWidth.'+ dtStr + '.csv')
    csvPath = os.path.join(bpwPath, fname)
    
    if os.path.exists(csvPath):
        os.remove(csvPath)
    
    header_added = False
    for i in range(0, len(beachwidths)):
        with open(csvPath, 'a', newline = '') as f:
            writer = csv.writer(f)
            if not header_added:
                writer.writerow(['Station', stationname])
                writer.writerow(['DateTime', dtInfo['Date Time (utc) String 3']])
                try:
                    writer.writerow(['TideLvl (m)', stationInfo['Tide Level (m)']])
                except:
                    pass
                writer.writerow(['Transects', int(len(xt))])
                writer.writerow([''])
                writer.writerow(['Transect #', 'Width (pixels)'])
                header_added = True
            else:
                pass
            writer.writerow([i, beachwidths[i]])        
    
    # Update list of used modules
    mod = ['os' , 'csv', 'math', 'numpy', 'matplotlib','win32api', 'scipy', 'mpl_toolkits']
    mods = stationInfo['Modules Used']
    for n in range(len(mod)):
        if mod[n] not in mods:
            mods.append(mod[n])
    stationInfo['Modules Used'] = mods
    
    return(stationInfo, figBPW, beachwidths)

#######################################

def figRecSl(stationInfo, slVars, img, imgType, wtLvl):
    
    cwd = os.getcwd()
    stationname = stationInfo['Station Name']
    
    h = stationInfo['RecImg Dimensions']['h'] - 1
    w = stationInfo['RecImg Dimensions']['w'] - 1
    
    dispW = GetSystemMetrics(0)/100
    dispH = GetSystemMetrics(1)/100
    
    xPts = stationInfo['Shoreline'][:,0]
    yPts = stationInfo['Shoreline'][:,1]
    
    dtInfo = stationInfo['Datetime Info']
    date = dtInfo['Date']
    time = dtInfo['Time_utc2']
    time2 = dtInfo['Time_utc']
    mm = dtInfo['Month']
    dd = dtInfo['Day']
    yyyy = dtInfo['Year']
    
    tideLvl = slVars['Tide Level']
    txt = "Water Level = {}m".format(tideLvl)
    
    xVal = stationInfo['Axis Information']['X-axis']['Values'] 
    yVal = stationInfo['Axis Information']['Y-axis']['Values'] 
    xTic = stationInfo['Axis Information']['X-axis']['Tics'] 
    yTic = stationInfo['Axis Information']['Y-axis']['Tics'] 

    saveDir = os.path.join(cwd, 'Outputs', stationname, date, time, 'rec')
    
    if not os.path.exists(saveDir):
        os.makedirs(saveDir)

    figRecSl,ax = plt.subplots(figsize=(dispW, dispH))
    ax.imshow(np.flipud(img),origin='lower', zorder = 0)
    # plt.text(w - 10 , 10, txt, size = 8 , va = 'bottom', ha = 'right', backgroundcolor = 'w')
    ax.text(w - 3 , 3, txt, va = 'bottom', ha = 'right', c = 'k', bbox=dict(facecolor='w', edgecolor='none', boxstyle='round'))
    plt.title('Local Grid Geo-Rectification\n' + mm + '/'+ dd + '/' + yyyy + ' at ' + time2 + ' UTC', fontsize = 24)
    plt.xticks(xVal,xTic);
    plt.yticks(yVal,yTic);
    plt.xlabel("X Distance from Camera (m)", fontsize = 22)
    plt.ylabel("Y Distance from Camera (m)", fontsize = 22)
    plt.tick_params(axis = 'both', which = 'major', labelsize = 20)
    plt.tick_params(axis = 'both', which = 'minor', labelsize = 20)
    # for i in range(0,len(xt)):
        # plt.plot(xt[i,:], yt[i,:], color = 'blue', linewidth = 0.5, label = '_nolegend_', zorder = 2)
    plt.plot(xPts[:], h - yPts[:], color = 'r', linewidth = 2, label = 'Detected Shoreline', zorder = 5)
    # plt.scatter(xPts[:], h - yPts[:], c ='r', linewidth = 1, edgecolor= 'k', label = 'Detected Shoreline', zorder = 8)
    plt.legend(prop={'size': 12})
    
    
    saveName = (stationname.lower() + '.' + dtInfo['Date Time (utc) String 2'] + '.recSL.jpg')
    plt.savefig(os.path.join(saveDir, saveName), bbox_inches = 'tight', dpi=400)
    plt.close('all')
    # plt.plot(xPts, yPts, 'or', lw = 2, mec = 'k')
    
    # Update list of used modules
    mod = ['os' , 'csv', 'math', 'numpy', 'matplotlib','win32api', 'scipy', 'mpl_toolkits']
    mods = stationInfo['Modules Used']
    for n in range(len(mod)):
        if mod[n] not in mods:
            mods.append(mod[n])
    stationInfo['Modules Used'] = mods
    
    return(stationInfo)
    



    