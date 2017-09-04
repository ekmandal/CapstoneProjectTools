#############################################################################################################
#Name: AnalyzeOSOWRoutes.py
#stand alone python script
#Requires ArcGIS
#This script was developed as part of  Capstone project -- ArcGIS Decision Support Tool for Planning Infrastructure Improvement--Penn State MGIS
#https://gis.e-education.psu.edu/sites/default/files/capstone/Mandal_report_596B_20170715.pdf
#####################################################
#This project involves the development of an ArcGIS Decision Support Tool Set
# to assist in planning the allocation of funding for transportation 
#infrastructure improvements. The tool set developed includes scripts to analyze and visualize Oversize/Overweight (OSOW) routing data available from the Permit System
#and to select candidate bridges  (acting as barriers to OSOW traffic) for improvement or replacement based on their spatial location in the
#context of OSOW traffic demand.This script AnalyzeOSOWRoutes.py is the first script of 4 scripts that are used in the project
########################################################################################################

#Description: Make OD pairs from OSOW shape file and State boundary polygon, and a buffer distance.
#Outputs the Origin_destination point featureclasses,
#OD Lines Frequency polygon and traffic classification as Interstate, Inbound, Outbound or Intrastate

############################################################################################################
# Two Inputs:  is geodatabase polyline featureclass of OSOW route, State boundary polygon
#OSOW route should have fields: LengthFt,HeightFt,Tonnage. A unique Id field will be helpful to join the resulting feature class to the routes

####################################################################################################
#
#ArcGIS version 10.5
#PythonWin 2.7.8 (default, Jun 30 2014, 16:03:49) [MSC v.1500 32 bit (Intel)] on win32.
## 
# Created by: Elsit Mandal
# 2017-06-20
#
#####################################
#Input Parameter1 : workspace FGDB
#Input parameter 2: OSOW Routes   input as one feature class
#Input Parameter3: State boundary poygon

#output is a ODlines with freq and classified as Inbound, outbound etc, ODLines drawn as polygon buffer with frequency
#The OD pairs derived are in WGS 84 coord system
#Sample input: "C:\\StateSystemOnly\\OD_Pairs.gdb" "OSOWRoutes" "State_boundary"
###############################################################################################################################
#
# Import system modules
import os
import arcpy
import datetime
import traceback
from arcpy import env
#
def main():
    try:
        #######################################
        print ("Process AnalyzeOSOWRoutes started"  +"**********************************************************")
        print datetime.datetime.now().time()

        start_time = time.time()
########################################################################### Inputs
       
        ws = arcpy.env.workspace = arcpy.GetParameterAsText(0)
                
        arcpy.env.overwriteOutput = True

        routes_fc= ws+"\\"+arcpy.GetParameterAsText(1)#This is OSOW routes
        
        State_boundary= ws+"\\"+arcpy.GetParameterAsText(2) # State Boundary polygon

        buffer_dist="-0.5 Miles"

##################################
        RoutesTbl= ws+"\\RoutesTbl"
        freq_tbl = ws+"\\freq_tbl"  # frequency analysis table with 2 decimal approximations of OD pairs, Tonnage_class,Length_class and HeightFt

        out_lines = ws + "\\ODLines" # these are lines connecting 2 decimal OD points

        Origins = ws +"\\Origins_2DEC_all"
        Destinations = ws +"\\Destinations_2DEC_all"

        outlines_prj= ws +"\\ODLines_prj"


        outlines_buff= ws +"\\ODLines_buff"

        #https://developers.arcgis.com/net/10-2/desktop/guide/projected-coordinate-systems-part-1.htm
        #https://developers.arcgis.com/net/10-2/desktop/guide/geographic-coordinate-systems.htm

        ODLineFreqBuffSpatRefFactCode= 3419 #Spatial reference Factory Code for state plane KS north FT_US
        SpatialRef_WGS84=4326 #Spatial reference Factory Code for WGS84

       
        #The value below is multiplied by frequency to get buff distance of ODLine frequency for visulaization in map,

        #appropriate value depends on ODLine frequency
        ODLINEFreqBuffDistMultiplier=10 #appropriate value depends on projection and expected freq
        
        # significant_freq is the frequency above which the OD pairs are assigned new xy coordinates to create
        #point feature class original XY coordinatesfrom one of the routes so that snapping Tolerance are not too large
        signi_freq =5
        Origins_subset=ws+"\\Origins_freqGEsigni_freq" # 
        Destinations_subset = ws+"\\Desinations_freqGEsigni_freq"
    
