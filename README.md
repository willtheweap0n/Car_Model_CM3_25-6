# Car_Model_CM3_25-6
We are modelling a car to drive a given route at the optimal speed. We are optimising for least time spent travelling and maximising fuel conservation. 
A README (or text-type) file explaining: (i) What each file does, (ii) How to run
the code, (iii) Where the three required numerical methods are implemented.
This Python simulation tool models a vehicle traveling on a real-world route (Edinburgh to Glasgow) to determine the Optimal Final Drive Ratio for maximum fuel efficiency.
Beyond fuel economy, it performs physics-based stress tests to ensure the selected gear ratio does not cripple the vehicle's performance (Top Speed and Hill Climbing ability).
Real-World Route Mapping: Uses the OpenRouteService (ORS) API to fetch real path geometry and elevation data.

Hybrid Physics Simulation: Combines ODE solvers (for acceleration events) with algebraic resistance models (for cruising) to calculate fuel flow.

Engine Efficiency Mapping: Uses interpolated BSFC (Brake Specific Fuel Consumption) data based on EPA engine logs.

Geometric Optimization: Uses scipy.optimize to find the exact Final Drive Ratio that minimizes fuel usage over the specific route.

Performance Analysis: Uses Newton-Raphson root-finding algorithms to calculate:

Top Speed (at 0% gradient).

Max Gradeability (max slope climbable at highway speeds).

Customizable Speed Limits: Logic to define speed zones based on distance from the start or end of the journey.

Prerequisites. 
User must have Python 3.x and install the libraries numpy, matplotlib, requests, scipy, pandas
If route is going to be changed then new API key may be needed, this can be done by registering to with openrouteservice.org

Configuration of Car
Vehicle can be configured for certain specifications, although engine must remain the same.
the following parameters can be modified for different cars:
Vehicle mass
Frontal area
Drag Coefficient 
Rolling Resistance Coefficient
Wheel radius
Gear Ratios
Route Start and End coordinates.

Configuration of route.
Route Start and End coordinates can be changed in the configuration section
In order to accurately change the route speed limit data will need to be gathered manually and changed in the manual speed limit section.

Configuration of Driver.
