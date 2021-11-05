#ImageJ-Python Macro
#MULTIPOSITION_MULTIMEASURE_UNIT-01 TEST-TYPE
#takes 384 well plate images and neuron position .txt files and performs 
#multiROI measurement of fluroescence - outputs measurements as neuron trace .txt files
#Eric Larsen 2021

#IMAGEJ ONLY
from ij import IJ
from ij.plugin.frame import RoiManager
from ij.gui import Roi
#Import Python Dependencies
#note: jython only supports default python libraries
import os
import time
import re

#Define tracking box size - used by MULTI_ROI_MEASURE() function
ROI_height=16
ROI_width=16
###

#Macro Performance Code
def main():
	#IMAGEJ SPECIFIC:
	#Ask user to select the folder of organized well images - ported from IJM code
	ImageDir = IJ.getDir("Choose Folder of Well Images")
	#Ask user for folder of neuron position txt files
	PositionDir = IJ.getDir("Choose Folder of Position Files")
	###

	#Use LoadPositionFile() to read all the NeuronPos##.txt files in PositionDir
	#Populates POSITION_LOOK_UP- a dictionary with Well number as the key
	#when the well number is entered the result is a dictionary of animal positions
	#(with support for multiple positions per animal)
	POSITION_LOOK_UP={}
	for foldername, subfolder, filename in os.walk(PositionDir):
		for CHECK_FILE in filename:
			if CHECK_FILE.find('.txt')!=0:
				THIS_FILE_ADDRESS = foldername + CHECK_FILE
				(THIS_WELL_ID,THIS_WELL_POS,NULL_TEST)=LoadPositionFile(THIS_FILE_ADDRESS)
			if NULL_TEST==0:
				NEW_ENTRY = {THIS_WELL_ID:THIS_WELL_POS}
				POSITION_LOOK_UP.update(NEW_ENTRY)
			if NULL_TEST==1:
				NULL_ENTRY = {THIS_WELL_ID:0}
				POSITION_LOOK_UP.update(NULL_ENTRY)
	#Working 10/29
	###

	#create folder to save NeuronTraces - use time!
	CURRENT_TIME = time.gmtime()
	#isolate the GMT date, hour, and minute
	DATE_ARRAY = [CURRENT_TIME.tm_year,CURRENT_TIME.tm_mon,CURRENT_TIME.tm_mday,CURRENT_TIME.tm_hour,CURRENT_TIME.tm_min]
	#build folder name
	#make the folder at the experiment 'root' - in the same folder as ImageDir
	ImageDir_end_search=ImageDir.rfind('\\')
	ImageDir_root_search=ImageDir.rfind('\\',0,ImageDir_end_search)
	ImageDir_root_string=ImageDir[0:ImageDir_root_search+1]
	#No f strings in jython(?)
	Trace_Folder_Name='NeuronTraces_'+str(DATE_ARRAY[0])+str(DATE_ARRAY[1])+str(DATE_ARRAY[2])+'_'+str(DATE_ARRAY[3])+str(DATE_ARRAY[4])
	Trace_Folder_Address=ImageDir_root_string+Trace_Folder_Name
	#make NeuronTrace folder
	os.makedirs(Trace_Folder_Address)
	###

	#loop through all video files to produce measurements:
	#regex for isolating video properties
	VIDEO_INDEX=re.compile(r'_well(\d*)cycle(\d*)mov(\d*).tif')
	#begin looping though all well folders - save one txt file per animal per video into Trace_Folder_Address
	for foldername, subfolder, file_name in os.walk(ImageDir):
		#get well INT from foldername string
		well_folder_search=foldername.rfind('\\')
		well_folder=foldername[well_folder_search+1::]
		#avoid reading the root (a non int '' string)
		if bool(well_folder) is not False:
			well_number = int(well_folder)
			#use POSITION_LOOK_UP to check IF this well is NULL
			WELL_POSITIONS = POSITION_LOOK_UP[well_number]
			#IF NOT null - process all videos
			if WELL_POSITIONS!=0:
				number_of_files = len(file_name)
				#loop through all files in the specific well folder
				for N in range(0,number_of_files):
					THIS_FILE = file_name[N]
					#confirm this is a TIF file and not thumbs.db or something else
					THIS_VIDEO_INDEX=VIDEO_INDEX.findall(THIS_FILE)
					if bool(THIS_VIDEO_INDEX) is not False:
						#THIS_VIDEO_INDEX produced by RE is nested lists - get the Well, Cycle, and Trial as INTs
						[WELL_ID,CYCLE_ID,TRIAL_ID]=[int(THIS_VIDEO_INDEX[0][0]),int(THIS_VIDEO_INDEX[0][1]),int(THIS_VIDEO_INDEX[0][2])]
						#load and measure image
						if WELL_ID==well_number:
							TIF_FILE_ADDRESS = foldername+'\\'+THIS_FILE
							print('Measuring Well {} Cycle {} Trial {}'.format(WELL_ID,CYCLE_ID,TRIAL_ID))
							#perform measurements for this video and save measurements to file (see function code)
							(ROI_MEASUREMENTS,ROI_DB) = MULTI_ROI_MEASURE(TIF_FILE_ADDRESS,POSITION_LOOK_UP,WELL_ID,CYCLE_ID)
							ROI_MEASUREMENTS.show('Results')
							PROCESS_AND_SAVE_MEASUREMENTS(ROI_MEASUREMENTS,ROI_DB,WELL_ID,CYCLE_ID,THIS_FILE,Trace_Folder_Address)
			#IF well is null
			if WELL_POSITIONS==0:
				#report null
				print('Null Well')
		#Clear all windows for next TIF file - disabed for debug
		IJ.run("Clear Results");
		IJ.run("Close All");
