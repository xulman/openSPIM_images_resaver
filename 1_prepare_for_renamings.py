#@File (label="File with input directories:") inFile
#@String (label="Renaming instructions file:", value="renaming.txt") renameFileName

# the file names are understood to consist of three sections:
# common prefix, then middle section like _channelX_..._positionY_viewZ, and _timeT_zZ.tif postfix
patternHowMiddleSectionStarts = "_channel"
patternHowLastSectionStarts = "_time"
patternWhatFilesToCareAboutOnly = ".tif"

# =======================================================================================
import os.path


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


def processOneFolder(wrkDirStr):
    print("Analyzing now folder: "+wrkDirStr)

    # fetch the list of all files in the wrkDirStr directory
    allFiles = ""
    for rootDir,dirs,files in os.walk(wrkDirStr, topdown = True):
        #print(f"root = {rootDir}, dirs={dirs}, files={files}")
        allFiles = files
        break
    #print(f"all detected files={allFiles}")


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

    renamingFile = wrkDirStr + os.path.sep + renameFileName
    outFile = open(renamingFile,"w")
    outFile.write("# A quick help here:\n")
    outFile.write("# Each line represents one discovered pattern, one combination.\n")
    outFile.write("# The lines are organized as 'leftSide' -> 'rightSide'.\n")
    outFile.write("# 'leftSide' you should not change, the program uses it to match/find the right files.\n")
    outFile.write("# 'rightSide' you should change to how you prefer to have the combination actually named.\n")
    outFile.write("# 'rightSide' should include a special term '{3}'.\n")
    outFile.write("# '{3}' is a placeholder where time information will be printed in the file name.\n")
    outFile.write("# '{3}' says that the time information will be printed using (at least) 3 digits, zero padded.\n")
    outFile.write("# '{3}' can be positioned anywhere in the 'rightSide' text, e.g. timepoint{3}_channel1...\n")
    outFile.write("#\n")
    for m in sorted(middleSections):
        outFile.write(m + " -> " + m + "_tp{3}\n")
    outFile.close()
    print("were written into a file: " + renamingFile)


inFileStr = inFile.getAbsolutePath()
wrkDirStr = os.path.dirname(inFileStr)

folders = open(inFileStr, "r")
for folder in folders:
    processOneFolder(wrkDirStr + os.path.sep + folder.rstrip())
folders.close()
