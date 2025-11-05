#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov  5 11:57:04 2025

@author: brucenewlands
"""
    
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Load your route data
df = pd.read_csv("edinburgh_london_route.csv")

def calculate_incline_angles(df):
    """Calculate incline angles between route points."""
    # Calculate elevation change between points
    df['elevation_change_m'] = df['elevation_m'].diff()
    
    # Use forward difference for elevation change (aligns with segment_length)
    df['elevation_change_m'] = df['elevation_change_m'].shift(-1)
    
    # Calculate incline angle in degrees and percent grade
    df['incline_angle_deg'] = np.degrees(np.arctan2(df['elevation_change_m'], df['segment_length_m']))
    df['grade_percent'] = (df['elevation_change_m'] / df['segment_length_m']) * 100
    
    # Clean up infinite values from zero-length segments
    df['grade_percent'] = df['grade_percent'].replace([np.inf, -np.inf], 0)
    df['incline_angle_deg'] = df['incline_angle_deg'].replace([np.inf, -np.inf], 0)
    
    # Fill NaN values (first row)
    df = df.fillna(0)
    
    return df

def plot_route_elevation(df):
    """Plot the elevation profile of the route."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    # Plot 1: Elevation profile
    ax1.plot(df['cumulative_distance_m'] / 1000, df['elevation_m'], 'b-', linewidth=1)
    ax1.set_xlabel('Distance (km)')
    ax1.set_ylabel('Elevation (m)')
    ax1.set_title('Edinburgh to London - Elevation Profile')
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Grade/incline profile
    ax2.plot(df['cumulative_distance_m'] / 1000, df['grade_percent'], 'r-', linewidth=1, alpha=0.7)
    ax2.set_xlabel('Distance (km)')
    ax2.set_ylabel('Grade (%)')
    ax2.set_title('Route Grade Profile')
    ax2.grid(True, alpha=0.3)
    ax2.axhline(y=0, color='k', linestyle='-', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('route_elevation_grade_profile.png', dpi=300, bbox_inches='tight')
    plt.show()

def calculate_torque_requirements(df, vehicle_mass_kg=1500, wheel_radius_m=0.3, 
                                target_speed_ms=25, Crr=0.015, Cd=0.3, A=2.2, rho=1.225):
    """
    Calculate torque requirements for each route segment.
    
    Parameters:
    - vehicle_mass_kg: Mass of vehicle (kg)
    - wheel_radius_m: Wheel radius (m)
    - target_speed_ms: Target speed (m/s) ~90 km/h
    - Crr: Rolling resistance coefficient
    - Cd: Drag coefficient
    - A: Frontal area (m²)
    - rho: Air density (kg/m³)
    """
    
    g = 9.81  # gravity m/s²
    
    # Calculate forces
    df['grade_angle_rad'] = np.radians(df['incline_angle_deg'])
    
    # Grade resistance force
    df['F_grade'] = vehicle_mass_kg * g * np.sin(df['grade_angle_rad'])
    
    # Rolling resistance force
    df['F_roll'] = vehicle_mass_kg * g * Crr * np.cos(df['grade_angle_rad'])
    
    # Aerodynamic drag force
    df['F_drag'] = 0.5 * Cd * A * rho * target_speed_ms**2
    
    # Total force required
    df['F_total'] = df['F_grade'] + df['F_roll'] + df['F_drag']
    
    # Torque at wheels
    df['torque_wheel_nm'] = df['F_total'] * wheel_radius_m
    
    # Power required
    df['power_w'] = df['F_total'] * target_speed_ms
    df['power_kw'] = df['power_w'] / 1000
    
    return df

def plot_torque_analysis(df):
    """Plot torque and power requirements along the route."""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    
    # Plot 1: Torque requirements
    ax1.plot(df['cumulative_distance_m'] / 1000, df['torque_wheel_nm'], 'g-', linewidth=1)
    ax1.set_xlabel('Distance (km)')
    ax1.set_ylabel('Wheel Torque (Nm)')
    ax1.set_title('Torque Requirements Along Route')
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Power requirements
    ax2.plot(df['cumulative_distance_m'] / 1000, df['power_kw'], 'purple', linewidth=1)
    ax2.set_xlabel('Distance (km)')
    ax2.set_ylabel('Power (kW)')
    ax2.set_title('Power Requirements Along Route')
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Force breakdown
    ax3.plot(df['cumulative_distance_m'] / 1000, df['F_grade'].abs(), 'r-', label='Grade Force', alpha=0.7)
    ax3.plot(df['cumulative_distance_m'] / 1000, df['F_roll'], 'b-', label='Rolling Resistance', alpha=0.7)
    ax3.plot(df['cumulative_distance_m'] / 1000, df['F_drag'], 'g-', label='Aerodynamic Drag', alpha=0.7)
    ax3.set_xlabel('Distance (km)')
    ax3.set_ylabel('Force (N)')
    ax3.set_title('Force Components Breakdown')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Grade vs Torque correlation
    scatter = ax4.scatter(df['grade_percent'], df['torque_wheel_nm'], 
                         c=df['elevation_m'], cmap='viridis', alpha=0.6, s=1)
    ax4.set_xlabel('Grade (%)')
    ax4.set_ylabel('Wheel Torque (Nm)')
    ax4.set_title('Grade vs Torque Requirement')
    ax4.grid(True, alpha=0.3)
    plt.colorbar(scatter, ax=ax4, label='Elevation (m)')
    
    plt.tight_layout()
    plt.savefig('torque_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

def generate_summary_statistics(df):
    """Generate summary statistics for the analysis."""
    stats = {
        'Total Distance (km)': df['cumulative_distance_m'].iloc[-1] / 1000,
        'Max Elevation (m)': df['elevation_m'].max(),
        'Min Elevation (m)': df['elevation_m'].min(),
        'Max Grade (%)': df['grade_percent'].max(),
        'Min Grade (%)': df['grade_percent'].min(),
        'Avg Absolute Grade (%)': df['grade_percent'].abs().mean(),
        'Max Torque (Nm)': df['torque_wheel_nm'].max(),
        'Avg Torque (Nm)': df['torque_wheel_nm'].mean(),
        'Max Power (kW)': df['power_kw'].max(),
        'Avg Power (kW)': df['power_kw'].mean()
    }
    
    print("=== ROUTE ANALYSIS SUMMARY ===")
    for key, value in stats.items():
        print(f"{key}: {value:.2f}")
    
    return stats

# Main analysis pipeline
print("Starting route incline and torque analysis...")

# Step 1: Calculate incline angles
df = calculate_incline_angles(df)

# Step 2: Plot elevation and grade profiles
plot_route_elevation(df)

# Step 3: Calculate torque requirements (using typical car parameters)
df = calculate_torque_requirements(
    df, 
    vehicle_mass_kg=1500,    # Typical car mass
    wheel_radius_m=0.3,      # Typical wheel radius
    target_speed_ms=25,      # ~90 km/h
    Crr=0.015,               # Rolling resistance coefficient
    Cd=0.3,                  # Drag coefficient
    A=2.2,                   # Frontal area
    rho=1.225                # Air density
)

# Step 4: Plot torque analysis
plot_torque_analysis(df)

# Step 5: Generate summary statistics
stats = generate_summary_statistics(df)

# Step 6: Save enhanced dataset
df.to_csv("edinburgh_london_route_with_torque.csv", index=False)
print(f"\nEnhanced dataset saved with {len(df)} points")

print("\nFirst 5 points with torque analysis:")
print(df[['lon', 'lat', 'elevation_m', 'grade_percent', 'torque_wheel_nm', 'power_kw']].head().round(4))