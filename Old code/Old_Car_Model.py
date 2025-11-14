"""
We are modelling a Golf MK VIII with 1.2-litre TSI 85 PS engine unit. 
Technical specifications can be found here: https://www.vwpress.co.uk/press-kits/988, https://www.vwpress.co.uk/assets/documents/original/17282-Tech_spec_1.pdf


C_DRAG = 0.275
C_ROLLING_RESISTANCE = 30 * C_DRAG
AIR_DENSITY = 1.2 #kg/m^3
CAR_FRONTAL_AREA = 2.21 #m^2
TOTAL_MASS = 1850 #kg (1780kg car + 70kg human)

#1D (x direction) FORCES - NO TURNING
drag_force =
friction_force =
rolling_force =

net_force_x = drag_force + friction_force + rolling_force

#1D (x direction) FORCES - NO TURNING
"""

import numpy as np
from scipy.interpolate import interp1d, RegularGridInterpolator, CubicSpline
from scipy.integrate import cumulative_trapezoid
from scipy.optimize import brentq

# ---------- Example vehicle parameters ----------
m = 1500.0                      # kg
r_w = 0.33                      # wheel radius m
rho = 1.225
Cd = 0.30
A = 2.2
Crr = 0.012
i_fd = 3.9                      # final drive
eta_driv = 0.92
gears = np.array([3.8, 2.2, 1.5, 1.0, 0.8])  # gear ratios
mu = 0.9                        # grip, for corner limit
# ---------- End params ----------

# ---------- Given path arrays (N points) ----------
# x,y,z are numpy arrays from your data
# Example placeholders
# x, y, z = load_your_path(...)
# For demo:
N = 1000
s_dummy = np.linspace(0,1000,N)
x = s_dummy
y = np.zeros_like(x)
z = 0.01*np.sin(x/50.0)

# ---------- compute segment lengths, slopes, curvature ----------
dx = np.diff(x); dy = np.diff(y); dz = np.diff(z)
dhoriz = np.sqrt(dx**2 + dy**2)
ds = np.sqrt(dx**2 + dy**2 + dz**2)
s = np.concatenate(([0.0], np.cumsum(ds)))
s_seg = ds.copy()

# slope (radians) per segment
slope = np.arctan2(dz, dhoriz + 1e-12)  # avoid div by zero

# discrete curvature approx using triplets (simple)
# Use curvature = |(x'y'' - y'x'')| / (x'^2 + y'^2)^(3/2)
# approximate derivatives by finite differences:
x_p = np.gradient(x, s)
y_p = np.gradient(y, s)
x_pp = np.gradient(x_p, s)
y_pp = np.gradient(y_p, s)
curvature = np.abs(x_p * y_pp - y_p * x_pp) / (np.maximum((x_p**2 + y_p**2),1e-12)**1.5)
radius = np.divide(1.0, curvature, out=np.full_like(curvature, np.inf), where=curvature>0)

# max speed from curvature (lateral grip)
v_curve = np.sqrt(np.maximum(0.0, mu * 9.81 / np.maximum(curvature,1e-12)))
v_curve[~np.isfinite(v_curve)] = 50.0  # cap infinity to some large value

# ----------
# Engine maps (example synthetic)
omega_grid = np.array([1000,1500,2000,2500,3000,3500,4000,4500,5000,5500,6000])
Tmax_curve = np.array([130,160,160,160,155,150,140,130,120,100,80])
T_interp = interp1d(omega_grid, Tmax_curve, kind='cubic', fill_value='extrapolate')

# Example BSFC map (BSFC [g/kWh]) as function of omega and torque — here simple function:
def bsfc(omega_rpm, torque_Nm):
    # small surrogate: best BSFC near 2000-3000 RPM and mid torque
    return 250 + 0.02*(omega_rpm-2500)**2 + 0.1*(torque_Nm-100)**2  # g/kWh

# ---------- discrete speed decision variables (initial guess) ----------
# start with v at each node equal to min(curve_limit, some speed)
v0 = np.minimum(v_curve, 25.0)  # initial guess 25 m/s cap

# Example forward-backward pass to enforce accel/brake limits and engine torque availability
a_max = 2.0     # m/s2 (max acceleration)
a_min = -4.0    # m/s2 (max braking)

# Convert to node speeds and enforce acceleration feasibility
v = v0.copy()
# forward pass (accelerate)
for i in range(len(v)-1):
    vmax_possible = np.sqrt(v[i]**2 + 2*a_max*max(s_seg[i],1e-6))
    v[i+1] = min(v[i+1], vmax_possible, v_curve[i+1])

# backward pass (braking)
for i in reversed(range(len(v)-1)):
    vmax_possible = np.sqrt(v[i+1]**2 + 2*(-a_min)*max(s_seg[i],1e-6))
    v[i] = min(v[i], vmax_possible, v_curve[i])

# Compute segment times using trapezoidal rule
v_mid = 0.5*(v[:-1] + v[1:])
delta_t = 2*s_seg / (v[:-1] + v[1:] + 1e-12)  # time on each segment
total_time = np.sum(delta_t)

# Compute fuel for each segment by computing required force and estimating engine operating point
fuel_mass = 0.0
for i in range(len(s_seg)):
    v_avg = v_mid[i]
    # kinematics accel
    a = (v[i+1]**2 - v[i]**2) / (2*max(s_seg[i],1e-6))
    F_acc = (m) * a
    F_drag = 0.5 * rho * Cd * A * v_avg**2
    F_rr = Crr * m * 9.81 * np.cos(slope[i])
    F_grade = m * 9.81 * np.sin(slope[i])
    F_req = F_acc + F_drag + F_rr + F_grade  # positive -> traction, negative -> braking

    # find gear and torque feasible
    # try gears and choose minimal fuel (or minimal throttle)
    best_fuel = np.inf
    for g in gears:
        omega_e_rpm = (v_avg / r_w) * g * 60.0/(2*np.pi)
        T_wheel_required = F_req * r_w
        T_engine_required = T_wheel_required / (g * i_fd * eta_driv + 1e-12)

        if T_engine_required < 0:
            # braking or negative torque: assume engine idling + braking performed by brakes
            # simple model: braking fuel = idle fuel rate * dt (approx)
            fuel_segment = 0.0001 * delta_t[i]  # placeholder small idle fuel
        else:
            Tmax = float(T_interp(np.clip(omega_e_rpm, omega_grid[0], omega_grid[-1])))
            if T_engine_required <= Tmax:
                power_kW = (omega_e_rpm * 2*np.pi/60.0) * T_engine_required / 1000.0
                # bsfc returns g/kWh
                bsfc_val = bsfc(omega_e_rpm, T_engine_required)
                fuel_rate_gps = bsfc_val * power_kW / 3600.0  # g/s
                fuel_segment = fuel_rate_gps * delta_t[i] / 1000.0  # convert g to kg
            else:
                fuel_segment = np.inf  # not feasible in this gear

        if fuel_segment < best_fuel:
            best_fuel = fuel_segment

    fuel_mass += best_fuel

print(f"Total time (s): {total_time:.1f}, fuel (kg): {fuel_mass:.3f}")
