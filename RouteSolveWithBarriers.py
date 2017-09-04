#RouteSolveWithBarriers.py
#stand alone python script
#This script is the third script in a set of 4 python scripts
#Author: Elsit Mandal, MGIS Program Penn State University-World Campus
#Date:6/20/17
#Description: Solve best route for a set of OD pairs and barriers save the output to a prenamed (hard-coded)feature class in the workspace
#each run will intialize the TIMELOST,Counter,DYN_UPDATE_FLAG  field in bridges, truncate prenamed output fc

######################################
#
# Requirements: Network Analyst Extension, Routable Network Dataset
#PARAMETERS
#1.Network data set
#2.Origin (point) feature class,
#3. Destination (point feature class),
#4. Bridges feature class
#5. feature class from route solve with no barriers
#6 empty Feature class to save the routes with barriers
#7.workspace geodb location

#sample  parameters as below.
#"C:\\StateSystemOnly\\DissolveND.gdb\\StateSystemOnly\\StateSystemOnly_ND" "Origins_10" "Destinations_10" "BRID_LE15_ExtraMiles_R" "testNoBarr" "testBarr" "C:\\StateSystemOnly\\TestGeoDatabase.gdb"
#There is a text file to capture some print statements c:\\temp\\GPMessages.txt
#Origins and Destinations should have SER_NUM, HeightFt, LengthFt, Tonnage fields 
#barrier bridges should have CLLEARANCE, POSTED, ExtraMiles,Counter,DYN_UPDATE_FLAG  fields

#Barriers snapped at 5m, OD snapped at 30 m. Update if necessary in the RouteSolverWithBarriers function

#########################################################################
#
# Origin and Destination are in pairs, they have same SER_NUM, oversize overweight (OSOW) truck dimension attributes.
#Depending on the truck height (HeightFt attribute in Origin or Destination)and avaialble vertical clearance in feet(CLEARANCE) of bridges, 'POINT BARRIERS' are identified..

############################################################################################
class LicenseError(Exception):
    pass

