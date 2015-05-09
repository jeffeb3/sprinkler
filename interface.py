#!/usr/bin/python

from bottle import run, Bottle
from bottle import route, static_file, request, template
from hwio import *

web = Bottle()
hw = hwio()

zones = {
    'Front':3,
    'Back North':5,
    'Back South':12,
    'Way Back':7
    }

@web.route('/')
def Index():
  return template('index', zones = zones, specialText = None)

# handle the change of the switch:
@web.route('/action', method='POST')
def action():
  on = request.forms.get('strState').startswith('on')
  zone = request.forms.get('strZone')
  if not zone in zones.keys():
    print "I don't know about zone: %s" % zone
    return
  print "Turned zone '%s' on" % zone
  GPIO.output(zones[zone], not on)
  print 'Zone:' + request.forms.get('strZone') + ' = ' + str(on)

# router for the jquery scripts
@web.route('/javascript/<path:path>')
def JavascriptCallback(path):
  return static_file('javascript/'+path, root='.')

run(web, host='0.0.0.0', port=8080)
