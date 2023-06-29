# -*- coding: utf-8 -*-
"""
Created on Thu Jul 29 10:31:32 2021

@author: braunj
"""

import os
import cv2
import sys
import wget
import math
import shutil
import ctypes
import requests
import termcolor
import webbrowser
import numpy as np
import tkinter as tk
from PIL import Image
from tqdm import tqdm
from ftplib import FTP
import tkcalendar as tkc
from termcolor import cprint
from functools import partial
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
from datetime import date, datetime
from tkinter import filedialog as fd
from scipy.interpolate import interp1d
from tkinter import simpledialog as sd

#######################################
#       STATION_SETUP FUNCTIONS       #
#######################################

#%%

def setup_msg():
    title = 'Station Setup Instrutions'
        
    line1 = 'This script will allow you to set up a station for shoreline position analysis.'
    line2 = 'This only needs to be done once unless the position of the dune line or camera view changes.'
    step1 = 'Step 1: Enter the station name, a webCOOS archive link, and select the desired setup video. '
    step2 = 'Step 2: Link camera specific calibration variable file (if applicable).'
    step3 = 'Step 3: Digitize a line along the dune base and define the horizon location within the image.'
    step4 = 'Step 4: Mark two reference shoreline endpoints to define a region of interest for shorline detection.'
   
    
    text = (line1 + "\n\n" + line2 + "\n\n" + step1 + "\n\n" + step2 
            + "\n\n" + step3 + "\n\n" + step4)
    
    MB_OK = 0x0
    ICON_INFO = 0x40
    WIN_TOP = 0x1000
    
    ctypes.windll.user32.MessageBoxW(0, text, title, MB_OK | ICON_INFO | WIN_TOP)

#%%

def define_station():
  
    root = tk.Tk()
    root.attributes("-topmost", True)
    root.eval('tk::PlaceWindow %s center' %root.winfo_toplevel())
    root.withdraw()
    
    # the input dialog
    stationname = sd.askstring(title="Station Name", 
               prompt= "        Define a Site Name (no spaces):         ",
               parent = root)
    root.destroy()
    
    cwd = os.getcwd()
    stationFod = os.path.join(cwd, 'Inputs', stationname)
    if not os.path.exists(stationFod):
        os.makedirs(stationFod)
    
    return(stationname, stationFod)

#%%

def getRTSP():
  
    root = tk.Tk()
    root.attributes("-topmost", True)
    root.eval('tk::PlaceWindow %s center' %root.winfo_toplevel())
    root.withdraw()
    
    # the input dialog
    rtspURL = sd.askstring(title="RTSP URL", 
               prompt="          Enter the Station's RTSP URL          ",
               parent = root)
    root.destroy()

    return(rtspURL)

#%%

def getStationType():
    
    def video():
        global stationType
        stationType = 'video'
        root.destroy()
        return(stationType)
    
    def stillshot():
        global stationType
        root.destroy()
        stationType = 'still'
        return(stationType)
    
    root = tk.Tk()
    root.title("Select Video File")
    root.eval('tk::PlaceWindow %s center' %root.winfo_toplevel())
    
    button1 = tk.Button(text = "Video", command = video, width = 15)
    button1.pack(side = "bottom", padx = 5, pady = 3, fill="none", expand=True)
    
    button2 = tk.Button(text = "Still Shot", command = stillshot, width = 15)
    button2.pack(side = "bottom",  padx = 5, pady = 3, fill="none", expand=True)
    
    label = tk.Label(root, text = 'Select Media Type', font='Helvetica 10 underline')
    label.pack(padx = 5, pady = 3)
    root.mainloop()
   
    return(stationType)


#%%

