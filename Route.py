#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov  5 11:46:47 2025

@author: brucenewlands
"""

import requests
import pandas as pd
import numpy as np
from scipy.spatial import cKDTree
import time

# Configuration
API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImJmMWQ0ZjgyNmNhZTRjZjA5M2I5ODAzMDkyZTY1MTJjIiwiaCI6Im11cm11cjY0In0="

# Route coordinates: Edinburgh to London
START = [-3.1883, 55.9533]  # [lon, lat]
END = [-0.1276, 51.5074]

def get_osrm_route(start, end):
    """Get high-resolution route geometry from OSRM."""
    url = f"https://router.project-osrm.org/route/v1/driving/{start[0]},{start[1]};{end[0]},{end[1]}?overview=full&geometries=geojson"
    
    response = requests.get(url)
    print(f"OSRM Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        coords = data["routes"][0]["geometry"]["coordinates"]
        df = pd.DataFrame(coords, columns=["lon", "lat"])
        print(f"Received {len(df)} route points from OSRM")
        return df
    else:
        raise Exception(f"OSRM API error: {response.text}")

def get_ors_elevation(coords, api_key):
    """Get elevation data from ORS Elevation API in batches."""
    elevations = []
    
    for i in range(0, len(coords), 100):
        batch = coords[i:i+100]
        
        # Correct format for ORS Elevation API
        locations = [[lon, lat] for lon, lat in batch]
        
        body = {
            "locations": locations,
            "format": "point"
        }
        
        headers = {
            "Authorization": api_key,
            "Content-Type": "application/json"
        }
        
        url = "https://api.openrouteservice.org/elevation/line"
        response = requests.post(url, headers=headers, json=body)
        
        if response.status_code == 200:
            data = response.json()
            if 'geometry' in data and 'coordinates' in data['geometry']:
                batch_elevations = [point[2] for point in data['geometry']['coordinates']]
                elevations.extend(batch_elevations)
                print(f"Successfully processed elevation batch {i//100 + 1}")
            else:
                print(f"Unexpected response format in batch {i//100 + 1}")
                elevations.extend([None] * len(batch))
        else:
            print(f"Elevation API error {response.status_code}: {response.text}")
            # Fill with None for failed batch
            elevations.extend([None] * len(batch))
        
        time.sleep(0.2)  # Rate limiting
    
    return elevations

def calculate_route_metrics(df):
    """Calculate distance metrics for the route."""
    # Convert to radians for haversine calculation
    lat_rad = np.radians(df["lat"].to_numpy())
    lon_rad = np.radians(df["lon"].to_numpy())
    
    # Earth radius in meters
    R = 6371000
    
    # Calculate distances between successive points
    dlat = lat_rad[1:] - lat_rad[:-1]
    dlon = lon_rad[1:] - lon_rad[:-1]
    
    a = np.sin(dlat/2)**2 + np.cos(lat_rad[:-1]) * np.cos(lat_rad[1:]) * np.sin(dlon/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    distances = R * c
    
    # Add to DataFrame
    df["segment_length_m"] = np.concatenate([[0], distances])
    df["cumulative_distance_m"] = np.cumsum(df["segment_length_m"])
    
    print(f"Average point spacing: {np.mean(distances):.1f} meters")
    print(f"Total route distance: {df['cumulative_distance_m'].iloc[-1]/1000:.1f} km")
    
    return df

def get_elevation_fallback(route_df):
    """Fallback method using Open-Elevation API if ORS fails."""
    print("Attempting fallback elevation data...")
    elevations = []
    
    for i in range(0, len(route_df), 100):
        batch = route_df.iloc[i:i+100]
        locations = []
        
        for _, row in batch.iterrows():
            locations.append(f"{row['lat']},{row['lon']}")
        
        locations_str = "|".join(locations)
        url = f"https://api.open-elevation.com/api/v1/lookup?locations={locations_str}"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                batch_elevations = [result['elevation'] for result in data['results']]
                elevations.extend(batch_elevations)
                print(f"Fallback elevation batch {i//100 + 1} successful")
            else:
                print(f"Fallback API error: {response.status_code}")
                elevations.extend([0] * len(batch))  # Use 0 as default
        except Exception as e:
            print(f"Fallback API exception: {e}")
            elevations.extend([0] * len(batch))
        
        time.sleep(0.5)
    
    return elevations

def main():
    print("Generating Edinburgh to London route...")
    
    # Step 1: Get high-resolution route from OSRM
    route_df = get_osrm_route(START, END)
    
    # Step 2: Get elevation data
    print("Fetching elevation data from ORS...")
    coords_list = route_df[["lon", "lat"]].values.tolist()
    elevations = get_ors_elevation(coords_list, API_KEY)
    
    # Check if elevation data was successfully obtained
    successful_elevations = [e for e in elevations if e is not None]
    if len(successful_elevations) < len(route_df) * 0.8:  # Less than 80% success
        print("ORS elevation API had limited success, using fallback...")
        elevations = get_elevation_fallback(route_df)
    
    # Add elevation to dataframe
    route_df["elevation_m"] = elevations
    
    # Step 3: Calculate route metrics
    route_df = calculate_route_metrics(route_df)
    
    # Step 4: Save final dataset
    output_file = "edinburgh_london_route.csv"
    route_df.to_csv(output_file, index=False)
    
    print(f"Successfully saved {len(route_df)} route points to '{output_file}'")
    print("\nData summary:")
    print(f"Coordinates range: Lon ({route_df['lon'].min():.3f} to {route_df['lon'].max():.3f})")
    print(f"Coordinates range: Lat ({route_df['lat'].min():.3f} to {route_df['lat'].max():.3f})")
    print(f"Elevation range: {route_df['elevation_m'].min():.1f} to {route_df['elevation_m'].max():.1f} meters")
    print(f"Total distance: {route_df['cumulative_distance_m'].iloc[-1]/1000:.1f} km")
    
    print("\nFirst 5 points:")
    print(route_df.head())
    
    return route_df

if __name__ == "__main__":
    route_data = main()
    
    
    
    
   