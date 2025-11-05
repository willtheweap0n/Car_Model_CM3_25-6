#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov  5 20:43:15 2025

@author: brucenewlands
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize
import warnings
warnings.filterwarnings('ignore')

# Load your enhanced route data
df = pd.read_csv("edinburgh_london_route_with_torque.csv")

class VehicleModel:
    def __init__(self, mass=1500, wheel_radius=0.3, gear_ratios=[3.5, 2.0, 1.5, 1.0, 0.8],
                 final_drive=4.0, engine_max_power=100000, engine_max_torque=200,
                 idle_fuel_rate=0.0003, brake_specific_consumption=250):
        
        self.mass = mass
        self.wheel_radius = wheel_radius
        self.gear_ratios = gear_ratios
        self.final_drive = final_drive
        self.engine_max_power = engine_max_power  # W
        self.engine_max_torque = engine_max_torque  # Nm
        self.idle_fuel_rate = idle_fuel_rate  # kg/s at idle
        self.brake_specific_consumption = brake_specific_consumption  # g/kWh
        
        # Engine efficiency map (simplified)
        self.engine_speeds = np.linspace(800, 6000, 10)  # RPM
        self.engine_torques = np.linspace(0, engine_max_torque, 10)
        
    def calculate_gear(self, speed_ms):
        """Determine appropriate gear based on speed."""
        wheel_rpm = (speed_ms * 60) / (2 * np.pi * self.wheel_radius)
        engine_rpm = wheel_rpm * self.final_drive
        
        for i, ratio in enumerate(self.gear_ratios):
            gear_engine_rpm = wheel_rpm * self.final_drive * ratio
            if gear_engine_rpm <= 4500:  # Optimal RPM range
                return i, gear_engine_rpm
        return len(self.gear_ratios) - 1, wheel_rpm * self.final_drive * self.gear_ratios[-1]
    
    def engine_efficiency(self, engine_rpm, engine_torque):
        """Simplified engine efficiency model."""
        # Normalized RPM (0-1 where 0.7 is optimal)
        rpm_norm = min(1.0, engine_rpm / 3000)
        rpm_penalty = 1.0 - 0.3 * abs(rpm_norm - 0.7)
        
        # Load factor efficiency
        load_factor = min(1.0, engine_torque / self.engine_max_torque)
        load_efficiency = 0.3 + 0.7 * load_factor  # More efficient at higher loads
        
        return rpm_penalty * load_efficiency
    
    def fuel_consumption(self, power_required, speed_ms, duration_s):
        """Calculate fuel consumption for given power requirement."""
        if power_required <= 0:  # Coasting or braking
            return self.idle_fuel_rate * duration_s
        
        # Get gear and engine RPM
        gear, engine_rpm = self.calculate_gear(speed_ms)
        total_ratio = self.gear_ratios[gear] * self.final_drive
        
        # Engine torque required
        engine_torque = power_required / (engine_rpm * np.pi / 30)
        engine_torque = min(engine_torque, self.engine_max_torque)
        
        # Engine efficiency
        efficiency = self.engine_efficiency(engine_rpm, engine_torque)
        
        # Fuel consumption calculation
        power_kw = power_required / 1000
        fuel_flow_kg_per_s = (power_kw * (self.brake_specific_consumption / 3600000)) / efficiency
        
        return fuel_flow_kg_per_s * duration_s

def simulate_route_with_constant_speed(df, target_speed_ms, vehicle):
    """Simulate fuel consumption with constant speed strategy."""
    fuel_consumed = 0
    fuel_data = []
    
    for i in range(len(df) - 1):
        segment_length = df['segment_length_m'].iloc[i]
        if segment_length == 0:
            continue
            
        duration = segment_length / target_speed_ms
        power_req = df['power_w'].iloc[i]
        
        segment_fuel = vehicle.fuel_consumption(power_req, target_speed_ms, duration)
        fuel_consumed += segment_fuel
        fuel_data.append(fuel_consumed)
    
    return fuel_consumed, fuel_data