import datetime
import math #used for rounding math.ceil
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
        #Set local variables
        #write messages to a text file
        txtFile = open("c:\\temp\\GPMessages.txt","w")
        print("RouteSolve with Barriers started; Precondition-Routes geometry with no barrier solve should exist"+"\n")
        txtFile.write (str(datetime.datetime.now().time()) +"\n")
        txtFile.write("RouteSolve with Barriers started; Precondition-Routes geometry with no barrier solve should exist"+"\n")
                
        print("process comments will be saved in text file at c:\\temp\\GPMessages.txt"+"\n")
        
      
        ws1 = arcpy.env.workspace = arcpy.GetParameterAsText(6)
        print ("workspace is  "+ws1)
        env.overwriteOutput = True
        
        inNetworkDataset = arcpy.GetParameterAsText(0)
        inOrigins = ws1+ "\\"+ arcpy.GetParameterAsText(1)
        print ("Origin Point fc is   "+inOrigins+ "\n")
        arcpy.AddMessage ("Origin Point fc is   "+inOrigins+ "\n")
        txtFile.write ("Origin Point fc is   "+inOrigins+ "\n")
        
        
        inDestinations = ws1+ "\\"+arcpy.GetParameterAsText(2)
        
        print ("Destination Point fc is   "+inDestinations+ "\n")
        
        txtFile.write ("Destination Point fc is   "+inDestinations+ "\n")
        
        
        inBarriers = ws1+ "\\"+arcpy.GetParameterAsText(3)
        print ("Barrier Point fc is   "+inBarriers+ "\n")
        
        txtFile.write ("Barrier Point fc is   "+inBarriers+ "\n")
        
        
        outRoutesFC2 = ws1+ "\\"+arcpy.GetParameterAsText(4)
        print ("RouteSolve with No barrierst fc is   "+outRoutesFC2+ "\n")
        
        txtFile.write("RouteSolve with No barrierst fc is   "+outRoutesFC2+ "\n")
        
        outRoutesFC22 = ws1+ "\\"+arcpy.GetParameterAsText(5)
        print ("RouteSolve with Barriers fc will be saved as"+outRoutesFC22+"in workspace"+"\n")
        txtFile.write("RouteSolve with Barriers fc will be saved as"+outRoutesFC22+"in workspace"+"\n")
        
        
        imped_param1='Total_Length'
        
         
        #####################################################################################################################################
        # print number of OD pairs as info for user
        odPairCount = arcpy.GetCount_management(inOrigins);
        print ("odPairCount is  "+ str(odPairCount)+ "\n")
        txtFile.write ("odPairCount is  "+ str(odPairCount)+ "\n")
       
        odPairCountNum = int(str(odPairCount));
        routesCount = arcpy.GetCount_management(outRoutesFC2);
        txtFile.write (" Route count for no barrier solution "+ str(routesCount)+ "\n")
        print(" Route count for no barrier solution "+ str(routesCount)+ "\n")
        #sort the origin and destination by SER_NUM so that the each row make an OD pair
        
        ##############################################################################
        
        #InitializeParameters in Barrier feature
        arcpy.CalculateField_management(inBarriers,"Counter","0","PYTHON_9.3") 
        arcpy.CalculateField_management(inBarriers,"ExtraMiles","0","PYTHON_9.3")
          
        arcpy.TruncateTable_management(outRoutesFC22)#delete records in any previous existing with barrier feature

        ###################################################################################
        
        sort_field = [ ["SER_NUM", "ASCENDING"]]    
        arcpy.Sort_management(inOrigins, "in_memory/sort_Origins", sort_field)
        arcpy.Sort_management(inDestinations, "in_memory/sort_Destinations", sort_field)  
        
        rows1 = arcpy.SearchCursor("in_memory/sort_Origins");
        rows2 =arcpy.SearchCursor("in_memory/sort_Destinations");
        
        inOrigins =rows1.next()
        inDestinations =rows2.next()
        count = int(odPairCount.getOutput(0))
        
        #for loop will go through all the OD pairs
        
        for x in xrange (1,count+1):
            print "--------------------------------------"
            print ("OD pair Num "+ str(x)+"\n")
            arcpy.AddMessage ("OD pair Num "+ str(x) +"\n")
            fieldName = 'SER_NUM'
            
            fieldName1 = "HeightFt"
            fieldName2 = "Tonnage_class"
            fieldName3 = "Length_class"
            fieldName4='FREQ'
            
            perID_orig= inOrigins.getValue(fieldName)
            
            perIDStr = str(int(perID_orig))
            perID_dest= inDestinations.getValue(fieldName)
            frequ=inOrigins.getValue(fieldName4)
            arcpy.AddMessage("frequ is "+str(frequ))
            perID_destStr = str (int(perID_dest))
                
            if perIDStr != perID_destStr:# if origin id and destinaion id are not same, we have an error
                print " OD pair data error: exiting"
                
                arcpy.AddMessage(" OD pair data error: exiting")
                sys.exit()
            else:
                pass
            
            
            whereClausex= BuildWhereClause(outRoutesFC2,"Name",perIDStr)#used for selecting no barrier route corresp. to PRMT_ID
            arcpy.AddMessage( "whereCluse to find no barr rte is"+whereClausex)
            
            no_barr_lyr ="no_barr_lyr"
                                           
            arcpy.MakeFeatureLayer_management(outRoutesFC2,no_barr_lyr,whereClausex)
           
            fc_count =arcpy.GetCount_management(no_barr_lyr)
            if int(str(fc_count)) >0:# which means that there is a route solved for no barrier case
                whereClause_OD= 'SER_NUM = '+str(perID_orig)
                arcpy.AddMessage ("-------------------------------"  + whereClause_OD+"-----------------------"+"\n")
                arcpy.AddMessage (" There is a route for no barrier case for this OD pair"+"\n")                                    
                print (str(fc_count)+" there is a route for no barrier case for this OD pair")
                truck_height = str(inOrigins.getValue(fieldName1))
                
               
                Tonnage_class=inOrigins.getValue(fieldName2)
                Length_class= inOrigins.getValue(fieldName3)
                
                
                print "OSOW Truck height is "+ truck_height
                txtFile.write ("OSOW Truck height is "+ truck_height+"FT"+"\n")
                arcpy.AddMessage("OSOW Truck height is "+ truck_height+"FT"+"\n")
                
                print "OSOW Tonnage_class is "+Tonnage_class
                txtFile.write ("OSOW Tonnage_class is "+Tonnage_class+"\n")
                arcpy.AddMessage("OSOW Tonnage_class is "+Tonnage_class+"\n")
                arcpy.AddMessage("OSOW Length_class is "+Length_class+"\n")
                whereClause_ht = "CLEARANCE"+" <" +truck_height
                
                
                inOrigins1 ="inOrigins1"
                inDestinations1 = "inDestinations1"
                
                
                print ("-------------------------------"  + whereClause_OD+"-----------------------")
                
                txtFile.write("-------------------------------"  + whereClause_OD+"-----------------------"+"\n")
                arcpy.MakeFeatureLayer_management("in_memory/sort_Origins",inOrigins1, whereClause_OD)
                arcpy.MakeFeatureLayer_management("in_memory/sort_Destinations",inDestinations1, whereClause_OD)
                
                
                lengthNoBarrierMiles = math.ceil(getTotal_ImpedanceParamValue(no_barr_lyr,imped_param1))
                
                txtFile.write( "lengthNoBarrierMiles is " +str (lengthNoBarrierMiles)+"\n")
                arcpy.AddMessage( "lengthNoBarrierMiles is " +str (lengthNoBarrierMiles)+"\n")
                
                BarrierParamUpdateCounter=0
                extraMiles=0
                print ("Total number of Bridges is = "+str(arcpy.GetCount_management(inBarriers)))
                # this is where the barriers spatial intersecting with the NoBarrierRouteSolve layer is getting DYN_UPDATE_FLG set to 'Y'
                BarrierBoolean = getBarriersToUpdateExtraMiles(inBarriers, no_barr_lyr,whereClause_ht,Tonnage_class,Length_class,txtFile)# if barriers exists, continue to slove
                
                print ("BarrierBoolean  is"  +str(BarrierBoolean))
                if BarrierBoolean: #if there are barriers with shortest path continue the process in step1
                    #inBarriers2 =  tupBarriers[0]
                    txtFile.write ("There are barriers on the shortest path for this OD pair")
                    barrierSolveBoolean=False;
                    tupPt_Barriers = getBarriersForRouteSolveWBarriers(inBarriers,whereClause_ht,Tonnage_class,Length_class,txtFile)
                    #we know this cannot be empty
                    barrierSolveBoolean = tupPt_Barriers[1]
                    
                    if barrierSolveBoolean:
                        pt_Barriers = tupPt_Barriers[0]
                        tupOutRoutesFC = RouteSolverWithBarriers(inNetworkDataset, pt_Barriers,inOrigins1,inDestinations1)
                    #need to have something different here
                        BRouteSolveBoolean =  tupOutRoutesFC[1]
                        if BRouteSolveBoolean:
                            outRoutesFC = tupOutRoutesFC[0]
                            countRoutes = arcpy.GetCount_management(outRoutesFC)
                            lengthWBarrierMiles = 0.0
                    
                            if int(str(countRoutes )) > 0:  # if there was an actual solve in this step
                                BarrierParamUpdateCounter = BarrierParamUpdateCounter + 1
                                lengthWBarrierMiles=getTotal_ImpedanceParamValue(outRoutesFC,imped_param1)
                                txtFile.write ( "lengthWBarrierMiles is " +str (math.ceil(lengthWBarrierMiles))+"\n")
                                print( "lengthWBarrierMiles is " +str (math.ceil(lengthWBarrierMiles))+"\n")
                                arcpy.AddMessage( "lengthWBarrierMiles is " +str (math.ceil(lengthWBarrierMiles))+"\n")
                                arcpy.management.Append(outRoutesFC, outRoutesFC22)
                                del outRoutesFC
                                #arcpy.DeleteFeatures_management ( outRoutesFC)
                                #   print "solve with barrier complete"
                                extraMiles = math.ceil (lengthWBarrierMiles- lengthNoBarrierMiles)
                                if extraMiles >= 2: # do something like 5 minutes?
                                    txtFile.write (" extra miles due to barrier is GT  3 miles and = "+ str (extraMiles)+ "\n")
                                    arcpy.AddMessage  (" extra miles due to barrier is GT  3 miles and = "+ str (extraMiles)+ "\n")
                                    arcpy.AddMessage ("-----Barrier solve completed for this OD pair--------")
                                    # need to multiply with frequency here
                                    
                                    
                                    UpdateBarrierCounterAndExtraMiles(inBarriers,extraMiles,frequ)#inBarriers2 are the intersecting barriers for shortest path
                                else:
                                    txtFile.write ("extraMiles is  LT 3 miles: Review Data "+ str(extraMiles)+ "  "+perIDStr+"\n")                                       
                                    #print "Time saved is negative: Review Data "+ str(TimeLost)+ "  "+perIDStr
                                pass
                            else:
                                print "route could not be found for this OD pair with barrier" +"," + str(perID_orig)+"\n"
                                arcpy.AddMessage ("route could not be found for this OD pair with barrier" +"," + str(perID_orig)+"\n")
                                txtFile.write ("route could not be found for this OD pair with barrier" +"," + str(perID_orig)+"\n")  
                                    ################################################################
                           
                                
                            
                        
                    del inOrigins1
                    del inDestinations1
                    del no_barr_lyr
                
            else:
                arcpy.AddMessage("Pre-req not met: There is no feature in the noBarrierSolve")
                #end of if myBoolean ==True
                
            inOrigins=rows1.next();
            inDestinations = rows2.next();
            arcpy.CalculateField_management(inBarriers,"DYN_UPDATE_FLAG","'N'","PYTHON_9.3")
                # for loop ends here
            
        print "Script completed successfully"
        
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
        #del rows1,rows2
        arcpy.CheckInExtension ("Network")
        txtFile.write ("----------------------------------------"+"\n")
        txtFile.write ("Completed")
        arcpy.AddMessage("----------------------------------------"+"\n")
        
        print("---elapsed time  %s seconds ---" % round(time.time() - start_time, 2))
        txtFile.write ("---elapsed time  %s seconds ---" % round(time.time() - start_time, 2))
        arcpy.AddMessage("---elapsed time  %s seconds ---" % round(time.time() - start_time, 2))
        
        txtFile.close()
        #round(time.time() - start_time, 2)
        ###############################################################################
        ########################################################################################################
        ###########################################################################################################


