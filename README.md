# CapstoneProjectTools
The scripts were developed as part of  Capstone project -- ArcGIS Decision Support Tool for Planning Infrastructure Improvement--Penn State MGIS
The tool set developed includes scripts to analyze and visualize Oversize/Overweight (OSOW) routing data available from the Permit System
and to select candidate bridges  (acting as barriers to OSOW traffic) for improvement or replacement based on their spatial location 
in the context of OSOW traffic demand.
For Capstone project  final report, visit the URL 
https://gis.e-education.psu.edu/sites/default/files/capstone/Mandal_report_596B_20170715.pdf 

1. AnalyzeOSOWRoutes.py

Description: Make OD pairs from OSOW shape file and
State boundary polygon, and a buffer distance. Outputs the Origin_destination point featureclasses, OD Lines Frequency polygon
and traffic classification as Interstate, Inbound, Outbound or Intrastate 

2. RouteSolveNoBarriers.py 

Description: Solve best route (without any barriers)for the set of OD pairs and save the output to a 
feature class 

3. RouteSolveWithBarriers.py 

Description: Solve best route for a set of OD pairs and barriers save the output to a prenamed (hard-coded)feature class
in the workspace each run will intialize the ExtraMiles,Counter,DYN_UPDATE_FLAG  field in bridges, truncate prenamed output fc 