##############################################################################################################
        arcpy.Describe (routes_fc)
        spatial_ref = arcpy.Describe(routes_fc).spatialReference
        print spatial_ref.factoryCode
        
    
        #############################copy feature if needs to project to WGS84######################
        routes_fc_copy = "routes_fc_copy"  # this is copied, so original routes is not altered
        arcpy.CopyFeatures_management(routes_fc, routes_fc_copy)
        
        # if projection is not WGS 84, reproject
    
        targetSR = arcpy.SpatialReference()
        targetSR.factoryCode = 4326
        targetSR.create()
        spatial_ref_factory_code= spatial_ref.factoryCode
    
        if spatial_ref_factory_code != SpatialRef_WGS84:
        
            print "projecting to WGS84"
            #routes_fc_copy= "routes_fc_copy"  # this is for keeping the WGS84 route featureclass
            arcpy.Project_management(routes_fc, routes_fc_copy, targetSR)  
        
        else: #here assumed to be already in WGS84
            #routes_fc_copy=routes_fc_copy #point to copied route fc
            print "route not reprojected:"
        
        # create a polygon within State Boundary polygon with buffere distance to determine inbound, outbound traffic based on spatial location of  origin destination points    
        State_boundary_buffDistMile_in= "State_boundary_buffDistMile_in"
        arcpy.Buffer_analysis(in_features=State_boundary, out_feature_class=State_boundary_buffDistMile_in, buffer_distance_or_field= buffer_dist, line_side="FULL", line_end_type="ROUND", dissolve_option="NONE", dissolve_field="", method="PLANAR")
        
        # Add Length_class and Tonnage_class
        fieldName5 = "Tonnage_class"
        fieldName6 = "Length_class"
        arcpy.AddField_management(routes_fc_copy, fieldName5, "TEXT","","",13)
        arcpy.AddField_management(routes_fc_copy, fieldName6, "TEXT","","",15)
        routes_lyr = "routes_lyr"
        
        arcpy.MakeFeatureLayer_management(routes_fc_copy,routes_lyr)
        arcpy.CalculateField_management(routes_lyr, "Tonnage_class", "'GT_60'","PYTHON_9.3")# initialize all values
        arcpy.SelectLayerByAttribute_management(routes_lyr,"NEW_SELECTION","Tonnage <= 60")
        selectedCount= int(str(arcpy.GetCount_management(routes_lyr))) # only selected features ae counted
        if  selectedCount > 0:
            arcpy.CalculateField_management(routes_lyr, "Tonnage_class", "'LESS_OREQ_60'","PYTHON_9.3")
                   
        arcpy.SelectLayerByAttribute_management(routes_lyr,"NEW_SELECTION","Tonnage >75")               
        selectedCount= int(str(arcpy.GetCount_management(routes_lyr))) # only selected features ae counted
        if  selectedCount >0:                       
            arcpy.CalculateField_management(routes_lyr, "Tonnage_class", "'SUPERLOAD'","PYTHON_9.3")


        arcpy.SelectLayerByAttribute_management(routes_lyr,"CLEAR_SELECTION")      
        arcpy.CalculateField_management(routes_lyr, "Length_class", "'NO_RNDABT_RESTR'","PYTHON_9.3")  #initialize all values
        arcpy.SelectLayerByAttribute_management(routes_lyr,"NEW_SELECTION","LengthFt > 85")# roundabout restrictions if length >85 feet
        selectedCount= int(str(arcpy.GetCount_management(routes_lyr)))
        if  selectedCount >0:                       
        
            arcpy.CalculateField_management(routes_lyr, "Length_class", "'RNDABT_RESTR'","PYTHON_9.3")
        arcpy.SelectLayerByAttribute_management(routes_lyr,"CLEAR_SELECTION")

        del routes_lyr # not needed anymore
        fieldName1 = "X_INI"
        fieldName2 = "Y_INI"
        fieldName3 = "X_FIN"
        fieldName4 = "Y_FIN"
        #
    


        arcpy.AddField_management(routes_fc_copy, fieldName1, "DOUBLE")
        arcpy.AddField_management(routes_fc_copy, fieldName2, "DOUBLE")
        arcpy.AddField_management(routes_fc_copy, fieldName3, "DOUBLE")
        arcpy.AddField_management(routes_fc_copy, fieldName4, "DOUBLE")

    
        #     Calculate XY
        arcpy.CalculateField_management(routes_fc_copy, fieldName1,"!shape.firstpoint.x!","PYTHON_9.3")
        arcpy.CalculateField_management(routes_fc_copy, fieldName2,"!shape.firstpoint.y!","PYTHON_9.3")
        arcpy.CalculateField_management(routes_fc_copy, fieldName3,"!shape.lastpoint.x!","PYTHON_9.3")
        arcpy.CalculateField_management(routes_fc_copy, fieldName4,"!shape.lastpoint.y!","PYTHON_9.3")
        # Add fields
    
        arcpy.AddField_management(routes_fc_copy, "X1_2DEC", "DOUBLE")
        arcpy.AddField_management(routes_fc_copy, "Y1_2DEC", "DOUBLE")
        arcpy.AddField_management(routes_fc_copy, "X2_2DEC", "DOUBLE")
        arcpy.AddField_management(routes_fc_copy, "Y2_2DEC", "DOUBLE")
   
        arcpy.AddField_management(routes_fc_copy, "unique_field", "TEXT",field_length=100)
        # Calculate XY
        arcpy.CalculateField_management(routes_fc_copy, "X1_2DEC","round(!X_INI!,2)","PYTHON_9.3")
        arcpy.CalculateField_management(routes_fc_copy, "Y1_2DEC","round(!Y_INI!,2)","PYTHON_9.3")
        arcpy.CalculateField_management(routes_fc_copy, "X2_2DEC","round(!X_FIN!,2)","PYTHON_9.3")
        arcpy.CalculateField_management(routes_fc_copy, "Y2_2DEC","round(!Y_FIN!,2)","PYTHON_9.3")
        arcpy.CalculateField_management(routes_fc_copy, "HeightFt","round(!HeightFt!,2)","PYTHON_9.3") # HeightFt is re-calculated because, if there are trailing digits in this field, it causes problem in a unique_id text field which includes HeightFt
    
    
        expression2 = 'str(!X1_2DEC!)+ ","+ str(!Y1_2DEC!)+","+str(!X2_2DEC!)+","+str(!Y2_2DEC!)+","+!Tonnage_class!+","+!Length_class!+","+str(!HeightFt!)'
    
    
        arcpy.CalculateField_management(routes_fc_copy, "unique_field",expression2,"PYTHON_9.3")
        #create frequency table
   
    
        arcpy.Frequency_analysis(routes_fc_copy,freq_tbl,frequency_fields = "X1_2DEC;Y1_2DEC;X2_2DEC;Y2_2DEC;Tonnage_class;Length_class;HeightFt")
    
        arcpy.AddField_management(freq_tbl, "unique_field", "TEXT",field_length=100)
        arcpy.CalculateField_management(freq_tbl, "unique_field",expression2,"PYTHON_9.3") 
        ########update freq_tbl with SER_NUM##########################################
        arcpy.AddField_management(freq_tbl, "SER_NUM", "LONG")
    
        fields_in_cursor= ['SER_NUM','unique_field','FREQUENCY']
        xx='ORDER BY FREQUENCY DESC'
        sql_clause =(None, xx)
        #arcpy.AddIndex_management(freq_tbl,"FREQUENCY;unique_field","FREQ_IN;INX1")
        cur = arcpy.da.UpdateCursor(freq_tbl,  fields_in_cursor,sql_clause=(None,xx))
    
    
        i=1
        for row in cur:
            row[0] = i
            i += 1
            cur.updateRow(row)

        del cur, row
        print("--SER_NUM  in FEQ table -elapsed time  %s seconds ---" % round(time.time() - start_time, 2))

        #####################################################################
        arcpy.MakeTableView_management(routes_fc_copy, RoutesTbl)
        arcpy.AddIndex_management(RoutesTbl,"unique_field","INX","UNIQUE","ASCENDING")
        arcpy.AddIndex_management(freq_tbl,"SER_NUM","INX2","UNIQUE","ASCENDING")
        arcpy.JoinField_management(RoutesTbl,"unique_field",freq_tbl,"unique_field")#this join has to be based on unique field
        #arcpy.CopyRows_management(RoutesTbl,RoutesTbl1)
        #arcpy.RemoveIndex_management(RoutesTbl,"INX")
        #arcpy.RemoveIndex_management(freq_tbl,"INX")
        arcpy.AddIndex_management(RoutesTbl,"SER_NUM","INX2","UNIQUE","ASCENDING")
        ####################################################
                              
   
        # create Origin Points and Destination Points

        #XY To Line using 2 decimal approx
        arcpy.XYToLine_management(freq_tbl,out_lines,"X1_2DEC","Y1_2DEC","X2_2DEC","Y2_2DEC","GEODESIC","SER_NUM",targetSR)
        # make point layers of origins and Destinations
    
        #################################################################################
        # make origins and destinations feature classes with 2 decimal approximations
        ##################################################################################
        O_layer="O_layer" #origin layer
      
        arcpy.MakeXYEventLayer_management (freq_tbl, "X1_2DEC", "Y1_2DEC", O_layer, targetSR)
        arcpy.CopyFeatures_management(O_layer,Origins)
        del O_layer
        D_layer="D_layer" #destination layer
    
        arcpy.MakeXYEventLayer_management (freq_tbl, "X2_2DEC", "Y2_2DEC", D_layer, targetSR)
        arcpy.CopyFeatures_management(D_layer,Destinations)
        del D_layer
        print("---Origin Dest  apprx fc made  elapsed time  %s seconds ---" % round(time.time() - start_time, 2))
        ##########################################################################################################
        #classify the OD pairs as INTERSTATE,INTRASTATE,INBOUND,OUTBOUND: this is done with OD 2 DEC approximations
        #classify Origins, create a separate feature class
        Origins_class= "Origins_class"
        arcpy.CopyFeatures_management(Origins, Origins_class)
        arcpy.AddField_management(Origins_class, "CLASSIFY", "TEXT","","", 50)
    
        polyLayer= arcpy.MakeFeatureLayer_management(State_boundary_buffDistMile_in)
        Origins_lyr= arcpy.MakeFeatureLayer_management(Origins_class)
        arcpy.AddSpatialIndex_management(Origins_lyr)
    
    
        arcpy.SelectLayerByLocation_management(Origins_lyr,"COMPLETELY_WITHIN",polyLayer, "", "NEW_SELECTION","NOT_INVERT")
        arcpy.CalculateField_management(Origins_lyr, "CLASSIFY", '"""ORIGIN_WITHIN"""',"PYTHON_9.3")
        #classify Destinations
        Destinations_class= "Destinations_class"
        arcpy.CopyFeatures_management(Destinations, Destinations_class)
        arcpy.AddField_management(Destinations_class, "CLASSIFY", "TEXT","","", 50)
        Destinations_lyr= arcpy.MakeFeatureLayer_management(Destinations_class)
        arcpy.AddSpatialIndex_management(Destinations_lyr)
        arcpy.SelectLayerByLocation_management(Destinations_lyr,"COMPLETELY_WITHIN",polyLayer, "", "NEW_SELECTION","NOT_INVERT")
        arcpy.CalculateField_management(Destinations_lyr, "CLASSIFY", '"""DESTINATION_WITHIN"""',"PYTHON_9.3")
        #clear selected features
        arcpy.SelectLayerByAttribute_management(Origins_lyr,"CLEAR_SELECTION")
        arcpy.SelectLayerByAttribute_management(Destinations_lyr,"CLEAR_SELECTION")
        #####################################################################
        #JOIN ORIGIN and DESTINATION TO COMPLETE THE CLASSIFICATION
        arcpy.AddIndex_management(Origins_class,"SER_NUM","SER_INDX")
        arcpy.AddIndex_management(Destinations_class,"SER_NUM","SER_INDX")
        arcpy.JoinField_management(Origins_class,"SER_NUM",Destinations_class,"SER_NUM")
        arcpy.AddField_management(Origins_class, "TRAFFIC_CLASS", "TEXT","","", 50)
        #OUTBOUND
        arcpy.SelectLayerByAttribute_management(Origins_lyr, "NEW_SELECTION","Origins_class.CLASSIFY = 'ORIGIN_WITHIN' AND Origins_class.CLASSIFY_1 IS NULL")
        arcpy.CalculateField_management(Origins_lyr, "TRAFFIC_CLASS", '"""OUTBOUND"""',"PYTHON_9.3")
        #INBOUND
        arcpy.SelectLayerByAttribute_management(Origins_lyr, "NEW_SELECTION","Origins_class.CLASSIFY IS NULL AND Origins_class.CLASSIFY_1= 'DESTINATION_WITHIN'")
        arcpy.CalculateField_management(Origins_lyr, "TRAFFIC_CLASS", '"""INBOUND"""',"PYTHON_9.3")
        #INTRASTATE
        arcpy.SelectLayerByAttribute_management(Origins_lyr, "NEW_SELECTION","Origins_class.CLASSIFY='ORIGIN_WITHIN' AND Origins_class.CLASSIFY_1= 'DESTINATION_WITHIN'")
        arcpy.CalculateField_management(Origins_lyr, "TRAFFIC_CLASS", '"""INTRASTATE"""',"PYTHON_9.3")
        #INTERSTATE: All remaining is INTERSTATE
        arcpy.SelectLayerByAttribute_management(Origins_lyr, "NEW_SELECTION","Origins_class.TRAFFIC_CLASS IS NULL")
        arcpy.CalculateField_management(Origins_lyr, "TRAFFIC_CLASS", '"""INTERSTATE"""',"PYTHON_9.3")
        arcpy.SelectLayerByAttribute_management(Origins_lyr,"CLEAR_SELECTION")

        print("traffic class done  ---elapsed time  %s seconds ---" % round(time.time() - start_time, 2))
        # JOIN this Origin_class with OD lines
        arcpy.AddIndex_management(out_lines,"SER_NUM","SER_INX","UNIQUE")
        arcpy.JoinField_management(out_lines,"SER_NUM",Origins_class,"SER_NUM")
        arcpy.AddField_management(out_lines,"BUFF_DIST","DOUBLE")
        ##############################################
   
        projSR = arcpy.SpatialReference()
        projSR.factoryCode = ODLineFreqBuffSpatRefFactCode 
        projSR.create()
        #############################################################3
    
        arcpy.Project_management(out_lines, outlines_prj, projSR)
        #print ODLINEFreqBuffDistMultiplier
        expression1="!FREQUENCY!"+"*"+str(ODLINEFreqBuffDistMultiplier)
        arcpy.CalculateField_management(outlines_prj, "BUFF_DIST", expression1,"PYTHON_9.3")# this is hard coded
    
        arcpy.Buffer_analysis(outlines_prj, outlines_buff, "BUFF_DIST")
        #buff_lyr = "c:\\Student\\buff_lyr"
        #arcpy.ApplySymbologyFromLayer_management(outlines_buff,buff_lyr)
        # Get subset of Origins and Destinations with one of original xy coord. in each frquecy set, where freq > significant frequency to be used in further analysis
        #Routes_tbl has X_INI,Y_INI,X_FIN,Y_FIN
        print("---elapsed time  %s seconds ---" % round(time.time() - start_time, 2))
        whereClauseFreq = "FREQUENCY" +">="+str(signi_freq)
        freq_tbl_select="freq_tbl_select"
        arcpy.MakeTableView_management(freq_tbl,"freq_tbl_view",whereClauseFreq)
        arcpy.CopyRows_management("freq_tbl_view",freq_tbl_select)
        Origins_1 = UpdateCoordinates(freq_tbl_select, RoutesTbl,1,targetSR)
        arcpy.CopyFeatures_management(Origins_1,Origins_subset)
        Destinations_1 = UpdateCoordinates(freq_tbl_select, RoutesTbl, 2,targetSR)
        arcpy.CopyFeatures_management(Destinations_1,Destinations_subset)
        


        #print ("program completed")
    except:
        print "An error Occurred"
        
        tb=sys.exc_info() [2]
        tbinfo =traceback.format_tb(tb)[0]
        pymsg= "PYTHON ERRORS:\nTracebakinfo:\n"+tbinfo+"\nErrorInfo:\n"+str(sys.exc_type)+":"+str(sys.exc_value)+"\n"
        arcpy.AddError (pymsg)
        msgs= "Arcpy ERRORS: \n"+arcpy.GetMessages(2)+"\n"
        arcpy.AddError (msgs)
        print pymsg +"\n"
        print msgs
        
    finally:
        #arcpy.Delete_management("in_memory")
        arcpy.Delete_management(Origins_class)
        arcpy.Delete_management(Destinations_class)
        arcpy.Delete_management(State_boundary_buffDistMile_in)
        #https://geonet.esri.com/thread/35455
        
        del Origins_lyr,Destinations_lyr
        print "program completed"
        print("---elapsed time  %s seconds ---" % round(time.time() - start_time, 2))