#End of main()
###

#Function Code:
#Read a position file into a dictionary variable
def LoadPositionFile(file_address):
	#read file to string
	POSITION_FILE = open(file_address)
	RAW_POS_TXT = POSITION_FILE.readlines()
	POSITION_FILE.close()
	#create POSITION_DICTIONARY
	VERBOSE_INPUT=0
	POSITION_DICTIONARY = {}
	IS_NULL = 0;
	#parse string RAW_POS_TXT
	for N,S in enumerate(RAW_POS_TXT):
		#N is the line number
		#S is the line string
		#isolate integers from the line - working 10/29/21
		#FROM blog.finxter.com/how-to-extract-numbers-from-a-string-in-python/
		LINE_VALUES = [int(c) for c in str.split(S) if c.isdigit()]
		#use size of LINE_VALUES to determine type of input
		#LINE_VALUES(3) is the Animal ID - use this for dictionary build
		LINE_SIZE = len(LINE_VALUES)
		#oldest format (no video specifics)
		if LINE_SIZE==4:
			WELL_ID = LINE_VALUES[0]
			ANIMAL_X = LINE_VALUES[1]
			ANIMAL_Y = LINE_VALUES[2]
			ANIMAL_ID = LINE_VALUES[3]
			#revised format - specific cycle used for selection
		if LINE_SIZE==5:
			WELL_ID = LINE_VALUES[0]
			ANIMAL_X = LINE_VALUES[1]
			ANIMAL_Y = LINE_VALUES[2]
			ANIMAL_ID = LINE_VALUES[3]
			ANIMAL_CYCLE = LINE_VALUES[4]
			VERBOSE_INPUT=1
			#verbose format - specifies cycle, trial, and frame
			#For now only cycle is used for multipositions        
		if LINE_SIZE==7:
			WELL_ID = LINE_VALUES[0]
			ANIMAL_X = LINE_VALUES[1]
			ANIMAL_Y = LINE_VALUES[2]
			ANIMAL_ID = LINE_VALUES[3]
			ANIMAL_CYCLE = LINE_VALUES[4]
			ANIMAL_TRIAL = LINE_VALUES[5]
			ANIMAL_FRAME = LINE_VALUES[6]
			VERBOSE_INPUT=1
			#Detect null
		if N==1 and sum(LINE_VALUES)==0:
			IS_NULL=1
		else:
			try:
				#animal is already recorded - update positions
				ANIMAL_POSITIONS = POSITION_DICTIONARY[ANIMAL_ID]
				if VERBOSE_INPUT==1:
					ADDITIONAL_POSITION = [ANIMAL_X,ANIMAL_Y,ANIMAL_CYCLE]
				if VERBOSE_INPUT==0:
					ADDITIONAL_POSITION = [ANIMAL_X,ANIMAL_Y]
				ANIMAL_POSITIONS.append(ADDITIONAL_POSITION)
				UPDATED_ENTRY = {ANIMAL_ID:ANIMAL_POSITIONS}
				POSITION_DICTIONARY.update(UPDATED_ENTRY)
			except KeyError:
				#new Animal - create dictionary entry
				if VERBOSE_INPUT==1:
					INITIAL_ANIMAL_POSITION = [ANIMAL_X,ANIMAL_Y,ANIMAL_CYCLE]
				if VERBOSE_INPUT==0:
					INITIAL_ANIMAL_POSITION = [ANIMAL_X,ANIMAL_Y]
				ANIMAL_ENTRY = {ANIMAL_ID:[INITIAL_ANIMAL_POSITION]}
				POSITION_DICTIONARY.update(ANIMAL_ENTRY)
	return WELL_ID,POSITION_DICTIONARY,IS_NULL
