#!/usr/bin/python

from bottle import run, Bottle
from hwio import *

web = Bottle()
hw = hwio()

zones = {
    'Front':3, 
    'Back North':5,
    'Back South':12,
    'Way Back':7
    }


def GetStatus(specialText=None):
    text = ''
    text += '<html><body>'
    text += '<h1>'
    text += 'Sprinker controls<br>'
    text += '</h1>'
    if None != specialText and len(specialText) != 0:
        text += '<h2>%s</h2>' % specialText
    text += '<table>'
    for zone in zones.keys():
        status = ''
        if GPIO.input(zones[zone]) == False: # That means it's on
            status = 'Running'
        text += '<tr><td>%s:</td><td><a href="/on/%s">Turn On</a></td><td><a href="/off/%s">Turn Off</a></td><td>%s</td></tr>' % (zone, zone, zone, status)
    text += '</table>'
    text += '</body></html>'
    return text

@web.route('/')
def Index():
    return GetStatus()

@web.route('/on/<zone>')
def TurnOn(zone=None):
    if not zone in zones.keys(): 
        print "I don't know about zone: %s" % zone 
        return GetStatus("I don't know about zone: %s" % zone)
    print "Turned zone '%s' on" % zone
    GPIO.output(zones[zone], False)
    return GetStatus("Turned zone '%s' on" % zone)

@web.route('/off/<zone>')
def TurnOff(zone=None):
    if not zone in zones.keys(): 
        print "I don't know about zone: %s" % zone 
        return GetStatus("I don't know about zone: %s" % zone)
    print "Turned zone '%s' off" % zone
    GPIO.output(zones[zone], True)
    return GetStatus("Turned zone '%s' off" % zone)

run(web, host='10.0.2.105', port=8080)