def getFieldValue (fc,fieldName):
    #input is only one feature in feature class
    SC= arcpy.SearchCursor (fc)
    
    for row in SC:
        fieldValue = row.getValue(fieldName)
        break
    del row, SC
    return fieldValue
################################################################

def getTotal_ImpedanceParamValue(outRoutesFC,imped_param):
    #input is only one feature in feature class
    SC= arcpy.SearchCursor (outRoutesFC)
    #fieldName = 'Total_DrivingTime'
    fieldName = imped_param
    for row in SC:
        total_ImpedanceParamValue = row.getValue(fieldName)
        break
    del row, SC
    return total_ImpedanceParamValue
    ###############################################################################################
def getBarriersToUpdateExtraMiles (Barriers, RoutesLayer,whereClause_ht,Weight_class,Leng_class,txtFile):
    
    print ("in function getBarriers")
    boolBarrierPresence = False;
    count2=0
    count1=0
    arcpy.MakeFeatureLayer_management(Barriers, "BarrierCopyLyr")        
    countt=arcpy.GetCount_management( "BarrierCopyLyr")
    print ( str(countt)  +  "is total bridges-potential barriers-- in project")
    print ("select posted bridges")
    arcpy.AddMessage("select posted bridges")
    #this also selects roundabouts in wellington,0096-R%
    arcpy.SelectLayerByAttribute_management("BarrierCopyLyr","NEW_SELECTION","Posted = 'P'")
    #select restricted bridges
    arcpy.AddMessage("wight class=   " + Weight_class   ) 
    
    if Weight_class.strip() == 'SUPERLOAD':
        arcpy.AddMessage (" SUPERLOAD -select restricted bridges")
        whereClauseR= '"Posted"='R''
        arcpy.SelectLayerByAttribute_management("BarrierCopyLyr","ADD_TO_SELECTION","Posted = 'R'")
    elif Weight_class.strip() == 'GT_60':
        print (" >60 T-select restricted bridges")
        whereClauseR= '"Posted"='R''
        arcpy.SelectLayerByAttribute_management("BarrierCopyLyr","ADD_TO_SELECTION","Posted = 'R'")
    else:
        arcpy.AddMessage("there are no restricted bridge barriers for this OD pair")
    #select vert clearance limited bridges
    arcpy. SelectLayerByAttribute_management("BarrierCopyLyr","ADD_TO_SELECTION",whereClause_ht)
    #select Roundabouts based on Length
    if Leng_class.strip() =='RNDABT_RESTR':
        #whereClauseX= '"Posted"='X''
        arcpy.AddMessage("selecting RNDABOUT")
        arcpy. SelectLayerByAttribute_management("BarrierCopyLyr","ADD_TO_SELECTION","Posted = 'X'")
    arcpy.SelectLayerByLocation_management("BarrierCopyLyr", "INTERSECT",RoutesLayer,"","SUBSET_SELECTION")
    intersected_barriersCnt= arcpy.GetCount_management("BarrierCopyLyr")
    if int(str(intersected_barriersCnt)) >0: # if there is an intersecting bridge with no barrier route solve
        
        print ("total number of shortest path barriers for this OD pair is  "+str(intersected_barriersCnt))
        txtFile.write("total number of shortest path barriers for this OD pair is  "+str(intersected_barriersCnt)+"\n")
        arcpy.AddMessage("total number of shortest path barriers for this OD pair is  "+str(intersected_barriersCnt)+"\n")
        boolBarrierPresence = True;
        # the statement below updates only for real obstructions for the specific OD pair
        arcpy.CalculateField_management("BarrierCopyLyr","DYN_UPDATE_FLAG","'Y'","PYTHON_9.3")
        return (boolBarrierPresence)
        
    else:
        boolBarrierPresence =False
        print ("There are no intersecting barriers with shortestPath for this OD pair-further steps not needed in this process")
        txtFile.write ("There are no intersecting barriers with shortestPath for this OD pair-further steps not needed in this process"+"\n")
        arcpy.AddMessage("There are no intersecting barriers with shortestPath for this OD pair-further steps not needed in this process"+"\n")
        return (boolBarrierPresence)
