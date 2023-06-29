# WebSPAT
Webcams for Shoreline Position Analysis Toolkit

The code in this repository is designed to process coastal webcam imagery and subsequently detect shoreline position from time-averaged and brightest-pixel image products.

Each camera requires a one-time station setup to be performed to establish a camera-specific config file that is used for all subsequent processing. 
  This can be done within the "Individual" directory by running runWebSPAT.py and selecting "Setup New Station."
    
When setting up a new station, you will be asked to define multiple variabels.
  The station name, it is essential that the station name matches WebCOOS.org's camera-specific data access slug.
    
  The camera's base RTSP archive URL (ex. https://stage-ams.srv.axds.co/archive/mp4/uncw/oakisland_west/)
    
  The station ID of the NOAA Water Level Observation Station closest to the camera (https://tidesandcurrents.noaa.gov/stations.html?type=Water+Levels)
    
The indivdual script is equiped with a Guided-User-Interface to aid in overall user friendliness.


The batch processing script (batchWebSPAT.py) is designed querythe WebCOOS video archives and process a list of targeted videos that meet user specified parameters.