def selectVid(stationInfo):
     
    def localFile():
        global vid, source
        vid = fd.askopenfilename(title="Select video")
        root.destroy()
        source = 'local'
        return(vid, source)
        
    def ftpFile(stationInfo):
        global vid, source
        root.destroy()
        vid = ftpDownload(stationInfo)
        source = 'ftp'
        return(vid, source)
    
    def rtspFile(stationInfo):
        global vid, source
        root.destroy()
        vid = rtspDownload(stationInfo)
        source = 'rtsp'
        return(vid, source)
    
    root = tk.Tk()
    root.title("Video Source")
    root.eval('tk::PlaceWindow %s center' %root.winfo_toplevel())
    
    button1 = tk.Button(text = "Upload Local Video File", command = localFile, width = 25)
    button1.pack(side = "bottom", padx = 5, pady = 3, fill="none", expand=True)
    
    button2 = tk.Button(text = "Download from FTP Server", command = 
                        lambda info = stationInfo: ftpFile(info), width = 25)
    button2.pack(side = "bottom", padx = 5, pady = 3, fill="none", expand=True)
    
    button2 = tk.Button(text = "Download from RTSP Server", command = 
                        lambda info = stationInfo: rtspFile(info), width = 25)
    button2.pack(side = "bottom", padx = 5, pady = 3, fill="none", expand=True)
    
    label = tk.Label(root, text = 'Select Video Source', font = 'Helvetica 10 underline')
    label.pack()
    root.mainloop()
    
    # if source == 'rtsp' or source == 'ftp':
    #     return(vid, source)
    
    if source == 'local':
        
        line1 = 'Local uploads are assumed to be named using the following format:'
        line2 = 'stationname-yyyy-mm-dd_HHMMSSZ.mp4'
        line3 = '(Ex. ' + stationInfo['Station Name'] + '.2023-06-22_140600Z.mp4)'
        line4 = '\n\nThe filename of the video you have uploaded is:'
        line5 =  os.path.basename(vid)
        line6 = '\n\nIs this video named using UTC or LTZ times?'

        msg = ("\n" + line1 + "\n" + line2 + "\n" + line3 + "\n" + line4 +  '\n' + line5)

        def ftp():
            global source
            root.destroy()
            source = 'ftp'
            return(source)
        
        def rtsp():
            global source
            root.destroy()
            source = 'rtsp'
            return(source)
        
        def rename(button):
            global newVidName, vid
            newVidName = sd.askstring(title="Enter New Video Name", 
                       prompt= "  Enter New Video File Name (no spaces):   ",
                       parent = root)
            button3.grid_forget()
            label1.config(text = 'The video file name has been changed.')
            label2.config(text = '\nDoes the new file name use UTC or LTZ time?')
            os.rename(vid,os.path.join(os.path.dirname(vid), newVidName))
            vid = os.path.join(os.path.dirname(vid), newVidName).replace('\\','/')
        
        root = tk.Tk()
        root.title("Naming Format")
        root.eval('tk::PlaceWindow %s center' %root.winfo_toplevel())
        # root.geometry('500x250')
        
        button1 = tk.Button(text = "UTC (RTSP)", command = rtsp)
        button1.grid(column = 1, row = 2, sticky="ew", 
                                      pady=5, padx=5)
        
        button2 = tk.Button(text = "LTZ (FTP)", command = ftp)
        button2.grid(column = 2, row = 2, sticky="ew", 
                                      pady=5, padx=5)
        
        button3 = tk.Button(text = "Rename Video", command = lambda: rename(button3))
        button3.grid(column = 3, row = 2, sticky="ew", 
                                      pady=5, padx=5)
        
        label1 = tk.Label(root, text = msg)
        label1.grid(row = 0, column = 1, columnspan = 3)
        label2 = tk.Label(root, text = line6)
        label2.grid(row = 1, column = 1, columnspan = 3)
        root.mainloop()  
    else:
        pass
    
    # Update list of used modules
    mod = ['os' , 'opencv', 'sys', 'wget', 'math', 'shutil', 
           'ctypes', 'requests', 'webbrowser', 'numpy', 'tkinter', 
           'PIL', 'tqdm', 'ftplib', 'tlcalendar', 'functools',
           'beautifulsoup4', 'matplotlib', 'datetime', 'scipy', 
           'termcolor']

    mods = stationInfo['Modules Used']
    for n in range(len(mod)):
        if mod[n] not in mods:
            mods.append(mod[n])
    stationInfo['Modules Used'] = mods
    
    return(stationInfo, vid, source)

#%%