def optimize_speed_profile(df, vehicle, max_speed=30, min_speed=10):
    """Optimize speed profile for minimum fuel consumption."""
    
    def objective(speeds):
        """Objective function: total fuel consumption."""
        total_fuel = 0
        
        for i in range(len(df) - 1):
            if df['segment_length_m'].iloc[i] == 0:
                continue
                
            # Use average speed for the segment
            segment_speed = (speeds[i] + speeds[i+1]) / 2
            duration = df['segment_length_m'].iloc[i] / max(segment_speed, 0.1)
            
            # Recalculate power for this speed
            grade_angle_rad = np.radians(df['incline_angle_deg'].iloc[i])
            g = 9.81
            
            F_grade = vehicle.mass * g * np.sin(grade_angle_rad)
            F_roll = vehicle.mass * g * 0.015 * np.cos(grade_angle_rad)
            F_drag = 0.5 * 0.3 * 2.2 * 1.225 * segment_speed**2
            F_total = F_grade + F_roll + F_drag
            power_req = F_total * segment_speed
            
            segment_fuel = vehicle.fuel_consumption(power_req, segment_speed, duration)
            total_fuel += segment_fuel
            
        return total_fuel
    
    # Initial guess: constant moderate speed
    n_segments = len(df)
    initial_speeds = np.ones(n_segments) * 20  # 20 m/s ~ 72 km/h
    
    # Constraints: speed limits
    bounds = [(min_speed, max_speed) for _ in range(n_segments)]
    
    # Smoothness constraint (speed changes gradually)
    def smoothness_constraint(speeds):
        max_acceleration = 0.5  # m/s²
        constraints = []
        for i in range(len(speeds) - 1):
            if df['segment_length_m'].iloc[i] > 0:
                dt = df['segment_length_m'].iloc[i] / speeds[i]
                acceleration = (speeds[i+1] - speeds[i]) / dt
                constraints.append(max_acceleration - abs(acceleration))
        return np.array(constraints)
    
    # Solve optimization
    constraints = {'type': 'ineq', 'fun': smoothness_constraint}
    
    result = minimize(objective, initial_speeds, method='SLSQP', 
                     bounds=bounds, constraints=constraints,
                     options={'maxiter': 100, 'disp': True})
    
    return result

def advanced_fuel_optimization(df, vehicle):
    """More sophisticated optimization considering acceleration and gear selection."""
    
    # Simple strategy: slow down on uphills, speed up on downhills
    optimized_speeds = np.ones(len(df)) * 20  # Base speed 20 m/s
    
    # Adjust speed based on grade
    for i in range(len(df)):
        grade = df['grade_percent'].iloc[i]
        
        if grade > 5:  # Steep uphill
            optimized_speeds[i] = max(15, 20 - grade * 0.5)
        elif grade < -5:  # Steep downhill
            optimized_speeds[i] = min(25, 20 - grade * 0.3)
        else:  # Moderate terrain
            optimized_speeds[i] = 20
    
    # Smooth the speed profile
    from scipy.ndimage import gaussian_filter1d
    optimized_speeds = gaussian_filter1d(optimized_speeds, sigma=2)
    
    return optimized_speeds