#########################################################################
def UpdateCoordinates(frequ_tbl, routes_tbl,flag_num,targetSR):
    #returns points_layer     
    if flag_num ==1: #to make origins feature
        arcpy.AddField_management(frequ_tbl, "new_x1", "DOUBLE")
        arcpy.AddField_management(frequ_tbl, "new_y1", "DOUBLE")
        fields_in_cursor1 =["new_x1","new_y1","SER_NUM"]
        fields_in_cursor2=["X_INI","Y_INI","SER_NUM"]
    if flag_num==2:# to make destinations feature
        arcpy.AddField_management(frequ_tbl, "new_x2", "DOUBLE")
        arcpy.AddField_management(frequ_tbl, "new_y2", "DOUBLE")
        fields_in_cursor1 =["new_x2","new_y2","SER_NUM"]
        fields_in_cursor2=["X_FIN","Y_FIN","SER_NUM"]
        
    cur1= arcpy.da.UpdateCursor(frequ_tbl,fields_in_cursor1,sql_clause=(None, 'ORDER BY SER_NUM ASC')) 
    
    for row1 in cur1: #to update Origins with new x,y 
        
        uniq_id = row1[2]#SER_NUM field is at position 2
        #print uniq_id
        where_clause2=BuildWhereClause(routes_tbl,"SER_NUM",uniq_id)
        cur2 = arcpy.da.SearchCursor(routes_tbl, fields_in_cursor2, where_clause2) # has original x,y coords
                    
        for row2 in cur2: # get x and Y from Routes Begin point coord.
            x1= row2[0]#cur2 poistion 0 is X_INI or X_FIN dependng on flag_num value
            y1=row2[1] #cur2 poistion 1is Y_INI or Y_FIN dependng on flag_num value
            del row2
            break
        del cur2
        row1[0]=x1  #cur1 field at position 0, which is new_x
        row1[1]=y1 #cur1 field at position 1 which is new_y
        cur1.updateRow(row1)
    del cur1,row1
    
    points_layer="pts_layer"
    
    if flag_num==1: 
        arcpy.MakeXYEventLayer_management (frequ_tbl, "new_x1", "new_y1", points_layer, targetSR)
    if flag_num==2:
        arcpy.MakeXYEventLayer_management (frequ_tbl, "new_x2", "new_y2", points_layer, targetSR)    
    
    return points_layer
###########################################################################
def BuildWhereClause(table, field, value):
    #https://gis.stackexchange.com/questions/27457/including-variable-in-where-clause-of-arcpy-select-analysis
    
    # Add field delimiters
    fieldDelimited = arcpy.AddFieldDelimiters(table, field)
    # get field type
    fieldType = arcpy.ListFields(table, field)[0].type
    
    
    # Add single-quotes for string field values
    if str(fieldType) == 'String':
        expression = "'%s'" % value
    
    whereClause = "%s = %s" % (fieldDelimited, value)
    #print whereClause
    return whereClause
#########################################################
main()
####################################################################
