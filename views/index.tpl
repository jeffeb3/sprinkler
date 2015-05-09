<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="javascript/jquery-mobile/jquery.mobile.min.css">
<script src="javascript/jquery/jquery.min.js"></script>
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

</head>
<body>

<div data-role="page">
  <div data-role="header">
    <h1>Sprinklers</h1>
  </div>
  <div data-role="main" class="ui-content">
    <form>
    % for zone in zones.keys():
      <label for="flip-' + zone + '"> {{zone}} :</label>
      <select name="flip-' + zone + '" class="ckLED" data-role="slider" data-zone="{{zone}}">
        <option value="off">Off</option>
        <option value="on">On</option>
      </select>
      <br>
    % end
    </form>
    % if None != specialText and len(specialText) != 0:
    <h2>%s</h2>' % specialText
  </div>
</div>

</body>
</html>