def plot_fuel_analysis(df, constant_fuel, optimized_fuel, optimized_speeds):
    """Plot fuel consumption analysis."""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    
    # Plot 1: Speed profiles
    ax1.plot(df['cumulative_distance_m'] / 1000, np.ones(len(df)) * 20 * 3.6, 
             'b-', label='Constant 72 km/h', alpha=0.7)
    ax1.plot(df['cumulative_distance_m'] / 1000, optimized_speeds * 3.6, 
             'r-', label='Optimized Speed', alpha=0.8)
    ax1.set_xlabel('Distance (km)')
    ax1.set_ylabel('Speed (km/h)')
    ax1.set_title('Speed Profiles Comparison')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Grade vs Speed
    ax2.scatter(df['grade_percent'], optimized_speeds * 3.6, 
               c=df['elevation_m'], cmap='viridis', alpha=0.6, s=2)
    ax2.set_xlabel('Grade (%)')
    ax2.set_ylabel('Optimized Speed (km/h)')
    ax2.set_title('Speed Adaptation to Grade')
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Fuel consumption comparison
    strategies = ['Constant Speed', 'Optimized Speed']
    fuel_kg = [constant_fuel, optimized_fuel]
    bars = ax3.bar(strategies, fuel_kg, color=['blue', 'red'], alpha=0.7)
    ax3.set_ylabel('Fuel Consumption (kg)')
    ax3.set_title('Fuel Consumption Comparison')
    
    # Add value labels on bars
    for bar, value in zip(bars, fuel_kg):
        ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                f'{value:.2f} kg', ha='center', va='bottom')
    
    # Plot 4: Power distribution
    ax4.hist(df['power_kw'], bins=50, alpha=0.7, color='green', edgecolor='black')
    ax4.set_xlabel('Power (kW)')
    ax4.set_ylabel('Frequency')
    ax4.set_title('Power Requirement Distribution')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('fuel_optimization_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

# Main optimization analysis
print("Starting fuel consumption modeling and optimization...")

# Initialize vehicle model
vehicle = VehicleModel(
    mass=1500,
    wheel_radius=0.3,
    engine_max_power=100000,  # 100 kW
    engine_max_torque=200,    # 200 Nm
    brake_specific_consumption=250  # g/kWh
)

# Strategy 1: Constant speed
print("\n1. Simulating constant speed strategy...")
constant_speed = 25  # m/s ~ 90 km/h
constant_fuel, _ = simulate_route_with_constant_speed(df, constant_speed, vehicle)
print(f"Constant speed fuel consumption: {constant_fuel:.2f} kg")

# Strategy 2: Optimized speed profile
print("\n2. Calculating optimized speed profile...")
optimized_speeds = advanced_fuel_optimization(df, vehicle)

# Calculate fuel for optimized profile
optimized_fuel = 0
for i in range(len(df) - 1):
    if df['segment_length_m'].iloc[i] == 0:
        continue
        
    segment_speed = (optimized_speeds[i] + optimized_speeds[i+1]) / 2
    duration = df['segment_length_m'].iloc[i] / segment_speed
    
    # Recalculate power for optimized speed
    grade_angle_rad = np.radians(df['incline_angle_deg'].iloc[i])
    g = 9.81
    
    F_grade = vehicle.mass * g * np.sin(grade_angle_rad)
    F_roll = vehicle.mass * g * 0.015 * np.cos(grade_angle_rad)
    F_drag = 0.5 * 0.3 * 2.2 * 1.225 * segment_speed**2
    F_total = F_grade + F_roll + F_drag
    power_req = F_total * segment_speed
    
    segment_fuel = vehicle.fuel_consumption(power_req, segment_speed, duration)
    optimized_fuel += segment_fuel

print(f"Optimized speed fuel consumption: {optimized_fuel:.2f} kg")
print(f"Fuel savings: {((constant_fuel - optimized_fuel) / constant_fuel * 100):.1f}%")

# Plot results
plot_fuel_analysis(df, constant_fuel, optimized_fuel, optimized_speeds)

# Add optimized speeds to dataframe
df['optimized_speed_ms'] = optimized_speeds
df['optimized_speed_kmh'] = optimized_speeds * 3.6

# Save results
df.to_csv("edinburgh_london_route_optimized.csv", index=False)
print(f"\nOptimized dataset saved with {len(df)} points")

# Print key insights
print("\n=== OPTIMIZATION INSIGHTS ===")
print(f"Total distance: {df['cumulative_distance_m'].iloc[-1]/1000:.1f} km")
print(f"Constant speed strategy: {constant_fuel:.2f} kg fuel")
print(f"Optimized strategy: {optimized_fuel:.2f} kg fuel")
print(f"Fuel savings: {constant_fuel - optimized_fuel:.2f} kg ({((constant_fuel - optimized_fuel) / constant_fuel * 100):.1f}%)")
print(f"Average optimized speed: {df['optimized_speed_kmh'].mean():.1f} km/h")