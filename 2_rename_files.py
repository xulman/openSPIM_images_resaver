#@File (label="Directory with original files:", style="directory") wrkDir
#@String (label="renaming instructions file:", default="renamings.txt") renameFileName
#@File (label="Directory with renamed files:", style="directory") outDir
#@Boolean (label="Dry run, no renaming now:") dryRun

# the file names are understood to consist of three sections:
# common prefix, then middle section like _channelX_..._positionY_viewZ, and _timeT_zZ.tif postfix
patternHowMiddleSectionStarts = "_channel"
patternHowLastSectionStarts = "_time"
patternWhatFilesToCareAboutOnly = ".tif"

# =======================================================================================
from cmath import inf
import os.path
import shutil

#renamingFile = wrkDir.getAbsolutePath() + os.path.sep + renameFileName
renamingFile = "/temp/Johannes/tstFolder/renaming.txt"
wrkDirStr = "/temp/Johannes/tstFolder"
outDirStr = "/temp/Johannes/renamedFolder"
dryRun = False

# fetch the renamings map
renameMap = dict()
mapFile = open(renamingFile,"r")
for pair in mapFile:
	sepIdx = pair.find("->")
	if sepIdx == -1:
		continue
	fromStr = pair[0:sepIdx].strip()
	toStr = pair[sepIdx+2:-1].strip()
	renameMap[fromStr] = toStr
mapFile.close()
print("considering the following renaming map:")
print(renameMap)
print("")

# fetch the list of all files in the wrkDirStr directory
allFiles = ""
for rootDir,dirs,files in os.walk(wrkDirStr, topdown = True):
	#print(f"root = {rootDir}, dirs={dirs}, files={files}")
	allFiles = files
	break
#print(f"all detected files={allFiles}")

# reduce the list to only wanted files, then do the renaming
for file in allFiles:
	if not file.endswith(patternWhatFilesToCareAboutOnly):
		continue
	midIdx = file.find(patternHowMiddleSectionStarts)
	lstIdx = file.find(patternHowLastSectionStarts)
	# were the sections detected at all?
	if midIdx == -1 or lstIdx <= midIdx:
		print(f"Warning: {file} with not explicit middle section was skipped!")
		continue
	midStr = file[midIdx:lstIdx]
	newMidStr = renameMap.get(midStr,"")
	if newMidStr is "":
		print(f"Warning: {file} with unknown middle section {midStr} was skipped!")
		continue

	newFile = file[0:midIdx] + newMidStr + file[lstIdx:-1]
	print(f"renaming: {file} -> {newFile}")

	inFile  = wrkDirStr + os.path.sep + file
	outFile = outDirStr + os.path.sep + newFile
	if dryRun:
		print(f"NOT moving {inFile} to {outFile}")
	else:
		shutil.move(inFile,outFile)
