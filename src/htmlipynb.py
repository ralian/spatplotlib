def format(**params):
  return f"""<head>
  {chr(10).join([l.render(embedded=params['embed_links']) for l in params['links']])}
  <style>
    .leaflet-container .leaflet-tile {{
       margin: 0;
    }}
    .leaflet-control-zoom-in {{
        text-decoration: none !important;
    }}
    .leaflet-control-zoom-out {{
        text-decoration: none !important;
    }}
    #map{params['mapid']} {{
      height:{params['height']}px;
    }}
  </style>
</head>
<body>
<div id="map{params['mapid']}"></div>
<script text="text/javascript">
func{params['mapid']} = function() {{
  var map = L.map('map{params['mapid']}');
  L.tileLayer(
    "{params['tile_url']}",
    {{maxZoom:19, attribution: '{params['attribution']}'}}).addTo(map);
  var gjData = {params['geojson']};
  
  if (gjData.features.length != 0) {{
    var gj = L.geoJson(gjData, {{
      style: function (feature) {{
        return feature.properties;
      }},
      pointToLayer: function (feature, latlng) {{
        var icon = L.divIcon({{'html': feature.properties.html,
          iconAnchor: [feature.properties.anchor_x,
                       feature.properties.anchor_y],
            className: 'empty'}});  // What can I do about empty?
        return L.marker(latlng, {{icon: icon}});
      }}
    }});
  
    gj.addTo(map);
    map.fitBounds(gj.getBounds());
  }} else {{
    map.setView([0, 0], 1);
  }}
}}
setTimeout(function() {{ func{params['mapid']}() }}, 2000);
</script>
</body>
"""