########################End function ###getBarriersToUpdateTimeLost#######################################
 #################################################################################################
def getBarriersForRouteSolveWBarriers (Barriers,whereClause_ht,Weight_class,Leng_class,txtFile):
    #returns barrier layer for the entire project area to feed in Route Solver
    
    #whereclause should have comparison with OD truck ht and barrier clearance ht
    #Also need to have the shortest path route as parameter
    #if there is no routes solved, this function is not called
    print ("in function getBarriers")
    boolBarrierPresence = False;
    count1=0
    count2=0
    arcpy.MakeFeatureLayer_management(Barriers, "BarrierCopyLyr")        
    count1=arcpy.GetCount_management( "BarrierCopyLyr")
    
       
    ## now add selection based on Vertical clearance and posted restricted
    #select posted bridges and Roundabout in Wellington '0096-R%
        
    print "select posted bridges"
       
    arcpy.SelectLayerByAttribute_management("BarrierCopyLyr","NEW_SELECTION","Posted = 'P'")
    
    if Weight_class.strip()=='SUPERLOAD':
        whereClauseR= '"Posted"='R''
        arcpy.SelectLayerByAttribute_management("BarrierCopyLyr","ADD_TO_SELECTION","Posted = 'R'")
    elif Weight_class.strip()=='GT_60':
        #whereClauseR= '"Posted"='R''
        arcpy.SelectLayerByAttribute_management("BarrierCopyLyr","ADD_TO_SELECTION","Posted = 'R'")
    else:
        pass
    arcpy. SelectLayerByAttribute_management("BarrierCopyLyr","ADD_TO_SELECTION",whereClause_ht)
    if Leng_class.strip() =='RNDABT_RESTR':
        #whereClauseX= '"Posted"='X''
        arcpy. SelectLayerByAttribute_management("BarrierCopyLyr","ADD_TO_SELECTION","Posted = 'X'")

    
    count2= int(str(arcpy.GetCount_management("BarrierCopyLyr")))#only selected features are counted
    
    if int(str(count2)) >0:
        print ("total number of barriers for this OD pair is  "+str(count2))
        arcpy.AddMessage("total number of barriers for this OD pair is  "+str(count2)+"\n")
        txtFile.write("total number of barriers for this OD pair is  "+str(count2)+"\n")
        boolBarrierPresence = True;
        return ("BarrierCopyLyr",boolBarrierPresence)
    else:
        boolBarrierPresence =False
        print ("There are no barriers for this OD pair, review data")
        arcpy.AddMessage("There are no barriers for this OD pair, review data"+"\n")
        txtFile.write("There are no barriers for this OD pair, review data"+"\n")
        return (0, boolBarrierPresence)    
