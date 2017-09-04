#Name: RouteSolveNoBarriers.py
#stand alone python script
#This script is the second script in a set of 4 python scripts
#Author: Elsit Mandal, MGIS Program Penn State University-World Campus
#Date:6/20/17
#####################################################################

#This script was developed as part of  Capstone project -- ArcGIS Decision Support Tool for Planning Infrastructure Improvement--Penn State MGIS

#https://gis.e-education.psu.edu/sites/default/files/capstone/Mandal_report_596B_20170715.pdf
#####################################################
 
# Description: Solve best route (without any barriers)for a set of OD pairs and save the output to a feature class

######################################

# Requirements: Network Analyst Extension, Routable Network Dataset
#5 parameters
#Inputs: 1.Routable network dataset
#2. Origin (point) feature class, 3. Destination (point feature class),
#4.output feature class where the shortest path routes will be appended to.  
#5. The work space file geodatabase where the origin, destination and the route feature class will be saved
# Note: There is a text file to capture some print statements c:\\temp\\GPMessages.txt
#Origins and Destinations should have SER_NUM field

#"C:\\StateSystemOnly\\DissolveND.gdb\\StateSystemOnly\\StateSystemOnly_ND" "Origins_10" "Destinations_10" "testNoBarr" "C:\\StateSystemOnly\\TestGeoDatabase.gdb"

#########################################################################
#
# Origin and Destination are in pairs, they have same unique_id (field:'SER_NUM'). The output from the first Script is to be used as input in this script.

############################################################################################
class LicenseError(Exception):
    pass
#Import system modules

import datetime

#Import system modules
import arcpy
import traceback
from arcpy import env

try:
    if arcpy.CheckExtension ("Network")== 'Available':

    #Check out the Network Analyst extension 
        arcpy.CheckOutExtension("Network")
    else:
        raise LicenseError
except LicenseError:
    print "Network Analyst Extension is unavailable"
    sys.exit()
######################################################################################



print datetime.datetime.now().time()

start_time = time.time()
#####################################################################################
def main():
    try:
        
        ws1 = arcpy.env.workspace = arcpy.GetParameterAsText(4)
        env.overwriteOutput = True
       
        inNetworkDataset = arcpy.GetParameterAsText(0)
        
        inOrigins = ws1+"\\"+ arcpy.GetParameterAsText(1)
        print inOrigins
      
        txtFile = open("c:\\temp\\GPMessages.txt","w")
       
        txtFile.write (str(datetime.datetime.now().time()) +"\n")
       
        inDestinations = ws1+"\\"+arcpy.GetParameterAsText(2)
        print inDestinations
       
        outRoutesFC2 =  ws1+"\\"+ arcpy.GetParameterAsText(3) #no barrier routes
        arcpy.TruncateTable_management(outRoutesFC2)#if there are any existing features from previous runs, delete those.
        #####################################################################
        #######################################################################
        


        
        #####################################################################################################################################
        # print number of OD pairs as info for user  
        odPairCount = arcpy.GetCount_management(inOrigins);
        print  ("odPairCount is  "+ str(odPairCount)+ "\n")
        txtFile.write ("odPairCount is  "+ str(odPairCount)+ "\n")
        
        odPairCountNum = int(str(odPairCount));
        
        #sort the origin and destination by SER_NUM so that the each row make an OD pair
        
        sort_field = [ ["SER_NUM", "ASCENDING"]]    
        arcpy.Sort_management(inOrigins, "in_memory/sort_Origins", sort_field)
        arcpy.Sort_management(inDestinations, "in_memory/sort_Destinations", sort_field)
        
        
        #try arcpy.da.SearchCursor later
        rows1 = arcpy.SearchCursor("in_memory/sort_Origins");
        rows2 =arcpy.SearchCursor("in_memory/sort_Destinations");
        
        inOrigins =rows1.next()
        inDestinations =rows2.next()
        count = int(odPairCount.getOutput(0))
            
        #for loop will go through all the OD pairs
        for x in xrange (1,count+1):
            print "--------------------------------------"
            print x
            
            #print "time elapsed =  "+ (round(time.time() - start_time)
            fieldName = "SER_NUM"
            perID_orig= inOrigins.getValue(fieldName)
            perIDStr = str(perID_orig)
            perID_dest= inDestinations.getValue(fieldName)
            perID_destStr = str(perID_dest)
            
            if perIDStr != perID_destStr:# if origin id and destinaion id are not same, we have an error
                print " OD pair data error: exiting"
                sys.exit()
            else:
                pass
                
            
            inOrigins1 ="inOrigins1"
            inDestinations1 = "inDestinations1"
            whereClause_OD= 'SER_NUM = '+str(perID_orig)
            print whereClause_OD
            txtFile.write(whereClause_OD+"\n")
            arcpy.AddMessage ("-------------------------------"  + whereClause_OD+"-----------------------")
            arcpy.MakeFeatureLayer_management("in_memory/sort_Origins",inOrigins1, whereClause_OD)
            arcpy.MakeFeatureLayer_management("in_memory/sort_Destinations",inDestinations1, whereClause_OD)
               

            arcpy.AddMessage ("starting no barrier solve")
            


            tOutRoutesFC = RouteSolverNoBarriers(inNetworkDataset,inOrigins1,inDestinations1)
            
            #RouteSover returns list of 2 things. First is the route, the second is a boolean which is True if there is a route solution
            
            myBoolean= tOutRoutesFC[1]
            print myBoolean
            
            # if there was a route solve, myBoolean will be set to True in the RouteSolver function
            if myBoolean == True:
                print "no barrier case, there is route solved"
                txtFile.write("no barrier case, there is route solved"+"\n")
                arcpy.AddMessage ("no barrier case, there is route solved")
                outRoutesFC=tOutRoutesFC[0]
               
                arcpy.management.Append(outRoutesFC, outRoutesFC2)
                
                arcpy.AddMessage ("------- no barrier solve completed----------")
                txtFile.write("----- no barrier solve completed----------"+"\n")
                        
                    #############################################
                
                del inOrigins1
                del inDestinations1
                inOrigins=rows1.next();
                inDestinations = rows2.next();
                   
            else: #else means there is no route solved 
                arcpy.AddMessage ("route could not be solved for this OD pair")
                print ("route could not be solved for this OD pair") 
                txtFile.write  ("route could not be solved for this OD pair") 
                
                del inOrigins1
                del inDestinations1
                inOrigins=rows1.next();
                inDestinations = rows2.next();
            
        
        print "Script completed successfully"
        txtFile.write ("Script completed successfully")
        
        print datetime.datetime.now().time()
        ####################################
    ####end main try()    
    except:
        print "An error Occurred"
        #txtFile.close()
        tb=sys.exc_info() [2]
        tbinfo =traceback.format_tb(tb)[0]
        pymsg= "PYTHON ERRORS:\nTracebakinfo:\n"+tbinfo+"\nErrorInfo:\n"+str(sys.exc_type)+":"+str(sys.exc_value)+"\n"
        arcpy.AddError (pymsg)
        msgs= "Arcpy ERRORS: \n"+arcpy.GetMessages(2)+"\n"
        arcpy.AddError (msgs)
        print pymsg +"\n"
        print msgs
        
    finally:
        
        arcpy.CheckInExtension ("Network")
        txtFile.write ("Completed")
        
        print("---elapsed time  %s seconds ---" % round(time.time() - start_time, 2))
        txtFile.write ("---elapsed time  %s seconds ---" % round(time.time() - start_time, 2))
        
        txtFile.close()
       

    