#Function working 10/29/21
#tested with multicycle input 11/3 - working
###

#Function that will build an ROI for a specific video using the position dictionary
#ROI_width & ROI_height are defined at the beginng of this macro
def MULTI_ROI_MEASURE(FULL_IMAGE_FILE,POSITION_DICTIONARY,WELL,CYCLE):
	#Read the Position_Dictionary for this well
	ALL_ANIMAL_POSITIONS = POSITION_DICTIONARY[WELL]
	#Load Image
	TIF_IMAGE = IJ.openImage(FULL_IMAGE_FILE)
	#Start Region Manager
	REGION_MANAGER = RoiManager.getInstance()
	if not REGION_MANAGER:
		REGION_MANAGER = RoiManager()
	REGION_MANAGER.reset()
	#Loop through all animals and build ROIs
	#The X,Y coordinates are the center of a rectangle, 
	#while Roi() accepts X,Y of the left hand corner
	for N,S in enumerate(ALL_ANIMAL_POSITIONS):
		ANIMAL_POSITION = ALL_ANIMAL_POSITIONS[N+1]
		if len(ANIMAL_POSITION)==1:
			#Only one position recorded for this animal - use in all videos
			CORNER_X = ANIMAL_POSITION[0][0]-(ROI_width/2)
			CORNER_Y = ANIMAL_POSITION[0][1]-(ROI_height/2)
		if len(ANIMAL_POSITION)>>1:
			#More than one position recorded for this animal - which one to use?
			TARGET_CYCLE=CYCLE
			CYCLE_INDEX=[]
			#get index of which positions are available
			for P,S in enumerate(ANIMAL_POSITION):
				CYCLE_INDEX.append(ANIMAL_POSITION[P][2])
			#Is TARGET_CYCLE in CYCLE_INDEX?
			if TARGET_CYCLE in CYCLE_INDEX:
				#Get Cycle Specific Position for ROI
				INDEX_ADDRESS=CYCLE_INDEX.index(TARGET_CYCLE)
				CORNER_X = ANIMAL_POSITION[INDEX_ADDRESS][0]-(ROI_width/2)
				CORNER_Y = ANIMAL_POSITION[INDEX_ADDRESS][1]-(ROI_height/2)
			else:
				#Which Cycle is closest?
				CHOSEN_CYCLE=0
				while CHOSEN_CYCLE==0:
					#first try cycle before
					if TARGET_CYCLE-1 in CYCLE_INDEX:
						CHOSEN_CYCLE = TARGET_CYCLE-1
					#next the cycle after
					elif TARGET_CYCLE+1 in CYCLE_INDEX:
						CHOSEN_CYCLE = TARGET_CYCLE+1
					#thirdly try 2 cycles before
					elif TARGET_CYCLE-2 in CYCLE_INDEX:
						CHOSEN_CYCLE = TARGET_CYCLE-2
					#fourth try 2 cycles after
					elif TARGET_CYCLE+2 in CYCLE_INDEX:
						CHOSEN_CYCLE = TARGET_CYCLE+2
					#fifth try 3 cycles before
					elif TARGET_CYCLE-3 in CYCLE_INDEX:
						CHOSEN_CYCLE = TARGET_CYCLE-2
					#sixth try 3 cycles after
					elif TARGET_CYCLE+3 in CYCLE_INDEX:
						CHOSEN_CYCLE = TARGET_CYCLE+2
					elif TARGET_CYCLE not in CYCLE_INDEX:
						#give up
						CHOSEN_CYCLE=8000
				#Get Cycle ESTIMATE Position for ROI
				try:
					INDEX_ADDRESS=CYCLE_INDEX.index(CHOSEN_CYCLE)
					CORNER_X = ANIMAL_POSITION[INDEX_ADDRESS][0]-(ROI_width/2)
					CORNER_Y = ANIMAL_POSITION[INDEX_ADDRESS][1]-(ROI_height/2)
				except KeyError:
					print('Failed to find best fit position for Animal {}'.format(N))
		#Build region of interest rectangle for this animal
		THIS_ANIMAL_REGION = Roi(CORNER_X,CORNER_Y,ROI_height,ROI_width)
		REGION_MANAGER.addRoi(THIS_ANIMAL_REGION)
	#with ROIs produced for all animals, select them all and perform multiMeasure
	REGION_MANAGER.runCommand(TIF_IMAGE, 'Select All')
	MEASUREMENTS = REGION_MANAGER.multiMeasure(TIF_IMAGE)
	#close image
	TIF_IMAGE.close()
	return MEASUREMENTS,REGION_MANAGER
