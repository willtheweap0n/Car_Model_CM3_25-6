!pip install folium

import folium
import pandas as pd

df = pd.read_csv("final_route_data.csv")

# Center map halfway between start and end
center = [(df.lat.iloc[0] + df.lat.iloc[-1]) / 2, (df.lon.iloc[0] + df.lon.iloc[-1]) / 2]
m = folium.Map(location=center, zoom_start=6)

# Add the route polyline (folium uses [lat, lon])
route_latlon = list(zip(df['lat'], df['lon']))
folium.PolyLine(route_latlon, weight=4).add_to(m)

# Add start/end markers
folium.Marker(route_latlon[0], popup="Start").add_to(m)
folium.Marker(route_latlon[-1], popup="End").add_to(m)

m  # in Jupyter this will render the interactive map