def rtspDownload(stationInfo):
    
    cprint(' Analyzing video archive please wait...', 'blue', attrs=['bold'])
    
    url = stationInfo['RTSP URL']
    subDirs = []
    page = requests.get(url).text
    soup = BeautifulSoup(page, 'html.parser')
    nodes = [node.get('href')[0:4] for node in soup.find_all('a')]
    for node in nodes:
        try:
            datetime.strptime(node, '%Y')
            subDirs.append(url + node + r'/')
        except ValueError:
            pass
    
    soup = []
    nodes = []
    moDirs = []   
    for i in range(len(subDirs)):
        url = subDirs[i]
        soup.append(BeautifulSoup(requests.get(subDirs[i]).text, 'html.parser'))
        nodes.append([node.get('href')[0:2] for node in soup[i].find_all('a')])

        for node in nodes[i]:
            try:
                datetime.strptime(node, '%m')
                moDirs.append(url + node + r'/')
            except ValueError:
                pass
    
    availableDateDirs = []
    for i in range(len(moDirs)):
        if i == len(moDirs)-1:
            if int(moDirs[i][-3:-1]) - int(moDirs[i-1][-3:-1]) == 1:
                availableDateDirs.append(moDirs[i])
            else:
                pass
            
        elif int(moDirs[i][-3:-1]) == 12:
            if int(moDirs[i+1][-3:-1]) == 1:
                availableDateDirs.append(moDirs[i])
            else:
                pass
    
        elif int(moDirs[i+1][-3:-1]) - int(moDirs[i][-3:-1]) == 1:
                availableDateDirs.append(moDirs[i])
        else:
            pass
        
    startPage = requests.get(availableDateDirs[0]).text
    soupStart = BeautifulSoup(startPage, 'html.parser')
    startNodes = [node.get('href')[0:2] for node in soupStart.find_all('a')]
    found = False
    for node in startNodes:
        if found == True:
            pass
        else:
            try:
                datetime.strptime(node, '%d')
                startURL = availableDateDirs[0] + node + r'/'
                found = True
            except ValueError:
                pass
    
    endPage = requests.get(availableDateDirs[-1]).text
    soupEnd = BeautifulSoup(endPage, 'html.parser')
    endNodes = [node.get('href')[0:2] for node in soupEnd.find_all('a')]
    for node in endNodes:
        try:
            datetime.strptime(node, '%d')
            endURL = availableDateDirs[-1] + node + r'/'
        except ValueError:
            pass
  
    startDate = date(int(startURL[-11:-7]), int(startURL[-6:-4]), int(startURL[-3:-1]))
    endDate = date(int(endURL[-11:-7]), int(endURL[-6:-4]), int(endURL[-3:-1]))
   
    
    msg1 = "   Archived videos availabe between % and $."    
    msg1 = msg1.replace('%', termcolor.colored(startDate.strftime('%B %d, %Y'),
                       'green', attrs = ['bold', 'underline']))
    msg1 = msg1.replace('$', termcolor.colored(endDate.strftime('%B %d, %Y'), 
                       'green', attrs = ['bold', 'underline']))
    cprint(msg1, 'white', attrs=['bold'])
    
    rtspURL = stationInfo['RTSP URL'] 
   
    root = tk.Tk()
    root.title("")
    root.eval('tk::PlaceWindow %s center' %root.winfo_toplevel())
    
    # title = tk.Label(root, text="Are you using an existing station \n or would you like to set up a new one?")
    # title.grid(root, columnspan = 2, row = 1)
    label = tk.Label(root, text = 'Choose the desired date:')
    label.grid(row = 0, column = 0, columnspan = 4, pady = 10)
    
    today = date.today()
    
    cal = tkc.Calendar(root, selectmode = 'day', year = today.year, 
                   month = today.month, day = today.day, 
                   date_pattern = 'y-mm-dd', mindate = startDate,
                   maxdate = endDate, firstweekday = 'sunday',
                   weekendbackground = 'gray90', weekendforeground = 'black',
                   othermonthbackground = 'darkgray', 
                   othermonthwebackground = 'darkgray', 
                   othermonthforeground = 'darkgray',
                   othermonthweforeground = 'darkgray',
                   disableddaybackground = 'darkgray', 
                   disableddayforeground = 'gray', )
    cal.grid(row = 3, rowspan = 4, column = 1, columnspan = 2)
    
    def selectDT(link):
        global dateChoice
        dateChoice = cal.get_date()
        # root.destroy()
        
        def chooseVid(times):
            global vidChoice
            vidChoice = times
            vidWin.destroy()
            root.destroy()
        
        vidWin = tk.Toplevel(root)
        sX = root.winfo_x()
        sY = root.winfo_y()
        
        vidWin.geometry("+%d+%d" % (sX-200, sY-200))
        
        vidWin.title('Select Interval')
        timeWin_label = tk.Label(vidWin,
          text ='Select video start time:')
        nCol = 5
        timeWin_label.grid(row = 0, column = 0, columnspan = nCol)
        
        timeDirs = []
        dtObj = datetime.strptime(dateChoice, '%Y-%m-%d')
        dateURL = link + datetime.strftime(dtObj, '%Y/%m/%d/')
        timePage = requests.get(dateURL).text
        soupTime = BeautifulSoup(timePage, 'html.parser')
        timeNodes = [node.get('href')[-22:-4] for node in soupTime.find_all('a')]
        for node in timeNodes:
            try:
                dt = datetime.strptime(node, '%Y-%m-%d-%H%M%SZ')
                timeDirs.append(datetime.strftime(dt, '%H:%M:%S UTC'))
            except ValueError:
                pass
        
        x = [0]*len(timeDirs)
        y = [0]*len(timeDirs)
         
        seq = [n for n in range(0,nCol)]*int(
            (((round(len(timeDirs)/nCol)*nCol)+nCol)/nCol))
        
        for i in range(0,len(timeDirs)):
            x[i] = seq[i]
            y[i] = 9 + math.floor(i/nCol) 
            
            tk.Button(vidWin, text = timeDirs[i], width=20, command = lambda 
                      times = timeDirs[i]: 
                  chooseVid(times)).grid(column = x[i], row = y[i],
                                        sticky="ew", pady=5, padx=5)
        
        
    tk.Button(root, text = 'Select Date', width=20, command = lambda link = rtspURL: 
              selectDT(link)).grid(column = 1, columnspan = 2, pady=20)     
    
    root.mainloop()
    
    dtChoice = datetime.strptime(dateChoice + ' ' + vidChoice, '%Y-%m-%d %H:%M:%S UTC')
    
    tgtURL = (rtspURL + datetime.strftime(dtChoice, '%Y/%m/%d/') + stationInfo['Station Name'] + 
              datetime.strftime(dtChoice, '-%Y-%m-%d-%H%M%SZ.mp4'))
    
    vidName = (stationInfo['Station Name'] + datetime.strftime(dtChoice, '-%Y-%m-%d-%H%M%SZ.mp4'))
    
    if stationInfo['Setup Video'] == False:
        outputDir = os.path.join(os.getcwd(), 'Inputs', stationInfo['Station Name'], '.Vids')
        if not os.path.exists(outputDir):
            os.makedirs(outputDir)
    elif stationInfo['Setup Video'] == True:
        outputDir = os.path.join(os.getcwd(), 'Inputs','.StationConfigs', '.setupVids', stationInfo['Station Name'])
        if os.path.exists(outputDir):
            shutil.rmtree(outputDir)
            os.makedirs(outputDir)
        elif not os.path.exists(outputDir):
            os.makedirs(outputDir)
      
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
          
    # Check if the latest build in the local path, if not download it.
    if os.path.isfile(os.path.join(outputDir, vidName)):
        vid = os.path.join(outputDir, vidName)
        cprint('   Selected file already exists, moving on...', 'white', attrs = ['bold'])
    else:   
        cprint('\n Downloading video...', 'blue', attrs=['bold'])
        vid = wget.download(tgtURL, out=outputDir, bar = pbar)
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
    return(vid)