########################################################################################             
def UpdateBarrierCounterAndExtraMiles(inBarriers,extraMiles,frequ):
    #these barriers are already layer
    # This function is called only when one OD pair successfully completes no barrier and with barrier route solutions-
    # Total_DrivingTime for the shortestPath and with barrier is needed. Only the barriers
    #that intersect the shortest path is going to be updated with TimeLost
    inBarriers1="inBarriers1"
    arcpy.MakeFeatureLayer_management(inBarriers,inBarriers1)    
    print "calculating bridge Counter field value"
    constant = frequ
    expression1 = "!Counter!+ "+str(constant)
    print ("expression1 is  "+ expression1)
    extraMiles=extraMiles*frequ

    expression2 = "!ExtraMiles!+ "+str(extraMiles)
    print "expression2 is "+ expression2
    
    whereClause = "DYN_UPDATE_FLAG='Y'"
    arcpy.SelectLayerByAttribute_management(inBarriers1,"NEW_SELECTION",whereClause)
    count1=arcpy.GetCount_management(inBarriers1)
    if int(str(count1)) >0:
        #print(" this many barriers will be updated with ExtraMiles Travelled  "+str(arcpy.GetCount_management(inBarriers1)))
        arcpy.AddMessage(" this many barriers will be updated with ExtraMiles Travelled  "+str(count1))
        arcpy.CalculateField_management(inBarriers1,"Counter",expression1,"PYTHON_9.3")
        arcpy.CalculateField_management(inBarriers1,"ExtraMiles",expression2,"PYTHON_9.3")
     
        arcpy.AddMessage( "returning after bridge updates")
        #return
    else:
        arcpy.AddMessage( "nothing to update, there must be an error")
        #return 
        ###############################################################################################
    #######################################################################################################



    
    ############################################################
    