###
#11/5 test - RawIntDen output in MEASUREMENTS.show('Results') matches saved text output from existing IJM

#function for saving measurements to a text file
def PROCESS_AND_SAVE_MEASUREMENTS(ROI_MEASUREMENTS,REGION_MANAGER,WELL,CYCLE,IMAGE_FILE_NAME,OUTPUT_FOLDER):
	#Establish constants
	NUMBER_OF_FRAMES = ROI_MEASUREMENTS.size()
	HEADER='well,cycle,animal,frame,x,y,sqarea,sqintdens,bgmedian,sqintsub'
	#loop through all animals in this video
	for ANIMAL,ROI in enumerate(REGION_MANAGER):
		#indexing starts at 0 - ID's start with 1
		ANIMAL_ID = ANIMAL+1
		#get X,Y data from this Animal's ROI
		X_corner = int(ROI.getXBase())
		Y_corner = int(ROI.getYBase())
		#get height and width data - 
		#NOTE THIS FUNCTION IS INDEPENDENT OF ROI_height and ROI_width
		#this function can also support ROIs of varying size
		REGION_WIDTH = int(ROI.getFloatWidth())
		REGION_HEIGHT = int(ROI.getFloatHeight())
		#calculate square pixel size of ROI
		SQAREA = REGION_WIDTH*REGION_HEIGHT
		#rediscover ROI center
		X_CENTER = X_corner + (REGION_WIDTH/2)
		Y_CENTER = Y_corner + (REGION_HEIGHT/2)
		#create txt file in OUTPUT_FOLDER from IMAGE_FILE_NAME (without file extension) and animal ID
		[EXTENSIONLESS_NAME,BLANK] = IMAGE_FILE_NAME.split('.tif')
		TXT_FILE_NAME = EXTENSIONLESS_NAME + 'an' + str(ANIMAL_ID) + '.txt'
		TXT_FILE_FULL = OUTPUT_FOLDER+'\\'+TXT_FILE_NAME
		VIDEO_ANIMAL_FILE=open(TXT_FILE_FULL,'w')
		#write HEADER to txt file
		VIDEO_ANIMAL_FILE.write(HEADER+'\n')
		#prepare for getting values and assembling FRAME_LINE
		MEDIAN_NAME = 'Median'+str(ANIMAL_ID)
		RAW_INT_NAME = 'RawIntDen'+str(ANIMAL_ID)
		GENERAL_START = str(WELL)+','+str(CYCLE)+','+str(ANIMAL_ID)+','
		GENERAL_GEOMETRY = str(X_CENTER)+','+str(Y_CENTER)+','+str(SQAREA)+','
		#loop through all frames
		for FRAME in range(0,NUMBER_OF_FRAMES):
			FRAME_RAW_INT = int(ROI_MEASUREMENTS.getValue(RAW_INT_NAME,FRAME))
			FRAME_MEDIAN = int(ROI_MEASUREMENTS.getValue(MEDIAN_NAME,FRAME))
			#calculate this frame sqintsub using the frame median, sqintdens, and sqarea
			FRAME_SQINTSUB = FRAME_RAW_INT - (SQAREA*FRAME_MEDIAN)
			#build frame measurement line:
			FRAME_MEASUREMENTS = str(FRAME_RAW_INT)+','+str(FRAME_MEDIAN)+','+str(FRAME_SQINTSUB)
			#Build FRAME_LINE from GENERAL_ and FRAME_ strings
			#[WELL CYCLE ANIMALID] FRAME [X Y SQAREA] [SQINTDENS BGMEDIAN SQINTSUB]
			FRAME_LINE = GENERAL_START+str(FRAME)+','+GENERAL_GEOMETRY+FRAME_MEASUREMENTS+'\n'
			#write line to txt file
			VIDEO_ANIMAL_FILE.write(FRAME_LINE)
		VIDEO_ANIMAL_FILE.close()
#END OF FUNCTIONS
###

#Execute Macro
if __name__ == '__main__':
    main()