#%%

def ftpDownload(stationInfo):
    
    def ftpLogin():
        
        def Login(username, password):
            username = username.get()
            password = password.get()
            root.destroy()

        root = tk.Tk()  
        root.eval('tk::PlaceWindow %s center' %root.winfo_toplevel()) 
        root.title('Server Login')
        
        titleLabel = tk.Label(root,text="FTP Server Login\n (ftp.axds.co)")
        titleLabel.grid(row=0, columnspan = 2, padx = 10, pady = 5)  
       
        #username label and text entry box
        usernameLabel = tk.Label(root, text="User Name:")
        usernameLabel.grid(row=1, column=0, padx = 10, pady = 5)
        username = tk.StringVar()
        usernameEntry = tk.Entry(root, textvariable=username) 
        usernameEntry.insert(0, 'webcoos_joe')
        usernameEntry.grid(row=1, column=1, padx = 10, pady = 5) 
        
        #password label and password entry box
        passwordLabel = tk.Label(root,text="Password:")
        passwordLabel.grid(row=2, column=0, padx = 10, pady = 5)
        password = tk.StringVar()
        passwordEntry = tk.Entry(root, textvariable=password, show='*')  
        passwordEntry.insert(0, 'uncwjoe2')
        passwordEntry.grid(row=2, column=1, padx = 10, pady = 5)
        Login = partial(Login, username, password)
        
        #login button
        loginButton = tk.Button(root, text="Login", command=Login) 
        loginButton.grid(row=4, columnspan = 2, padx = 10, pady = 5) 
        
        username = username.get()
        password = password.get()
        
        root.mainloop()
        
        return(username, password)
    
    username, password = ftpLogin()
    
    ftp = FTP('ftp.axds.co')
    ret = ftp.login(user=username, passwd=password)
    
    if ret == '230 Login successful.':
        cprint('\nLogin successful!', 'green', attrs=['bold'])
    else:
        cprint('Login unsuccessful, please try again.', 'red', attrs=['bold'])
    
    dir_list = []
    ftp.dir(dir_list.append)
    
    cameras = [0]*len(dir_list)
    for i in range(len(dir_list)):
            cameras[i] = max(dir_list[i].split(), key=len)
    
    root = tk.Tk()
    root.title("Camera Selection")
    root.eval('tk::PlaceWindow %s center' %root.winfo_toplevel())
    
    # title = tk.Label(root, text="Are you using an existing station \n or would you like to set up a new one?")
    # title.grid(root, columnspan = 2, row = 1)
    tk.Label(root, text = 'SELECT A CAMERA:').grid(row = 0, column = 1, 
                                                    columnspan = 2)
    
    for i in range(0,len(cameras)):
        
        def button(c):
            global camera
            camera = c
            root.destroy()
        
        if i % 2 == 0:
            x = 1
            y = i + 1
        else: 
            x = 2
            y = i
         
        tk.Button(root, text = cameras[i], command = lambda c = cameras[i]: 
                  button(c)).grid(column = x, row = y, sticky="ew", 
                                  pady=5, padx=5)
            
    root.mainloop()
    
    cprint('\nAnalyzing video archive please wait...', 'yellow', attrs=['bold'])
    
    ftp.cwd('/'+ camera)
    subdir_list = []
    ftp.dir(subdir_list.append)
    subdir = max(subdir_list[0].split(), key=len)
    
    fod_list = []
    ftp.cwd('/'+ camera + '/' + subdir)
    ftp.dir(fod_list.append)
    availableDates = []
    for item in fod_list[:len(fod_list)-1]:
        availableDates.append(datetime.strptime(item[-10:],'%Y-%m-%d'))
    
    def ftpSearchParams(availableDates):
        def time_interval(hour, minute, interval):
            return [
                f"{str(i).zfill(2)}:{str(j).zfill(2)}" 
                for i in range(6,22) #cameras start at 6 am and stop at 9 pm 
                for j in range(minute)
                if j % interval == 0
                ]

        times = time_interval(16, 60, 60)
        x = [0]*16
        y = [0]*16
        
        startDate = date(availableDates[0].year, availableDates[-1].month, availableDates[-1].day)
        endDate = date(availableDates[-1].year, availableDates[-1].month, availableDates[-1].day)
        
        msg1 = "\nArchived videos availabe between % and $."    
        msg1 = msg1.replace('%', termcolor.colored(startDate.strftime('%B %d %Y'),
                           'green', attrs = ['bold', 'underline']))
        msg1 = msg1.replace('$', termcolor.colored(endDate.strftime('%B %d %Y'), 
                           'green', attrs = ['bold', 'underline']))
        cprint(msg1, 'white', attrs=['bold'])
        
        root = tk.Tk()
        root.title("")
        root.eval('tk::PlaceWindow %s center' %root.winfo_toplevel())
        
        # title = tk.Label(root, text="Are you using an existing station \n or would you like to set up a new one?")
        # title.grid(root, columnspan = 2, row = 1)
        label = tk.Label(root, text = 'Choose the desired date and time(hour):')
        label.grid(row = 0, column = 0, columnspan = 4, pady = 10)
        
        today = date.today()

        cal = tkc.Calendar(root, selectmode = 'day', year = today.year, 
                       month = today.month, day = today.day, 
                       date_pattern = 'y-mm-dd', mindate = startDate,
                       maxdate = endDate, firstweekday = 'sunday',
                       weekendbackground = 'gray90', weekendforeground = 'black',
                       othermonthbackground = 'darkgray', 
                       othermonthwebackground = 'darkgray', 
                       othermonthforeground = 'darkgray',
                       othermonthweforeground = 'darkgray',
                       disableddaybackground = 'darkgray', 
                       disableddayforeground = 'gray', )
        cal.grid(row = 3, rowspan = 4, column = 1, columnspan = 2)

        def selectDT(t):
            global time, dateChoice
            time = t
            dateChoice = cal.get_date()
            
            def grabTimeInt(vt):
                global timeChoice
                timeChoice = vt
                timeWin.destroy()
                root.destroy()
                    
            timeWin = tk.Toplevel(root)
            timeWin.title('Select Interval')
            root.eval(f'tk::PlaceWindow {str(timeWin)} center')
            timeWin_label = tk.Label(timeWin,
              text ='Select a time (videos are produced in 10 minute increments)')
            timeWin_label.grid(row = 0, column = 0, columnspan = 3)
            
            hour = time[:2]
            minInt = [str(00), str(10), str(20), str(30), str(40), str(50)]
            minInt[0] = minInt[0].zfill(2)
            
            vidTimes = [0]*len(minInt)
            for i in range(len(minInt)):
                vidTimes[i] = (hour+':'+minInt[i])
                
                col = [0]*len(minInt)
                row = [0]*len(minInt)
                
            for i in range(len(minInt)):
                if i < 3:
                    row[i] = 1
                    col[i] = i
                else:
                    row[i] = 2
                    col[i] = i - 3
                
                tk.Button(timeWin, text = vidTimes[i], width=20, command = lambda 
                          vt = vidTimes[i]: 
                      grabTimeInt(vt)).grid(column = col[i], row = row[i],
                                            sticky="ew", pady=5, padx=5)
        
        for i in range(0,len(times)):
           
            if i >= 0 and i <= 3:
                y[i] = 9
                x[i] = i
                 
            elif i >= 4 and i <=7: 
                y[i] = 10
                for j in range(0,3):
                    x[i] = x[i-4]
                    
            elif i >= 8 and i <= 11:
                y[i] = 11
                for j in range(0,3):
                    x[i] = x[i-4]
                    
            elif i >= 12 and i <= 15:
                y[i] = 12
                for j in range(0,3):
                    x[i] = x[i-4]
                 
            tk.Button(root, text = times[i], width=20, command = lambda t = times[i]: 
                      selectDT(t)).grid(column = x[i], row = y[i], 
                                          sticky="ew", pady=5, padx=5)               
        root.mainloop()
        return(dateChoice, timeChoice)
    
    dateChoice, timeChoice = ftpSearchParams(availableDates)
    
    hour = timeChoice[:2]
    time = (timeChoice[:2] + '.' + timeChoice[3:5])
    timeStr =  (timeChoice[:2] + timeChoice[3:5])

    ftp.cwd('/'+ camera + '/' + subdir + '/' + dateChoice + '/001/dav/' + hour)

    file_list = []
    ftp.dir(file_list.append)
    
    class InvalidDateTime(Exception):
        'Raised when no FTP video exists for selected date and time.'
        pass
  
    for i in range(len(file_list)):
        if time in file_list[i]:
            if '.mp4' in file_list[i]:
                videoInfo = (file_list[i][29:].strip().split(' '))
                remotePath = videoInfo[5]
                break
        else:
            raise InvalidDateTime('No FTP video exists for this date and time.')

    localPath = (camera + '-' + dateChoice + '_' + timeStr + '00Z.mp4')
    
    if stationInfo['Setup Video'] == False:
        folder = os.path.join(os.getcwd(), 'Inputs', stationInfo['Station Name'], '.Vids')
        if not os.path.exists(folder):
            os.makedirs(folder)
    elif stationInfo['Setup Video'] == True:
        folder = os.path.join(os.getcwd(), 'Inputs','.StationConfigs', '.setupVids', stationInfo['Station Name'])
        if os.path.exists(folder):
            shutil.rmtree(folder)
            os.makedirs(folder)
        elif not os.path.exists(folder):
            os.makedirs(folder)
   
    cwd = os.getcwd()
    path = os.path.join(cwd, folder, localPath)
    
    # Check if the latest build in the local path, if not download it.
    if os.path.isfile(path):
        vid = str(path)
        cprint('\nSelected file already exists, moving on...', 'green', attrs = ['bold'])
        cprint(vid, 'grey', attrs=['bold'])
        
    else:
        bufsize = 1024
        f = open(folder + '\\' + localPath,'wb')
        size = ftp.size(remotePath)
        pbar = tqdm(total = size, unit = 'B', unit_scale = True, 
                    unit_divisor = 1024, file=sys.stdout)
        def bar(data):
            f.write(data)
            pbar.update(len(data))
        ftp.retrbinary('RETR '+remotePath,bar,bufsize)
        pbar.close()
        f.close()
        cprint('\nDownload Completed...', 'green', attrs=['bold'])
        vid = str(path)
        cprint(vid, 'grey', attrs=['bold'])
    return(vid)

