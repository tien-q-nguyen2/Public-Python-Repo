import os, shutil
from tkinter import *
from tkinter import ttk

#===== ===== =====#
#This stores the disk drives that are available on the computer
diskDrives = []

#This stores the size of used portion of the currently selected disk drive
currDiskSize = 0
global drive

for letter in range(67,91):  # 67 is 'C', 90 is 'Z'
 # e.g. if drive E doesn't exist, assume drives F, G,... also don't
 #if not os.path.exists(chr(letter) + ':/'): break #currently not used
 if os.path.exists(chr(letter) + ':/'):
  diskDrives.append(chr(letter))
	
#For each disk drive found, create an entry in the drop down select menu

global warningLog
warningLog = []

#===== ===== =====#
#Can handle and give alert about access-denied files
def getFileSize(filepath):
 try:
  return os.path.getsize(filepath)
 except Exception as excep:
  #if the system cannot find the file specified
  if(excep.errno == 2):
   warningLog.append("Can't find the file at " + filepath + \
    '. Assume file exists but with 0 byte size on disk.')
  #if the file cannot be accessed	by the system
  elif(excep.errno == 22):
   warningLog.append("Can't access the file at " + filepath + \
    '. Assume file exists but with 0 byte size on disk.')
  else:
   print(excep)
  return 0;
#===== ===== =====#

root = Tk()

content = ttk.Frame(root)

#Create the UI components that will populate the window
introLabel =  ttk.Label(content, text='These drives are available:')

driveVar = StringVar()
driveBox = ttk.Combobox(content, textvariable=driveVar)
driveBox['values'] = diskDrives

#usage: 1234 -> 1,234, 1234567 -> 1,234,567, ...
def formatWithCommas(numStr):
 #if less than 3 digits in the number, no need to format anything
 if(len(numStr) <= 3):
  return numStr
 newNumChars = []
 threeCounter = 0
 lenOfNumStr = len(numStr)
 currCharPos = 0
 for numChar in numStr[::-1]:
  newNumChars.append(numChar)
  threeCounter += 1
  currCharPos += 1
  if(threeCounter == 3):
   #e.g. if got to 1 in 123456, don't put a comma before 1 (or we get ,123,456)
   if(currCharPos == lenOfNumStr): break;
   newNumChars.append(',')
   threeCounter = 0
 return ''.join(newNumChars[::-1])

#Function to be called when the user clicked the 'Check' button
def getDiskSize():
 global currDisk
 currDisk = diskDrives[driveBox.current()] + ':/'
 #Get and format the disk drive usage data (from bytes to GB)
 diskDataTuple = shutil.disk_usage(currDisk)
 displayData = str(diskDataTuple[0] >> 30) + ' GB Total ' + \
			   '(' + str(diskDataTuple[1] >> 30) + ' GB Used, ' + \
			   str(diskDataTuple[2] >> 30) + ' GB Free)'
				
 
 global sizeContent 
 sizeContent.set(displayData)
 updateDirTree()

checkButton = ttk.Button(content, text = 'Check', command = getDiskSize)

sizeContent = StringVar()
diskUsageInfo = ttk.Label(content, textvariable = sizeContent)

def setParentFolderSize(size):
 global folderSize
 folderSize = size
 
def getCurrentFolderSize():
 global folderSize
 return folderSize
 