###################################################
    
def RouteSolverWithBarriers(inNetworkDataset, inBarriers1,inOrigins1,inDestinations1):
    #returns the best route feature layer and a boolean to show if there are was any barrier for the current OD pair
    # if there is no barrier, then the current OD pair can be eliminated from further finding best routes
    print "in Route Solver"
    outNALayerName = "BestRoutes"
    impedanceAttribute = "Length"
    outRoutesFC = "outRoutes2"
    boolRouteSolved = False
    barrierSnapToler = '5 Meters'
    OD_SnapToler ='30 Meters'
    OD_uniq_fieldName = 'SER_NUM'
    #outLines ="TRUE_LINES_WITHOUT_MEASURES" 
   
    outRouteResultObject = arcpy.na.MakeRouteLayer(inNetworkDataset, outNALayerName,impedanceAttribute, accumulate_attribute_name=["DrivingTime"],restriction_attribute_name= ["Oneway"],hierarchy="NO_HIERARCHY")
    
    #Get the layer object from the result object. The route layer can now be
    #referenced using the layer object.
    outNALayer = outRouteResultObject.getOutput(0)

    #Get the names of all the sublayers within the route layer.
    subLayerNames = arcpy.na.GetNAClassNames(outNALayer)
    #Store the layer names that we will use later
        
    StopsLayerName = subLayerNames["Stops"]
    barrierLayerName= subLayerNames ["Barriers"]
    routesLayerName = subLayerNames["Routes"]
    
   
    countBarriers = arcpy.GetCount_management(inBarriers1)
    
    print("There are  "+  str(countBarriers) + " barriers for this OD pair")
    arcpy.na.AddLocations(outNALayer, barrierLayerName, inBarriers1, "", barrierSnapToler)
        
        
    #fieldMappings = "RouteName PRMT_ID #;"
    fieldMappings = arcpy.na.NAClassFieldMappings(outNALayer, StopsLayerName)
    fieldMappings["RouteName"].mappedFieldName = OD_uniq_fieldName
    
    arcpy.na.AddLocations(outNALayer, StopsLayerName, inOrigins1, fieldMappings,OD_SnapToler)
            
   
    arcpy.na.AddLocations(outNALayer, StopsLayerName, inDestinations1, fieldMappings,OD_SnapToler)
    #print "before try"
    try:

        #Solve the route layer.
        arcpy.na.Solve(outNALayer)
        boolRouteSolved = True
        print ("route with barrier solved")
    except:
        print "Route Solve Execution error occurred, for this OD pair"
        return (0, boolRouteSolved)
        #pass

    # Get the output Routes sublayer and save it to a feature class
    RoutesSubLayer = arcpy.mapping.ListLayers(outNALayer, routesLayerName)[0]
    arcpy.management.CopyFeatures(RoutesSubLayer, outRoutesFC)
       
           
    del inOrigins1,inDestinations1,outNALayer
    
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
    print whereClause
    return whereClause
##############################################################
main()
###############################################################
###################################################################









