###################################################

    
def RouteSolverNoBarriers(inNetworkDataset,inOrigins,inDestinations):
    #returns the best route feature layer and a boolean to show if there are was any barrier for the current OD pair
    #print "in Route Solver"
    outNALayerName = "BestRoutes"
    impedanceAttribute = "Length"
    outRoutesFC = "outRoutes2"
    boolRouteSolved = False
    OD_SnapToler='30 Meters'
    OD_uniq_fieldName = 'SER_NUM'
    outLines ="TRUE_LINES_WITHOUT_MEASURES"
    
    #options are: TRUE_LINES_WITHOUT_MEASURES,TRUE_LINES_WITH_MEASURES,NO_LINES,STRAIGHT_LINES
   
    outRouteResultObject = arcpy.na.MakeRouteLayer(inNetworkDataset, outNALayerName,impedanceAttribute, accumulate_attribute_name= ["DrivingTime"],restriction_attribute_name= ["Oneway"],output_path_shape=outLines,hierarchy="NO_HIERARCHY")
    
    #Get the layer object from the result object. The route layer can now be eferenced using the layer object.
    outNALayer = outRouteResultObject.getOutput(0)

    #Get the names of all the sublayers within the route layer.
    subLayerNames = arcpy.na.GetNAClassNames(outNALayer)
    #Store the layer names that we will use later
        
    StopsLayerName = subLayerNames["Stops"]
    routesLayerName = subLayerNames["Routes"]
       
    fieldMappings = arcpy.na.NAClassFieldMappings(outNALayer, StopsLayerName)
    fieldMappings["RouteName"].mappedFieldName = OD_uniq_fieldName
    
    arcpy.na.AddLocations(outNALayer, StopsLayerName, inOrigins, fieldMappings,OD_SnapToler)
            
   
    arcpy.na.AddLocations(outNALayer, StopsLayerName, inDestinations, fieldMappings,OD_SnapToler)
   
    try:

        #Solve the route layer.
        arcpy.na.Solve(outNALayer)
        boolRouteSolved = True
        print ("route with no barrier solved")
    except:
        print "Route Solve Execution error occurred, for this OD pair"
        return (0, boolRouteSolved)
        

    # Get the output Routes sublayer and save it to a feature class
    RoutesSubLayer = arcpy.mapping.ListLayers(outNALayer, routesLayerName)[0]
    arcpy.management.CopyFeatures(RoutesSubLayer, outRoutesFC)
       
           
    del inOrigins,inDestinations,outNALayer
    
    return (outRoutesFC, boolRouteSolved )
    
    ##############################################################################################################################
    ##################################################################################################################################
def BuildWhereClause(table, field, value):
        
    # Add field delimiters
    fieldDelimited = arcpy.AddFieldDelimiters(table, field)
    # get field type
    fieldType = arcpy.ListFields(table, field)[0].type
    
    expression = value
    
    if str(fieldType) == 'String':
        expression = "'%s'" % expression
    
    whereClause = "%s = %s" % (fieldDelimited, expression)
    return whereClause
##############################################################
main()
###############################################################
###################################################################









































