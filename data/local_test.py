from pyrosm import OSM
FILE = "data/nordeste-260925.osm.pbf"

with open('my_lat_lon.txt', 'r') as f:
    lat_lon = f.read().strip().split(',')
    LAT = float(lat_lon[0])
    LON = float(lat_lon[1])

buffer_degree = 0.005
bbox = [
    LON - buffer_degree, # minx
    LAT - buffer_degree, # miny
    LON + buffer_degree, # maxx
    LAT + buffer_degree  # maxy
]

print("loading map...")
osm = OSM(FILE, bounding_box = bbox)

print("finding roads...")
roads = osm.get_pois(custom_filter = {"highway": ["*"]})

print(roads)