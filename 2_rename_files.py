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
from ij import IJ
import ij.ImagePlus
import ij.ImageStack
from ij.process import ShortProcessor

wrkDirStr = wrkDir.getAbsolutePath()
outDirStr = outDir.getAbsolutePath()
renamingFile = wrkDirStr + os.path.sep + renameFileName

##xx## #@String (label="zStacking instructions file:", value="zStacks.txt") zStacksFileName
# zStackFile = wrkDirStr + os.path.sep + zStacksFileName


def extractItemValue(filename, itempattern):
    idx = filename.find(itempattern)
    if idx == -1:
        # not found the field (e.g. _z000)
        return -1

    idx += len(itempattern)
    digits = 1
    while filename[idx:idx+digits].isdigit():
        digits += 1
    digits -= 1 # the last functional before the condition broke

    if digits == 0:
        # not found _z000 field
        return -1

    return int(filename[idx:idx+digits])


def isMatchingPattern(filename, requiredPattern):
    return True if filename.find(requiredPattern) > -1 else False


# fetch the list of all files in the wrkDirStr directory
allFiles = ""
for rootDir,dirs,files in os.walk(wrkDirStr, topdown = True):
    #print(f"root = {rootDir}, dirs={dirs}, files={files}")
    allFiles = files
    break
#print(f"all detected files={allFiles}")

zSmallest = dict() # default: 99999
zHighest = dict()  # default: -1
zHighestOverall = -1

for file in allFiles:
    # a wanted file?
    if not file.endswith(patternWhatFilesToCareAboutOnly):
        continue

    midIdx = file.find(patternHowMiddleSectionStarts)
    lstIdx = file.find(patternHowLastSectionStarts)
    # were the sections detected at all?
    if midIdx == -1 or lstIdx <= midIdx:
        # don't warn yet... will come over this image again later (and would warn then)
        # print("Warning: " + file + " with not explicit middle section was skipped!")
        continue

    midStr = file[midIdx:lstIdx]

    # what is the z-index in this file? ...and for this pattern
    zVal = extractItemValue(file, "_z")
    zSmall = zSmallest.get(midStr, 99999)
    if zVal < zSmall:
        zSmallest[midStr] = zVal
    zHigh = zHighest.get(midStr, -1)
    if zVal > zHigh:
        zHighest[midStr] = zVal
        if zVal > zHighestOverall:
            zHighestOverall = zVal


# fetch the renamings map
renameMap = dict()
mapFile = open(renamingFile,"r")
for pair in mapFile:
    if pair.startswith('#'):
        continue
    sepIdx = pair.find("->")
    if sepIdx == -1:
        continue
    fromStr = pair[0:sepIdx].strip()
    toStr = pair[sepIdx+2:].strip()
    renameMap[fromStr] = toStr
mapFile.close()

print("Considering the following renaming map:")
for m in renameMap:
    nm = renameMap.get(m,"not found")
    zs = str(zSmallest.get(m,"N/A"))
    zh = str(zHighest.get(m,"N/A"))
    print(m+" -> "+nm+"  with z-span of "+zs+" - "+zh)
print("And the largest z-slice index in the folder was found "+str(zHighestOverall)+"\n")


def replaceTimePlaceholder(msg, timeValue):
    idx = msg.find("{")
    if idx == -1:
        return msg+"_tp"+str(timeValue)

    dIdx = idx + 1
    digits = 1
    while msg[dIdx:dIdx+digits].isdigit() and dIdx+digits <= len(msg):
        digits += 1
    digits -= 1

    if digits == 0:
        return msg+"_tp"+str(timeValue)

    width = int(msg[dIdx:dIdx+digits])

    timeStr = str(timeValue)
    if len(timeStr) < width:
        timeStr = ("0000000000000000000"+timeStr)[-width:]

    return msg[:idx] + timeStr + msg[dIdx+digits+1:]


def saveStack(stackObj, fileNamePrefix, originalPattern, timepoint):
    global patternWhatFilesToCareAboutOnly
    global outDirStr
    global renameMap
    global dryRun

    newMidStr = replaceTimePlaceholder(renameMap[originalPattern], timepoint)
    newFileName = fileNamePrefix + newMidStr + patternWhatFilesToCareAboutOnly
    outFile = outDirStr + os.path.sep + newFileName

    imgFinal = ij.ImagePlus(newFileName, stackObj)
    if dryRun:
        print("only showing now but would have saved as "+outFile)
        imgFinal.show()
    else:
        print("saving: "+outFile)
        IJ.save(imgFinal, outFile)


def combineAllFilesMatching(allFilesInFolder, inputFolderPath, requiredPattern):
    global zSmallest
    global zHighest
    global zHighestOverall

    visitedTimepoints = set()
    for fileRef in allFilesInFolder:
        if not isMatchingPattern(fileRef, requiredPattern):
            continue

        timeRef = extractItemValue(fileRef, "_time")
        if timeRef in visitedTimepoints:
            continue
        visitedTimepoints.add(timeRef)

        # okay, we're now doing 'timeRef' timepoint (of this 'requiredPattern')
        print("Stacking: "+requiredPattern+" at time "+str(timeRef))
        zSlicesFiles = dict()
        firstFile = None
        firstFileZ = 99999
        for fileNow in allFilesInFolder:
            if not isMatchingPattern(fileNow, requiredPattern):
                continue

            time = extractItemValue(fileNow, "_time")
            if time != timeRef:
                continue

            z = extractItemValue(fileNow, "_z")
            if z < zSmallest[requiredPattern] or z > zHighest[requiredPattern]:
                continue
            zSlicesFiles[z] = fileNow

            if firstFile is None or z < firstFileZ:
                firstFile = fileNow
                firstFileZ = z

        # now, all available files are identified, let's build the stack
        designationOfEmptySlice = "empty slice"
        print("using this plan:")
        for z in range(zHighestOverall+1):
            file = zSlicesFiles.get(z,designationOfEmptySlice)
            print("z="+str(z)+" from file: "+file)

        imgSlicePath = inputFolderPath + os.path.sep + firstFile
        imgSlice = IJ.openImage(imgSlicePath)
        if imgSlice is None:
            print("Couldn't actually open "+firstFile+", skipping this ("+str(timeRef)+") timepoint...")
            continue
        imgStack = ij.ImageStack(imgSlice.getWidth(), imgSlice.getHeight())

        for z in range(zHighestOverall+1):
            file = zSlicesFiles.get(z,designationOfEmptySlice)
            if file is designationOfEmptySlice:
                # add the one-shared empty slice
                imgStack.addSlice( ShortProcessor(imgSlice.getWidth(), imgSlice.getHeight()) )
            else:
                # take from the disk
                if file != firstFile:
                    imgSlicePath = inputFolderPath + os.path.sep + file
                    imgSlice = IJ.openImage(imgSlicePath)
                imgStack.addSlice( imgSlice.getProcessor() )
                imgSlice.close()

        saveStack(imgStack, fileRef[0:midIdx], requiredPattern, timeRef)


# reduce the list to only wanted files, then do the renaming
visitedPatterns = set()
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

    # already processed stack?
    if midStr in visitedPatterns:
        continue
    visitedPatterns.add(midStr)

    newMidStr = renameMap.get(midStr,None)
    if newMidStr is None:
        print("Warning: " + file + " with unknown middle section " + midStr + " was skipped!")
        continue

    combineAllFilesMatching(allFiles, wrkDirStr, midStr)
    print("-------------")

