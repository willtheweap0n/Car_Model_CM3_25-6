import numpy as np
import matplotlib.pyplot as plt
#import sympy as sym

velocities = np.linspace(0.1, 60, 500) # m/s

# -----Car properties-----
mass = 1780 #kg
frontal_area = 1 #m^2
C_d = 1.05 # Drag for cube
C_rr = 0.01 # Rolling resistance coefficient
length = 2 # It appears to be length that matters for flow past bluff body
g = 9.81 #m/s^2
wetted_area = 6 # Total area in contact with air. 6 m^2 for a cube
tyre_radius = 0.335 # m. Average value for passenger cars (probably need to choose specific tyres)
# Calculation of dynamic radius probably later

# -----Air properties-----
p_air = 1.225 #kg/m^3
viscosity = 1.8e-5 #kg/ms

def skin_friction(velocity):
    Re = (p_air * velocity * length) / viscosity
    if Re >= 2e5:
        # Turbulent flow
        C_f = 0.074 / (Re**(1/5))
    elif Re <= 1e5:
        # Laminar flow
        C_f = 1.4 / (Re**(1/2))
    else:
        # This is what copilot said. I have no clue what to do when 1e5 < Re < 2e5. This is better than nothing I guess.
        # Transitional flow, interpolate between laminar and turbulent
        C_f_laminar = 1.4 / (1e5**(1/2))
        C_f_turbulent = 0.074 / (2e5**(1/5))
        C_f = C_f_laminar + (C_f_turbulent - C_f_laminar) * ((Re - 1e5) / (2e5 - 1e5))
    F_skin = 0.5 * p_air * C_f * wetted_area * velocity**2
    return F_skin

def drag(velocity):
    F_drag = 0.5 * p_air * C_d * frontal_area * velocity**2
    return F_drag

def surface_forces():   # Will probably input angle
    weight = mass * g
    F_normal = weight # Flat road for now
    F_rr = C_rr * F_normal
    return F_rr

def total_resistive_forces(velocity):
    F_skin = skin_friction(velocity)
    F_drag = drag(velocity)
    F_rr = surface_forces()
    F_total = F_skin + F_drag + F_rr
    return F_total, F_skin, F_drag, F_rr

def plot(Power_req, Torque_req, F_total, F_skin, F_drag, F_rr, x_var):   # x_var can be velocity or rpm
    plt.figure(figsize=(10,6))
    #plt.plot(x_var, Power_req, label='Power required (W)', color='blue')
    #plt.plot(x_var, Torque_req, label='Torque required (Nm)', color='red')
    plt.plot(x_var, F_total, label='Total Resistive Force', color='black')
    plt.plot(x_var, F_skin, label='Skin Friction', linestyle='--')
    plt.plot(x_var, F_drag, label='Drag', linestyle='-.')
    plt.plot(x_var, F_rr, label='Rolling Resistance', linestyle=':')
    plt.xlabel('Velocity (m/s)')
    plt.ylabel('Force (N)')
    plt.title('Resistive Forces vs Velocity')
    plt.legend()
    plt.grid(True)
    plt.show()

def vehicle_forces(F_total, velocity, radius):
    P_required = F_total * velocity  # Power in Watts
    Torque_required = F_total * radius   # Giving strange results
    return P_required, Torque_required

def vel_to_rpm(velocity, radius):
    rpm = (velocity / (2 * np.pi * radius)) * 60.0
    return rpm

def main():
    F_total_list = []
    F_skin_list = []
    F_drag_list = []
    F_rr_list = []
    P_req_list = []
    Torque_req_list= []
    wheel_rpm_list = []
    for i in range(len(velocities)):
        velocity = velocities[i]
        wheel_rpm = vel_to_rpm(velocity, tyre_radius)
        wheel_rpm_list.append(wheel_rpm)
        F_total, F_skin, F_drag, F_rr = total_resistive_forces(velocity)
        P_required, Torque_required = vehicle_forces(F_total, velocity, tyre_radius)
        P_req_list.append(P_required)
        Torque_req_list.append(Torque_required)
        F_total_list.append(F_total)
        F_skin_list.append(F_skin)
        F_drag_list.append(F_drag)
        F_rr_list.append(F_rr)
    plot(P_req_list, Torque_req_list, F_total_list, F_skin_list, F_drag_list, F_rr_list, velocities)

if __name__ == "__main__":
    main()