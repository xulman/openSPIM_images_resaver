#@File (label="File with input directories:") inFile
#@String (label="Renaming instructions file:", value="renaming.txt") renameFileName

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


class OneFolder:
    def __init__(self, workFolder, outFolder):
        self.wrkDirStr = workFolder
        self.renamingFile = self.wrkDirStr + os.path.sep + renameFileName
        #
        self.outDirStr = outFolder

        # fetch the list of all files in the wrkDirStr directory
        self.allFiles = ""
        for rootDir,dirs,files in os.walk(self.wrkDirStr, topdown = True):
            #print(f"root = {rootDir}, dirs={dirs}, files={files}")
            self.allFiles = files
            break
        #print(f"all detected files={self.allFiles}")

        self.zSmallest = dict() # default: 99999
        self.zHighest = dict()  # default: -1
        self.zHighestOverall = -1

        for file in self.allFiles:
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
            zSmall = self.zSmallest.get(midStr, 99999)
            if zVal < zSmall:
                self.zSmallest[midStr] = zVal
            zHigh = self.zHighest.get(midStr, -1)
            if zVal > zHigh:
                self.zHighest[midStr] = zVal
                if zVal > self.zHighestOverall:
                    self.zHighestOverall = zVal

        # fetch the renaming map
        self.renameMap = dict()
        try:
            mapFile = open(self.renamingFile,"r")
            for pair in mapFile:
                if pair.startswith('#'):
                    continue
                sepIdx = pair.find("->")
                if sepIdx == -1:
                    continue
                fromStr = pair[0:sepIdx].strip()
                toStr = pair[sepIdx+2:].strip()
                self.renameMap[fromStr] = toStr
            mapFile.close()
        except IOError:
            print("Warning: " + self.renamingFile + " couldn't be opened, skipping this folder.")
            return

        print("Considering the following renaming map:")
        for m in self.renameMap:
            nm = self.renameMap.get(m,"not found")
            zs = str(self.zSmallest.get(m,"N/A"))
            zh = str(self.zHighest.get(m,"N/A"))
            print(m+" -> "+nm+"  with z-span of "+zs+" - "+zh)
        print("And the largest z-slice index in the folder was found "+str(self.zHighestOverall)+"\n")
    # end of __init__()


    def combineAllFilesMatching(self, fileNamePrefix, requiredPattern):
        visitedTimepoints = set()
        for fileRef in self.allFiles:
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
            for fileNow in self.allFiles:
                if not isMatchingPattern(fileNow, requiredPattern):
                    continue

                time = extractItemValue(fileNow, "_time")
                if time != timeRef:
                    continue

                z = extractItemValue(fileNow, "_z")
                if z < self.zSmallest[requiredPattern] or z > self.zHighest[requiredPattern]:
                    continue
                zSlicesFiles[z] = fileNow

                if firstFile is None or z < firstFileZ:
                    firstFile = fileNow
                    firstFileZ = z

            # now, all available files are identified, let's build the stack
            designationOfEmptySlice = "empty slice"
            print("using this plan:")
            for z in range(self.zHighestOverall+1):
                file = zSlicesFiles.get(z,designationOfEmptySlice)
                print("z="+str(z)+" from file: "+file)

            imgSlicePath = self.wrkDirStr + os.path.sep + firstFile
            imgSlice = IJ.openImage(imgSlicePath)
            if imgSlice is None:
                print("Couldn't actually open "+firstFile+", skipping this ("+str(timeRef)+") timepoint...")
                continue
            imgStack = ij.ImageStack(imgSlice.getWidth(), imgSlice.getHeight())

            for z in range(self.zHighestOverall+1):
                file = zSlicesFiles.get(z,designationOfEmptySlice)
                if file is designationOfEmptySlice:
                    # add the one-shared empty slice
                    imgStack.addSlice( ShortProcessor(imgSlice.getWidth(), imgSlice.getHeight()) )
                else:
                    # take from the disk
                    if file != firstFile:
                        imgSlicePath = self.wrkDirStr + os.path.sep + file
                        imgSlice = IJ.openImage(imgSlicePath)
                    imgStack.addSlice( imgSlice.getProcessor() )
                    imgSlice.close()

            saveStack(imgStack, fileNamePrefix, requiredPattern, timeRef)
    # end of combineAllFilesMatching()


    def run(self):
        # reduce the list to only wanted files, then do the renaming
        visitedPatterns = set()
        for file in self.allFiles:
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

            newMidStr = self.renameMap.get(midStr,None)
            if newMidStr is None:
                print("Warning: " + file + " with unknown middle section " + midStr + " was skipped!")
                continue

            combineAllFilesMatching(file[0:midIdx], midStr)
            print("-------------")
    # end of run()


    def saveStack(self, stackObj, fileNamePrefix, originalPattern, timepoint):
        global dryRun

        newMidStr = replaceTimePlaceholder(self.renameMap[originalPattern], timepoint)
        newFileName = fileNamePrefix + newMidStr + patternWhatFilesToCareAboutOnly
        outFile = self.outDirStr + os.path.sep + newFileName

        self.imgFinal = ij.ImagePlus(newFileName, stackObj)
        if dryRun:
            print("only showing now but would have saved as "+outFile)
            self.imgFinal.show()
        else:
            print("saving: "+outFile)
            IJ.save(self.imgFinal, outFile)
    # end of saveStack()






inFileStr = inFile.getAbsolutePath()

# store in a separate list all folders to be processed
folderFile = open(inFileStr, "r")
folders = []
for folder in folderFile:
    folders.append(folder.rstrip())
folderFile.close()

wrkDirStr = os.path.dirname(inFileStr)
outDirStr = outDir.getAbsolutePath() #TODO how is this done in the older?

Folders = []
for folder in folders:
    OF = OneFolder(wrkDirStr + os.path.sep + folder, outDirStr)
    if len(OF.renameMap) > 0: # non-emptiness indicates success
        Folders.append(OF)

# figure out z-max pairs
globalHighestZ = -1
for F in Folders:
    globalHighestZ = F.zHighestOverall if F.zHighestOverall > globalHighestZ else globalHighestZ
for F in Folders:
    F.zHighestOverall = globalHighestZ
print("The largest z-slice index over all folders was found "+str(globalHighestZ)+"\n")

for F in Folders:
    F.run()
