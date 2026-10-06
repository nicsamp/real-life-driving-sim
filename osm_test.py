from OSMPythonTools.overpass import Overpass
from OSMPythonTools.overpass import overpassQueryBuilder

with open('my_lat_lon.txt', 'r') as f:
    lat_lon = f.read().strip().split(',')
    LAT = float(lat_lon[0])
    LON = float(lat_lon[1])

buffer_degree = 0.001
bbox = [
    LAT - buffer_degree, # miny
    LON - buffer_degree, # minx
    LAT + buffer_degree,  # maxy
    LON + buffer_degree # maxx
]

overpass = Overpass()
query = overpassQueryBuilder(bbox=bbox, elementType='way', selector='"highway"~"motorway|trunk|primary|secondary|tertiary|unclassified|residential|service"', out='geom')
result = overpass.query(query)
geometries = []
for element in result.elements():
    geometry = element.geometry()
    geometries.append(geometry["coordinates"])

print(geometries)