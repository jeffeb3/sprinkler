#!/usr/bin/python

from bottle import run, Bottle
from bottle import route, static_file, request
from hwio import *

web = Bottle()
hw = hwio()

zones = {
    'Front':3, 
    'Back North':5,
    'Back South':12,
    'Way Back':7
    }


HEADER = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="javascript/jquery-mobile/jquery.mobile.min.css">
<script src="javascript/jquery/jquery.min.js"></script>
<script src="javascript/jquery-flot/jquery.flot.js"></script>
<script src="javascript/jquery-mobile/jquery.mobile.min.js"></script>
<script>
  $(document).ready(function() {
    $(".ckLED").on('change',function() {
      var isChecked = $(this).val();
      var zone = $(this).data('zone')
      $.ajax({
              url: '/action',
              type: 'POST',
              data: { strID:'ckLED', strState:isChecked, strZone:zone }
      });
    });
  });
</script> 
<!--script>$.plot($("#placeholder"), [ [[0, 0], [1, 1]] ], { yaxis: { max: 1 } });</script-->
<script>
  $(function() {
    var d1 = [];
    for (var i = 0; i < 14; i += 0.5) {
      d1.push([i, Math.sin(i)]);
    }
    var d2 = [[0, 3], [4, 8], [8, 5], [9, 13]];
    // A null signifies separate line segments
    var d3 = [[0, 12], [7, 12], null, [7, 2.5], [12, 2.5]];
    $.plot("#placeholder", [ d1, d2, d3 ]);
  });
</script>
   

</head>
<body>

<div data-role="page">
  <div data-role="header">
    <h1>Sprinklers</h1>
  </div>

"""
FOOTER = """
</div> 

</body>
</html>
"""

def GetStatus(specialText=None):
    text = HEADER
    text += '<div data-role="main" class="ui-content">'
    text += '  <form> '
    for zone in zones.keys():
      text += '    <label for="flip-' + zone + '">' + zone + ':</label>'
      text += '    <select name="flip-' + zone + '" class="ckLED" data-role="slider" data-zone="' + zone + '">'
      text += '      <option value="off">Off</option>'
      text += '      <option value="on">On</option>'
      text += '    </select>'
      text += '    <br>'
    text += '    </form>'
    text += '    <div id=placeholder style="width: 100%;height:400px; text-align: center; margin:0 auto;"></div>'
    if None != specialText and len(specialText) != 0:
        text += '<h2>%s</h2>' % specialText
    text += '  </div>'
    return text

@web.route('/')
def Index():
    return GetStatus()

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

run(web, host='10.0.2.105', port=8080)