#%%

def getVidSnap(vid):
        vidObj = cv2.VideoCapture(vid)
        vidObj.set(cv2.CAP_PROP_POS_MSEC, 5000)
        success, snapBGR = vidObj.read()
        vidObj.release()
        snap = cv2.cvtColor(snapBGR, cv2.COLOR_BGR2RGB)
        return(snap)

#%%

def getSnapshot():
    
    def getSnapPath():
        global snapPath
        snapPath = fd.askopenfilename(title="Select Camera Still")
        root.destroy()
        return(snapPath)
    
    root = tk.Tk()
    root.title("Select Image File")
    root.eval('tk::PlaceWindow %s center' %root.winfo_toplevel())
    
    button1 = tk.Button(text = "Choose Image", command = getSnapPath)
    button1.pack(side = "bottom", pady = 6, fill="none", expand=True)
    
    label = tk.Label(root, text = 'Select Still Shot Iamge File')
    label.pack()
    root.mainloop()
    
    snap = cv2.cvtColor(cv2.imread(snapPath), cv2.COLOR_BGR2RGB)
    
    return (snap)

#%%

def setOrientation():
    
    line1 = 'What is the orientation of the image?'
  
    def oceanForward():
        global orn
        orn = 0
        root.destroy()
        return(orn)
    
    def oceanRight():
        global orn
        orn = 1
        root.destroy()
        return(orn)
    
    def oceanLeft():
        global orn
        orn = 2
        root.destroy()
        return(orn)
    
    root = tk.Tk()
    root.title("Select Ocean Orientation")
    root.eval('tk::PlaceWindow %s center' %root.winfo_toplevel())
    
    tk.Label(root, text = line1, font='Helvetica 10 underline').grid(row = 0, column = 0, sticky = "ew", padx= 3, pady= 3, columnspan=2)
    
    button1 = tk.Button(text = "Ocean Right", command = oceanRight, width = 15)
    button1.grid(row=1,column=0, padx= 3, pady= 3)
    tk.Label(root, text = ' = ocean is to the right of the dunes.  ').grid(row = 1, column = 1, sticky = "w")
    
    button2 = tk.Button(text = "Ocean Left", command = oceanLeft, width = 15)
    button2.grid(row=2,column=0, padx= 3, pady= 3)
    tk.Label(root, text = ' = ocean is to the left of the dunes.  ').grid(row = 2, column = 1, sticky = "w")
    
    button3 = tk.Button(text = "Ocean Forward", command = oceanForward, width = 15)
    button3.grid(row=3,column=0, padx= 3, pady= 3)
    tk.Label(root, text = ' = ocean is in front of the dunes.  ').grid(row = 3, column = 1, sticky = "w")

    root.mainloop()
    
    return(orn)

