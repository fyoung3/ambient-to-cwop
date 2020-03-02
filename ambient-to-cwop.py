import os
from socket import *
from datetime import datetime, time
import math
#import cPickle as pickle

############ API INFO ################
os.environ["AMBIENT_ENDPOINT"] = 'https://api.ambientweather.net/v1'
os.environ["AMBIENT_API_KEY"] = 'ENTER KEY HERE' #Enter your Ambient API Key
os.environ["AMBIENT_APPLICATION_KEY"] = 'ENTER APP KEY HERE' #Enter your Ambient App Keu
#####################################

from ambient_api.ambientapi import AmbientAPI

########### SITE INFO ###############
callsign = 'CWOP CALLSIGN' #Enter your CWOP Callsign
latitude = '3221.10N' #Enter Latitude - Lat must be listed in DECIMAL DEGREES (DD.DDDD). Number of digits doesn't really matter. Use positive values for N/E, negative for S/W. The program then converts to degrees decimal minutes (DD MM.MMMM), which is the format APRS requires.
longitude = '08615.06W' #Enter Longitude - Long must be listed in DECIMAL DEGREES (DD.DDDD). Number of digits doesn't really matter. Use positive values for N/E, negative for S/W. The program then converts to degrees decimal minutes (DD MM.MMMM), which is the format APRS requires.
devicename = 'WS2902A' #This identifies your equipment/software. You can put anything you want. Example: 'WS2902A'.
#####################################

api = AmbientAPI()

devices = api.get_devices()
home = devices[0] #this assumes you have only one station. Increase number accordingly if you want to get data from others
weather= home.last_data

#convert coordinates to degrees decimal minutes
## Commented out because long/lat already decimal
#if latitude < 0:
#    latitude = abs(latitude)
#    latitude = str(int(latitude)).zfill(2) + str(round(60*(latitude - int(latitude)),2)).zfill(2) + 'S'
#else:
#    latitude = str(int(latitude)).zfill(2) + str(round(60*(latitude - int(latitude)),2)).zfill(2) + 'N'

#if longitude < 0:
#    longitude = abs(longitude)
#    longitude = str(int(longitude)).zfill(3) + str(round(60*(longitude - int(longitude)),2)).zfill(2) + 'W'
#else:
#    longitude = str(int(longitude)).zfill(3) + str(round(60*(longitude - int(longitude)),2)).zfill(2) + 'E'

winddir = str(weather.get('winddir')).zfill(3)
windspeed = str(int(math.ceil(weather.get('windspeedmph')))).zfill(3)
windgust = str(int(math.ceil(weather.get('windgustmph')))).zfill(3)
if weather.get('tempf') < 0:
    temp = '-' + str(int(round(weather.get('tempf')))).zfill(2)
else:
    temp = str(int(round(weather.get('tempf')))).zfill(3)


########## TESTING ############
#Ambient API only gives hourly rain rate, not actual amount. Removed from CWOP packet until functional.
#Counter to compare dailyrainin on each run, set difference to rainhour, and reset to 0 every 60 minutes.
#
#rainhour = 000
#rainold = int(pickle.load( open( "rainhour.p", "rb" ) ))
#rainnew = int(weather.get('dailyrainin')*100)
#raincheck = rainnew - rainold
#
#
#if raincheck <= 0:
#	rainhour = str(rainold).zfill(3)
#else:
#	rainhour = str(rainnew - rainold).zfill(3)
#	
#rainint = pickle.load( open( "rainint.p", "rb" ) )
#			    
#if rainint <= 60:
#	pickle.dump( rainhour, open( "rainhour.p", "wb" ) )
#	rainint = rainint + 10 #Set this value to your schedule interval (i.e. every 10, 15, 30, 60 minutes, etc.)
#	pickle.dump( rainint, open( "rainint.p", "wb" ) )
#else:
#	rainreset = 000
#	pickle.dump( rainreset, open( "rainhour.p", "wb" ) )
#	pickle.dump( rainreset, open( "rainint.p", "wb" ) )
#			    
###############################

#Ambient API does not provide "rain in last 24 hours." Therefore past24hoursrain only gets reported after 23:40 local time, so rain since midnight is reasonably close to actual past 24 hours.
#Future Task - add a counter that compares dailyrainin on reach run, set as past24hoursrain, and reset every 24 hours.
past24hoursrain = str(int(weather.get('dailyrainin')*100)).zfill(3)

dailyrain = str(int(weather.get('dailyrainin')*100)).zfill(3) #Rain since local midnight / Always reported
pressure = str(int(weather.get('baromrelin')/0.0029529983071445)).zfill(5) #pressure is supposed to be reported to APRS in "altimiter" (QNH) format, that is, relative. The system itself corrects the pressure to sea level based on your station's listed elevation, so make sure that's accurate
humidity = str(int(weather.get('humidity')%100)).zfill(2) #uses modulus operator % so that 100% is given as '00'

# If luminosity is above 999 W/m^2, APRS wants a lowercase L
if weather.get('solarradiation') >= 1000:
	luminosity = 'l' + str(int(round(weather.get('solarradiation'))) % 1000).zfill(3)
else:
	luminosity = 'L' + str(int(round(weather.get('solarradiation')))).zfill(3)
	
########## Generate CWOP Packet ###############
# Time reported in Zulu (UTC). 24-hour rain workaround still has to be local time, though
packet = callsign + '>APRS,TCPIP*:@' + datetime.utcnow().strftime("%d%H%M") + 'z' + latitude + '/' + longitude + '_' + winddir + '/' + windspeed + 'g' + windgust + 't' + temp + 'r' + '...' + 'p' + (past24hoursrain if datetime.now().time() >= time(23,40) else '...') + 'P' + dailyrain + 'h' + humidity + 'b' + pressure + luminosity + devicename
print(packet) #prints the assembled packet for debugging purposes
###############################################

############ Send the Packet ##################
s = socket(AF_INET, SOCK_STREAM)
s.connect(('cwop.aprs.net', 14580))
s.send('user ' + callsign + ' pass -1 vers Python\n')
s.send(packet+'\n')
s.shutdown(0)
s.close()

