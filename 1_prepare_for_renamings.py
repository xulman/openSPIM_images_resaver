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

##xx## #@String (label="zStacking instructions file:", value="zStacks.txt") zStacksFileName
# zStackFile = wrkDirStr + os.path.sep + zStacksFileName


# fetch the list of all files in the wrkDirStr directory
allFiles = ""
for rootDir,dirs,files in os.walk(wrkDirStr, topdown = True):
    #print(f"root = {rootDir}, dirs={dirs}, files={files}")
    allFiles = files
    break
#print(f"all detected files={allFiles}")


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


# reduce the list to only wanted files, then extract
# all observed middle sections and their z-spans
middleSections = set()
zSmallest = dict() # default: 99999
zHighest = dict()  # default: -1

for file in allFiles:
    # a wanted file?
    if not file.endswith(patternWhatFilesToCareAboutOnly):
        continue

    midIdx = file.find(patternHowMiddleSectionStarts)
    lstIdx = file.find(patternHowLastSectionStarts)
    # were the sections detected at all?
    if midIdx == -1 or lstIdx <= midIdx:
        print("Warning: " + file + " with not explicit middle section was skipped!")
        continue

    midStr = file[midIdx:lstIdx]
    middleSections.add(midStr)

    # what is the z-index in this file? ...and for this pattern
    zVal = extractItemValue(file, "_z")
    zSmall = zSmallest.get(midStr, 99999)
    if zVal < zSmall:
        zSmallest[midStr] = zVal
    zHigh = zHighest.get(midStr, -1)
    if zVal > zHigh:
        zHighest[midStr] = zVal

print("All observed middle sections:")
for m in middleSections:
    print(m+" with z-span of "+str(zSmallest[m])+" - "+str(zHighest[m]))

outFile = open(renamingFile,"w")
for m in sorted(middleSections):
    outFile.write(m + " -> " + m + "\n")
outFile.close()
print("were written into a file: " + renamingFile)
