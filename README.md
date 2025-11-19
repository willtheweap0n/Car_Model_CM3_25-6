# Car Model CMM3 Group 3
We are modelling a car to drive a given route at the optimal final drive ratio. We are optimising for fuel efficiency. This Python simulation tool models a vehicle travelling on a real-world route (Edinburgh to Glasgow) to determine the Optimal Final Drive Ratio for maximum fuel efficiency. Beyond fuel economy, it performs physics-based stress tests to ensure the selected gear ratio does not cripple the vehicle's performance (Top Speed and Hill Climbing ability).

Prerequisites: User must have Python 3.x and install the libraries numpy, matplotlib, requests, scipy and pandas. If the route is going to be changed, then a new API key may be needed. This can be done by registering with openrouteservice.org

To run code, simply download and run the FDR Optimisation.ipynb file to a python notebook and run. During the process of running this code, the file final_route_data.csv is created. This data is then used to create the route segments. As the code creates this file during its run, there should be no need to download this file. As a precaution, we have left the file on GitHub. If errors occur while running the code, this file can be downloaded separately.

Section 1: configuration (line 13) section of the code. Defines the constants, vehicle data, and route information.

Section 2: Helper Functions (line 69), including helper functions used to calculate the distance between route points and convert between mph and kph.

Section 3: Core engine Model. (interpolation)(line 109) Using a bivariate spline, this interpolates fuel flow data to model the engine of our car and return a fuel flow map. This data also includes a line for wide-open throttle and closed throttle. This is used to find fuel use for given torques and speeds.

Section 4: Core Physics Functions (line 195) This contains functions that return the engine rpm from car speed and drive ratio. As well as the calculation of total resistive forces.

Section 5: route pre-processing (line 215). This contains functions that will process the route data into usable segments.

Section 6: Hybrid Simulation functions (ODE) (line 260) This contains a function to be used when the car is at constant speed to calculate df/dt for segments of the route where the car speed is not changing. Also contains an acceleration function used when the car is accelerating. This uses an ODE to calculate the changing velocity of the car while at 80% of max torque until the speed limit is reached, which is then used to find df/dt. This is done by calling section 3 to find fuel use for the given torques and speeds

Section 7: Hybrid Engine Simulation (line 382) This contains a function which runs the two hybrid simulation functions over the segments of the route.

Section 8: Optimisation (line 431) function that defines the objectives of the optimisation

Section 9: Route Mapper (line 451) Obtains route data from open route services using start and end coordinates and creates a file. Also applies manual speed limits to data.

Section 10: Top Speed Finder (line 605) defines the Newton-Raphson solver and top speed finder.

Section 11: Max gradient finder (line 687) Defines a function finding the max gradient at 70 mph

Section 12: Main execution (727) Executes functions in correct order.


# Configuration of the Car:
The vehicle can be configured for certain specifications, although the engine must remain the same for fuel flow data. This can be changed, although not much data is available. The following parameters can be modified for different cars: vehicle mass, frontal area, drag Coefficient, rolling Resistance Coefficient, wheel radius, gear Ratios.

# Configuration of route:
Route Start and End coordinates can be changed in the configuration section. In order to accurately change the route, speed limit data will need to be gathered manually and changed in the manual speed limit section.

# Configuration of Driver:
Currently, acceleration is set to occur at 80% of max torque. This can be changed in the get_engine_torque function.

# Troubleshooting:
"Newton-Raphson failed to converge": This usually happens if the vehicle physics are impossible (e.g., trying to climb a 20% grade in 6th gear with a heavy car). The physics solver cannot find a valid equilibrium.

"ORS API Error": Check your internet connection and ensure your API Key is valid.

Simulation Cost 0.0 L: This means the simulation failed to calculate valid engine operating points (likely the RPM dropped below MIN_ENGINE_RPM or the torque required exceeded the engine's max capability). Check your gear ratios.
