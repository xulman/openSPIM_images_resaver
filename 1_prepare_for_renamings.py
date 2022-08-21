#@File (label="Directory with files:", style="directory") wrkDir
#@String (label="Renaming instructions file:", value="renamings.txt") renameFileName

# the file names are understood to consist of three sections:
# common prefix, then middle section like _channelX_..._positionY_viewZ, and _timeT_zZ.tif postfix
patternHowMiddleSectionStarts = "_channel"
patternHowLastSectionStarts = "_time"
patternWhatFilesToCareAboutOnly = ".tif"

# =======================================================================================
import os.path

wrkDirStr = wrkDir.getAbsolutePath()
renamingFile = wrkDirStr + os.path.sep + renameFileName


# fetch the list of all files in the wrkDirStr directory
allFiles = ""
for rootDir,dirs,files in os.walk(wrkDirStr, topdown = True):
	#print(f"root = {rootDir}, dirs={dirs}, files={files}")
	allFiles = files
	break
#print(f"all detected files={allFiles}")

# reduce the list to only wanted files, then extract all observed middle sections
middleSections = set()
for file in allFiles:
	if not file.endswith(patternWhatFilesToCareAboutOnly):
		continue
	midIdx = file.find(patternHowMiddleSectionStarts)
	lstIdx = file.find(patternHowLastSectionStarts)
	# were the sections detected at all?
	if midIdx > -1 and lstIdx > midIdx:
		midStr = file[midIdx:lstIdx]
		middleSections.add(midStr)
print("all observed middle sections:")
print(middleSections)

outFile = open(renamingFile,"w")
for m in sorted(middleSections):
	outFile.write(m + " -> " + m + "\n")
outFile.close()
print("were written into a file: " + renamingFile)