#%%

def getCamCalabration():    
    line1 = 'Has a MATLAB camera calibration file been generated for this station?'
    line2 = '(This will extract and apply the camera parameters to undistort the image)'

    msg = ("\n" + line1 + "\n" + line2)

    
    def camCal_yes():
        global camCal_opt
        camCal_opt = True
        root.destroy()
        return(camCal_opt)
    
    def camCal_no():
        global camCal_opt
        camCal_opt = False
        root.destroy()
        return(camCal_opt)
    
    root = tk.Tk()
    root.title("Camera Calibration?")
    root.eval('tk::PlaceWindow %s center' %root.winfo_toplevel())
    
    button1 = tk.Button(text = "Yes", command = camCal_yes)
    button1.grid(column = 1, row = 2, sticky="ew", 
                                  pady=5, padx=5)
    
    button2 = tk.Button(text = "No", command = camCal_no)
    button2.grid(column = 2, row = 2, sticky="ew", 
                                  pady=5, padx=5)
    
    label = tk.Label(root, text = msg)
    label.grid(row = 0, column = 1, columnspan = 2)
    root.mainloop()
    
    return(camCal_opt)

#%%

def getDuneLine(stationInfo, snap):
        
    title = 'Digitize Dune Line'
            
    line1 = 'Click to create points along the dune line.'
    line2 = 'Left Click: Creates a new point.'
    line3 = 'Middle Click: Removes the most recently created point.'
    line4 = 'Right Click: Used to end input (click when finished).'   
        
    text = (line1 + "\n\n" + line2 + "\n\n" + line3 + "\n\n" + line4 + "\n\n")
        
    MB_OK = 0x0
    ICON_INFO = 0x40
    WIN_TOP = 0x1000
        
    ctypes.windll.user32.MessageBoxW(0, text, title, MB_OK | ICON_INFO | WIN_TOP)
    
    plt.imshow(snap, interpolation='nearest')
         
    plt.title('Click to Digitize Dune Line \n (right click to finish)', fontweight ="bold")
       
    D = plt.ginput(n = 100, show_clicks = True, mouse_add = 1, mouse_pop = 2, mouse_stop = 3)

    plt.close('all')
    
    dlX, dlY = zip(*D)
    
    dlX = np.asarray(dlX)
    dlX = np.asarray(dlX)
    
    w = len(snap[1])

    if stationInfo['Orientation'] == 0:
        dlIntF = interp1d(dlX, dlY, bounds_error = False)
        x = np.arange(0, w , 1)
        y = dlIntF(x)
        ornInfo = 'Ocean Forward'
    elif stationInfo['Orientation'] == 1 or stationInfo['Orientation'] == 2:
        dlIntLR = interp1d(dlY, dlX, bounds_error = False)
        y = np.arange(0, w , 1)
        x = dlIntLR(y)
        if stationInfo['Orientation'] == 1:
            ornInfo = 'Ocean Right'
        elif stationInfo['Orientation'] == 2:
            ornInfo = 'Ocean Left'
    Dl = np.vstack((x,y)).T
    
    xPts = []
    yPts = []
    for i in range(0,len(Dl)):
        if np.isnan(Dl[i,0]):
            pass
        elif np.isnan(Dl[i,1]):
            pass
        else:
            xPts.append(Dl[i,0])
            yPts.append(Dl[i,1])
            
    dunePts = np.vstack((xPts,yPts)).T
    
    Di = {'Duneline Orientation':ornInfo, 'Dune Line Interpolation':Dl, 'Dune Line Points':dunePts}
    return(Di)


