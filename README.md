# Car_Model_CM3_25-6

We are modelling a car to drive a given route at the optimal final drive ratio. We are optimising for fuel efficiency. 
This Python simulation tool models a vehicle traveling on a real-world route (Edinburgh to Glasgow) to determine the Optimal Final Drive Ratio for maximum fuel efficiency.
Beyond fuel economy, it performs physics-based stress tests to ensure the selected gear ratio does not cripple the vehicle's performance (Top Speed and Hill Climbing ability).

To run code simply run the python script in the FDR Optimisation file.

Section 1: configuration (line 13)
section one of the code defines the constants, vehicle data, and route information.

Section 2: Helper Functions (line 69)
This includes helper functions used to calculate distance between route points.
and convert between mph and kph.

Section 3: Core engine Model. (interpolation)(line 109)
Using bivariate spline this interpolates fuel flow data to model the engine of our car and return a fuel flow map. This data also includes a line for wide open throttle and closed throttle. This is used to find fuel use for given torques and speeds.

Section 4: Core Physics Functions (line 195)
This contains functions that return the engine rpm from car speed and drive ratio. As well as calculation of total resistive forces.

Section 5: route pre-processing (line 215)
This contains functions that will process the route data into usable segments.

Section 6: Hybrid Simulation functions (ODE) (line 260)
This contains a function to be used when car is at constant speed to calculate df/dt for segments of the route where car speed is not changing.
Also contains acceleration function used when car is accelerating. This uses an ODE to calculate the changing velocity of the car while at 80% of max torque until speed limit is reached, which is then used to find df/dt. This is done by calling section 3 to find fuel use for given torques and speeds

Section 7: Hybrid Engine Simulation (line 382)
This contains a function which runs the two hybrid simulation functions over the segments of the route.

Section 8: Optimization (line 431)
function that defines the objectives of the optimization

Section 9: Route Mapper (line 451)
Obtains route data from open route services using start and end coordinates and creates file. Also applies manual speed limits to data. 

Section 10: Top Speed finder (line 605)
Defines newton raphson solver, and top speed finder.

Section 11: Max gradient finder (line 687)
Defines function finding max gradient at 70 mph

Section 12: main execution
Executes functions in correct order.

Prerequisites. 
User must have Python 3.x and install the libraries numpy, matplotlib, requests, scipy, pandas
If route is going to be changed then new API key may be needed, this can be done by registering to with openrouteservice.org

Configuration of Car

Vehicle can be configured for certain specifications, although engine must remain the same for fuel flow data. This can be changed although not much data is available
.
the following parameters can be modified for different cars:
vehicle mass,
frontal area,
drag Coefficient,
rolling Resistance Coefficient,
wheel radius,
gear Ratios,

Configuration of route:

Route Start and End coordinates can be changed in the configuration section
In order to accurately change the route speed limit data will need to be gathered manually and changed in the manual speed limit section.

Configuration of Driver:

Currently acceleration is set to occur at 80% of max torque. this can be changed in the get_engine_torque function.


troubleshooting

"Newton-Raphson failed to converge": This usually happens if the vehicle physics are impossible (e.g., trying to climb a 20% grade in 6th gear with a heavy car). The physics solver cannot find a valid equilibrium.

"ORS API Error": Check your internet connection and ensure your API Key is valid.

Simulation Cost 0.0 L: This means the simulation failed to calculate valid engine operating points (likely the RPM dropped below MIN_ENGINE_RPM or torque required exceeded the engine's max capability). Check your gear ratios.
