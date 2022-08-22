#@File (label="Directory with original files:", style="directory") wrkDir
#@String (label="Renaming instructions file:", value="renamings.txt") renameFileName
#@File (label="Directory with renamed files:", style="directory") outDir
#@Boolean (label="Dry run, no renaming now:", value="True") dryRun

# the file names are understood to consist of three sections:
# common prefix, then middle section like _channelX_..._positionY_viewZ, and _timeT_zZ.tif postfix
patternHowMiddleSectionStarts = "_channel"
patternHowLastSectionStarts = "_time"
patternWhatFilesToCareAboutOnly = ".tif"

# =======================================================================================
import os.path
import shutil

wrkDirStr = wrkDir.getAbsolutePath()
outDirStr = outDir.getAbsolutePath()
renamingFile = wrkDirStr + os.path.sep + renameFileName


# fetch the renamings map
renameMap = dict()
mapFile = open(renamingFile,"r")
for pair in mapFile:
    sepIdx = pair.find("->")
    if sepIdx == -1:
        continue
    fromStr = pair[0:sepIdx].strip()
    toStr = pair[sepIdx+2:].strip()
    renameMap[fromStr] = toStr
mapFile.close()
print("considering the following renaming map:")
for m in renameMap:
    print(m+" -> "+renameMap[m])
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
        print("Warning: " + file + " with not explicit middle section was skipped!")
        continue
    midStr = file[midIdx:lstIdx]
    newMidStr = renameMap.get(midStr,None)
    if newMidStr is None:
        print("Warning: " + file + " with unknown middle section " + midStr + " was skipped!")
        continue

    newFile = file[0:midIdx] + newMidStr + file[lstIdx:]
    if not dryRun:
        print("renaming: "+file+" -> "+newFile)

    inFile  = wrkDirStr + os.path.sep + file
    outFile = outDirStr + os.path.sep + newFile
    if dryRun:
        print("NOT moving "+inFile+" to "+outFile)
    else:
        shutil.move(inFile,outFile)
