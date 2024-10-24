import streamlit as st
import folium
from streamlit_folium import st_folium

# Define a simple folium map centered at a specific location
m = folium.Map(location=[37.7749, -122.4194], zoom_start=12)

# Add a sample marker to the map
folium.Marker([37.8044, -122.2712], popup="San Francisco").add_to(m)

# Display the map in Streamlit
st_folium(m, width=700, height=500)