def getDataFor(parentDir, parentWidgetId):
 currLevelFileSizes = []

 try:
  filesAndDirs = os.listdir(parentDir)
 except Exception as excep:
  #if exception has a special error code associated to it,
  if (excep.errno != None): #throw the exception up a stack, to be processed
   raise Exception(excep.errno)
 likelyFolders = []
 likelyFiles = []
 for fileOrDir in filesAndDirs:
  if (len(parentDir + '/' + fileOrDir) > 260):
   print('filepath is too long to work with (over 260 characters).')
  if '.' not in fileOrDir:
   likelyFolders.append(fileOrDir)
  else:
   likelyFiles.append(fileOrDir)
 # Names of folders or files and their sizes on disk
 widgetsAndSizes = []
 
 #loop through likelyFiles to see what files may be folders
 for name in likelyFiles:
  try:
   #if not a folder, code will jump to except statement after os.listdir is run
   os.listdir(parentDir + '/' + name) 
   #if no exception thrown, name is a folder, so we move it to folders list
   likelyFolders.append(name) # and also remove the name from the files list
   likelyFiles.remove(name)
   
  except Exception as excep:
   #If the directory name is invalid (the case when using listdir on a file)
   if(excep.errno == 20): # path name is indeed a file, do nothing
    pass
   elif(excep.errno == 13):
    warningLog.append("Can't access the folder at " + parentDir + '/' + name + \
     '. Assume path exists with 0 byte size on disk.')
   elif(excep.errno == 2):
    warningLog.append("Can't find the folder at " + parentDir + '/' + name + \
     '. Assume path exists with 0 byte size on disk.')
   else:
    warningLog.append('(Errno: ' + excep.errno + ') - ' + str(excep))
 
 #loop through the names likely to be folders first, this is necessary
 # for us to perform left-to-right tree traversal
 for name in likelyFolders: ##if a file get in here, program will ...
  try:
   #insert a new widget corresponding to the current folder path, then detach it
   newWidgetId = dirTree.insert(parentWidgetId, 'end', text=name)
   dirTree.detach(newWidgetId)
   #recursively go down folder(s) and file(s) one level below
   getDataFor(parentDir + '/' + name, newWidgetId)
   #get the folder size of the current dir (set by setParentFolderSize below)
   folderSize = getCurrentFolderSize()
   #add this folder size to a list of sizes of current level's files and folders,
   # so that we can find the size of the folder one level above this (also below)
   currLevelFileSizes.append(folderSize)
   #append it to a list of folders and files found on the current tree level
   widgetsAndSizes.append( (newWidgetId , folderSize) )
  #Any exception errno (20, 13) is thrown up from getDataFor()
  except Exception as excep:
   #if given directory name is invalid (turned out to be a file and not a folder)
   if (str(excep) == '20'):
    #move on to processing as if it was a file by moving it to likelyFiles array
    likelyFiles.append(name)
   #if access to the folder (or file) is denied
   elif (str(excep) == '13'):
    warningLog.append("Can't access the folder at " + parentDir + '/' + name + \
		'. Assume path exists with 0 byte size on disk.')
   else:
    try:
     warningLog.append('(Errno: ' + excep.errno + ') - ' + str(excep))
    except: #if exception doesn't have the attribute errno
     warningLog.append(str(excep))
   
 for name in likelyFiles:
  try:
   #insert a new widget corresponding to the current file path, then detach it
   newWidgetId = dirTree.insert(parentWidgetId, 'end', text=name)
   dirTree.detach(newWidgetId)
   #get the file size of the current file (in the likelyFiles list)
   fileSize = getFileSize(parentDir + '/' + name)
   currLevelFileSizes.append(fileSize)
   #append it to a list of folders and files found on the current tree level
   widgetsAndSizes.append( (newWidgetId , fileSize) )
   
  except Exception as excep:
   warningLog.append(str(excep))
   
 parentFolderSize = sum(currLevelFileSizes)
 setParentFolderSize(parentFolderSize)
 
 #Sort the files and folders based on sizes on disk, descendingly
 widgetsAndSizes = sorted(widgetsAndSizes, \
  key = lambda tupleData: tupleData[1], reverse=True)
   
 for widgetId, size in widgetsAndSizes:
   dirTree.move(widgetId, parentWidgetId, 'end')
   dirTree.set(widgetId, 'size', formatWithCommas(str(size >> 20)) + ' MB')
   

def updateDirTree():
 global currDisk, dirTree
 
 #Initialize dirTreeIds if it has not been init before
 try: dirTreeIds
 except: dirTreeIds = []
 
 #Reset the treeview
 dirTree.delete(*dirTree.get_children())

 #Start traversing through the directories and populating the treeview
 getDataFor(currDisk, '')
 
#I can do something with warningLog here in the future if I like
 
#Create a treeview for our folders and files, with a column 'size'
dirTree = ttk.Treeview(content, columns = ('size'))
dirTree.heading('size', text = 'Size')
dirTree.column('size', width = 75, anchor = 'e', stretch = 0)

#Place the UI components into the content window
#Row 0 (first row)
content.grid(column = 0, row = 0, padx = 10, pady = 10, sticky=(N,W,E,S))
#Row 1
introLabel.grid(column = 0, row = 0)
driveBox.grid(column = 0, row = 1, pady = 5)	
checkButton.grid(column = 1, row = 1)
#Row 2
diskUsageInfo.grid(column = 0, columnspan = 2, row = 2)
#Row 3
dirTree.grid(column = 0, row = 3, columnspan = 2, padx=10, pady=10, \
 sticky=(N,W,E,S))

#make the UI grids responsive
root.columnconfigure(0, weight = 1)
root.rowconfigure(0, weight = 1)

content.columnconfigure(0, weight=1)
content.columnconfigure(1, weight=1)
content.rowconfigure(0, weight = 0)
content.rowconfigure(1, weight = 0)
content.rowconfigure(2, weight = 0)
content.rowconfigure(3, weight = 1)

#Run the UI
root.mainloop()
