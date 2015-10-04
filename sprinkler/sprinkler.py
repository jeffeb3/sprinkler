
# The place where the sprinkler runs.

# system imports
import bisect
import commands
import copy
import datetime
import json
import logging
import threading
import time
import urllib
import urllib2
from collections import deque

from email_utils import sendemail

# local imports
import settings
from hwio import hwio

# zones is a map from a zone number to a pin number and name.
zones = {
    1:(3, "Front Yard"), # Front
    2:(5, "Back Yard North"), # Back North
    4:(12, "Back Yard South"), # Back South
    3:(7, "Back Yard Trees") # Way back
    }

def uptime():
    ''' get this system's seconds since starting. Apparently this works with cygwin. '''
    with open('/proc/uptime', 'r') as f:
        uptime_seconds = float(f.readline().split()[0])
        return uptime_seconds

def freeMem():
    ''' get this system's free memory (unix and cygwin supported).'''
    text = commands.getoutput('free -m').split('\n')
    for line in text:
        if '-/+ buffers' in line:
            values = line.split()
            used = float(values[2])
            free = float(values[3])
            return used / (used + free)

class Sprinkler(threading.Thread):
    """
    Sprinkler contains the main loop, and anything that aren't big
    enough for their own module/file. There should be no web here.
    """

    def __init__(self):
        """
        Creates a thread (but doesn't start it).
        :logHandlers: A list of logging.handlers to append to my log.
        """
        threading.Thread.__init__(self)
        # Set to daemon so the main thread will exit even if this is still going.
        self.daemon = True

        # run these events right away.
        self.lastLoopTime = 0
        self.lastOutsideMeasurementTime = 0

        # state
        self.previous_zone = None
        self.startTime = time.time()

        # cache
        self.outsideTemp = 0
        self.override = 0
        self.overrideTime = time.time()

        self.zones = zones

        # state data history
        self.plotData = deque([], 60/5*72)
        self.recentHistory = deque([], 10) # deque will only keep maxlen items. I'm shooting for five minutes
        self.plotDataLock = threading.RLock()

        # log
        self.log = logging.getLogger(__name__)

        # hwio
        self.hwio = hwio()

        #try:
        #    sendemail(settings.Get("email_from"), settings.Get("email_to").split(','), [],'Sprinklers restarted', '', settings.Get("email_from"), settings.Get("email_passw"))
        #except Exception as e:
        #    # swallow any exceptions, we don't want the sprinkler to break if there is no Internet
        #    self.log.exception(e)

    def run(self):
        """
        Main loop for the sprinkler project. Reads data from external sources,
        updates internal data, and sends data out to data recorders.
        """
        self.log.info('Starting the Sprinkler Thread');
        while True:     # Forever
            # this try...except block is to log all exceptions. It's in this
            # while loop because the while loop should recover.
            try:
                # sleep a moment at a time, so that we can catch the quit signal
                while (time.time() - self.lastLoopTime) < 30.0:
                    time.sleep(0.5)

                self.lastLoopTime = time.time()

                # Gather data from Wunderground, but only every 10 minutes (limited for free api account)
                outsideTempUpdated = False
                if ((time.time() - self.lastOutsideMeasurementTime) > 360):
                    try:
                        outsideData = json.load(urllib2.urlopen("http://api.wunderground.com/api/" +
                                                                settings.Get("weather_api_key") + "/conditions/q/" +
                                                                settings.Get("weather_state") + '/' + settings.Get("weather_city") + ".json"))
                        self.outsideTemp = outsideData['current_observation']['temp_f']
                        self.log.debug('Retrieved outside temp:' + str(self.outsideTemp))
                        outsideTempUpdated = True
                        self.lastOutsideMeasurementTime = time.time()
                    except Exception as e:
                        # swallow any exceptions, we don't want the sprinkler to break if there is no Internet
                        self.log.exception(e)
                        pass

                active_zone = self.GetCurrentZone()

                data = {}
                data["time"] = time.time() * 1000.0
                data["linux_uptime_ms"] = uptime() * 1000.0
                data["linux_free_mem_perc"] = freeMem() * 100.0
                data["py_uptime_ms"] = (time.time() - self.startTime) * 1000.0
                data["outside_temp"] = self.outsideTemp
                data["outside_temp_updated"] = outsideTempUpdated
                data["active_zone"] = active_zone
                if active_zone is None:
                    # I need a float to be able to plot it and stuff.
                    data["active_zone"] = 0

                self.log.debug('Active Zone: %d', data['active_zone'])

                with self.plotDataLock:
                    self.recentHistory.append(data)

                self.updatePlotData()

                try:
                    self.speak()
                except Exception as e:
                    self.log.exception(e)

                if active_zone != self.previous_zone:
                    self.actuateZone(active_zone)

            except Exception as e:
                self.log.exception(e)
                time.sleep(60.0) # sleep for extra long.
                continue

    def updatePlotData(self):
        ''' Add data to the plotData based on the recent history '''

        with self.plotDataLock:
            if len(self.plotData) == 0 or self.recentHistory[0]['time'] > self.plotData[-1]['time']:
                self.log.debug('updating plot data, len %d', len(self.plotData))
                data = copy.deepcopy(self.recentHistory[-1])
                self.plotData.append(data)

    def ComputeProgram(self):
        # TODO get these from the config file/settings instead.
        zones = [1, 2, 3, 4]
        minutes = [36, 27, 0, 21]
        starttime = 10
        cycles = 3

        program = {}

        for cycle in range(cycles):
            for idx, minute in enumerate(minutes):
                if minute <= 0:
                    continue
                time = starttime
                starttime += minute / cycles

                program[time] = idx + 1
        program[starttime] = None

        return program

    def setOverride(self, zone):
        """ Overrides whatever is currently being activated. This also can clear the override if sent with a None."""
        self.override = zone
        self.overrideTime = time.time()
        self.actuateZone(zone)

    def GetCurrentZone(self):

        if self.override is not None and self.override > 0:
            if time.time() - self.overrideTime > 600.0:
                self.log.info("Clearing the override, because it's been %f seconds in this override state.", time.time() - self.overrideTime)
                self.override = 0
            else:
                return self.override

        if not settings.Get("doWater"):
            self.log.debug("Not watering because it's been disabled")
            return None

        now = datetime.datetime.now()
        day = settings.DAYS[(now.weekday() + 1) % 7] # python says 0 is Monday.
        # TODO figure out which days to water. based on lots of stuff.
        if day != 'Sunday' and day != 'Wednesday' and day != 'Friday':
            return None

        # returns a zone (positive integer) or zero
        program = self.ComputeProgram()
        program_times = program.keys()
        program_times.sort()

        minutes = now.minute + 60*now.hour

        # use bisect to find the "insertion point"
        index = bisect.bisect(program_times, minutes)
        if not index:
            # We haven't reached the starttime yet
            return None

        # return active zone, which is index - 1. This is the less than equal:
        return program[program_times[index - 1]]

    def actuateZone(self, active_zone):
        if active_zone is None:
            self.log.info("Turning off the sprinklers")
        else:
            self.log.info('setting new zone to %s, "%s"', str(active_zone), zones[active_zone][1])

        if self.previous_zone is not None:
            self.hwio.output(zones[self.previous_zone][0], True)
        if active_zone is not None:
            self.hwio.output(zones[active_zone][0], False)
        if active_zone is None:
             sendemail(settings.Get("email_from"), settings.Get("email_to").split(','), [],'Sprinklers ran', '', settings.Get("email_from"), settings.Get("email_passw"))
        self.previous_zone = active_zone

    def speak(self):
        """ Record last data to thingspeak. """
        if not settings.Get('doThingspeak'):
            # don't log to thing speak.
            return

        raise InputError("I don't support this for the sprinkler yet")
        channelData = {}
        channelData['key'] = settings.Get("thingspeak_api_key")

        with self.plotDataLock:
            data = self.recentHistory[-1]

            channelData['field1'] = data['temperature']
            if data["outside_temp_updated"]:
                channelData['field2'] = data['outside_temp']
            channelData['field3'] = data['heat']
            channelData['field4'] = data['heatSetPoint']
            channelData['field5'] = data['cool']
            channelData['field6'] = data['coolSetPoint']
            channelData['field7'] = data['uptime_ms'] / 1000.0
            channelData['field8'] = data['py_uptime_ms'] / 1000.0

        headers = \
        {
            'Content-type': 'application/x-www-form-urlencoded',
            'Accept': 'text/plain'
        }
        enc = urllib.urlencode(channelData)
        req = urllib2.Request('https://api.thingspeak.com/update', enc, headers)
        response = urllib2.urlopen(req)

    def copyData(self):
        """ Retrieve the latest data. """
        with self.plotDataLock:
            return copy.deepcopy(self.recentHistory[-1])

    def getPlotHistory(self):
        ''' returns a dictionary with variables defined for the updater template.'''
        # store this information in key-value pairs so that the template engine can find them.
        updaterInfo = \
        {
            "zoneHistory" : '',
            "updateTimeHistory" : '',
            "memHistory" : '',
        }

        with self.plotDataLock:
            for data in self.plotData:
                updaterInfo['zoneHistory']   += '[ %f, %f],' % (data["time"] - (time.timezone * 1000.0), data["active_zone"])
                updaterInfo['updateTimeHistory']    += '[ %f, %d],' % (data["time"] - (time.timezone * 1000.0), data["py_uptime_ms"])
                updaterInfo['memHistory']           += '[ %f, %d],' % (data["time"] - (time.timezone * 1000.0), data["linux_free_mem_perc"])

        # Add the outside brackets to each plot data.
        for key, value in updaterInfo.items():
            updaterInfo[key] = '[' + value + ']'

        return updaterInfo