#%%

def getNOAAstationID(stationInfo):
  
    root = tk.Tk()
    root.attributes("-topmost", True)
    root.eval('tk::PlaceWindow %s center' %root.winfo_toplevel())
    root.geometry("300x150")
    
    def enterStationID():
       global stationID
       stationID = int(entry.get())
       root.destroy()
       root.quit()
    
    def hyperlink(url):
       webbrowser.open_new_tab(url)
       
    label1=tk.Label(root, text="Enter the Nearest NOAA Water Level Station ID #:")
    label1.pack()
    
    entry= tk.Entry(root, width = 20)
    entry.focus_set()
    entry.pack(pady = 5)
    
    label2=tk.Label(root, text="Station information can be found here: ")
    label2.pack()
    
    link = tk.Label(root, text=" NOAA Water Level Stations ", fg="blue", cursor="hand2", font= ('TkDefaultFont 10 underline'))
    link.pack()
    link.bind("<Button-1>", lambda e: 
          hyperlink("https://tidesandcurrents.noaa.gov/stations.html?type=Water+Levels"))
    
    tk.Button(root, text= "Enter", width= 20, command = enterStationID).pack(pady = 10)
        
    root.mainloop()
    
    # Update list of used modules
    mod = ['os' , 'opencv', 'sys', 'wget', 'math', 'shutil', 
           'ctypes', 'requests', 'webbrowser', 'numpy', 'tkinter', 
           'PIL', 'tqdm', 'ftplib', 'tlcalendar', 'functools',
           'beautifulsoup4', 'matplotlib', 'datetime', 'scipy', 
           'termcolor']

    mods = stationInfo['Modules Used']
    for n in range(len(mod)):
        if mod[n] not in mods:
            mods.append(mod[n])
    stationInfo['Modules Used'] = mods
    
    return(stationInfo, stationID)

#%%

def showSetupImg(stationInfo):
    stationname = stationInfo['Station Name']
    cwd = os.getcwd()
    fname = os.path.join(cwd, 'Inputs', '.StationConfigs', '.setupImgs', stationname + '.setup.png')
    image = Image.open(fname)
    image.show()
    
    # Update list of used modules
    mod = ['os' , 'opencv', 'sys', 'wget', 'math', 'shutil', 
           'ctypes', 'requests', 'webbrowser', 'numpy', 'tkinter', 
           'PIL', 'tqdm', 'ftplib', 'tlcalendar', 'functools',
           'beautifulsoup4', 'matplotlib', 'datetime', 'scipy', 
           'termcolor']

    mods = stationInfo['Modules Used']
    for n in range(len(mod)):
        if mod[n] not in mods:
            mods.append(mod[n])
    stationInfo['Modules Used'] = mods
    
    return(stationInfo)
    
#%%