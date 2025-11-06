import matplotlib.pyplot as plt
import numpy as np

# Simulated motor characteristics for a typical EV motor
rpm = np.linspace(0, 16000, 500)  # motor speed range
max_torque = 300  # Nm (example motor)
base_rpm = 5000  # point where torque starts to drop

# Torque curve: flat until base_rpm, then decreases inversely with speed
torque = np.piecewise(
    rpm,
    [rpm <= base_rpm, rpm > base_rpm],
    [lambda x: max_torque, lambda x: max_torque * base_rpm / x]
)

# Power curve: P = torque * angular speed (in rad/s), then converted to kW
power = torque * (rpm * 2 * np.pi / 60) / 1000

# Plotting
fig, ax1 = plt.subplots(figsize=(8, 5))

color_torque = 'tab:blue'
color_power = 'tab:red'

ax1.set_xlabel("Motor Speed (RPM)")
ax1.set_ylabel("Torque (Nm)", color=color_torque)
ax1.plot(rpm, torque, color=color_torque, label="Torque")
ax1.tick_params(axis='y', labelcolor=color_torque)

ax2 = ax1.twinx()
ax2.set_ylabel("Power (kW)", color=color_power)
ax2.plot(rpm, power, color=color_power, linestyle='--', label="Power")
ax2.tick_params(axis='y', labelcolor=color_power)

plt.title("Typical EV Motor Torque and Power Curves")
plt.grid(True)
plt.tight_layout()
plt.show()