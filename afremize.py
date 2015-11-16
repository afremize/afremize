# Copyright (C) 2015 Jana Cavojska
# This file is part of 'Afremize'.

# 'Afremize' is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 2 of the License.

# 'Afremize' is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with 'Afremize'.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import division
import numpy as np
import random
from random import randint
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
from skimage.segmentation import felzenszwalb
from math import sqrt, acos, degrees, ceil, floor
import warnings
import os

# own imports:
import imgIO
import brushstroke


# give each felzenszwalb segment a random color to improve their visibility and save the clusters as a new image
def saveClusteredImage(inPix, segmentsByIDlist, width, height, filename):
    im, pix = imgIO.createWhiteImg(width, height)
    for segment in range(0,len(segmentsByIDlist)):
        RGB = inPix[segmentsByIDlist[segment][0][0], segmentsByIDlist[segment][0][1]]
        for p in range (0, len(segmentsByIDlist[segment])):
            pix[segmentsByIDlist[segment][p][0], segmentsByIDlist[segment][p][1]] = RGB
    im.save(filename + "_clustered.png")
    del im
    del pix
    im, pix = imgIO.createWhiteImg(width, height)
    for segment in range(0,len(segmentsByIDlist)):
        RGB = (randint(0,255), randint(0,255), randint(0,255))
        for p in range (0, len(segmentsByIDlist[segment])):
            pix[segmentsByIDlist[segment][p][0], segmentsByIDlist[segment][p][1]] = RGB
    im.save(filename + "_clustered_randomColor.png")
    del im
    del pix



# color each segment in outPix with the color inPix contains at that position:
def colorImgSegments(inPix, segmentsByIDlist, outPix):
    for segment in range(0, len(segmentsByIDlist)):
        RGB = inPix[segmentsByIDlist[segment][0][0], segmentsByIDlist[segment][0][1]]
        for p in range (0, len(segmentsByIDlist[segment])):
            outPix[segmentsByIDlist[segment][p][0], segmentsByIDlist[segment][p][1]] = RGB
    return outPix


def colorBackground(inIm, inPix, segmentsByIDlist, outIm, outPix, background="blur"):
    if background == "blur": # use the blurred input image as background for the output image
        outIm = inIm.filter(ImageFilter.BLUR)
        outPix = outIm.load()
    elif background == "cluster":
        outPix = colorImgSegments(inPix, segmentsByIDlist, outPix)
    return outIm, outPix


def getOutfileName(path, output_dir, infile):
    extension = ".png"
    appendix = "__out"
    outfileTmp = infile.split('.')
    filename = ''
    for namepiece in range(0, len(outfileTmp) - 1):
        filename = filename + outfileTmp[namepiece]
    i = 0
    outfile = path + output_dir + filename
    while True or i < 500:
        if os.path.exists(outfile + appendix + extension):
            appendix = appendix + "__out"
        else:
            outfile = outfile + appendix + extension
            break
    return filename, outfile


def clustering(inPixNP, width, height, scale=50, sigma=4.5, min_size=10):
    segmentsNP = felzenszwalb(inPixNP, scale, sigma, min_size)
    # felzenszwalb(image, scale=1, sigma=0.8, min_size=20)
    # image : (width, height, 3) or (width, height) ndarray - Input image.
    # scale : float - Free parameter. Higher means larger clusters.
    # sigma : float - Width of Gaussian kernel used in preprocessing.
    # min_size : int - Minimum component size. Enforced using postprocessing.
    
    # create a data structure with regionIDs as keys and lists of their pixel coordinates as values:
    maxSegmentID = np.max(segmentsNP)
    segmentsByIDlist = [[] for i in range(maxSegmentID + 1)]
    for y in range(0,height):
        for x in range(0,width):
            regionID = segmentsNP[y,x]
            segmentsByIDlist[regionID].append((x, y))
    return segmentsNP, segmentsByIDlist


def getRegLineCoordinates(minX, maxX, regression, height):
    # create an array regLine with all x and y coordinates of the regression line
    start = regression[0]*(minX**2) + regression[1]*minX + regression[2]
    stop = regression[0]*(maxX**2) + regression[1]*maxX + regression[2]
    numOfPointsX = euclidDist((minX, start), (maxX, stop))
    stepSize = (maxX - minX) / numOfPointsX
    pointsX = (np.arange(minX, maxX + 1, stepSize)).tolist()
    pointsY = list(pointsX)
    
    stopLen = len(pointsY)
    pointY = 0
    while pointY < stopLen:
        pointsY[pointY] = int(regression[0]*(pointsY[pointY]**2) + regression[1]*pointsY[pointY] + regression[2])
        if pointsY[pointY] < 0 or pointsY[pointY] > height - 1: # this regression point is out of range of the input image, so discard it
            del pointsX[pointY]
            del pointsY[pointY]
            stopLen = stopLen - 1
        else:
            pointY = pointY + 1
    return [[int(i) for i in pointsX], [int(i) for i in pointsY]]



# compute regression lines and rotated bounding boxes of all segments
# linear regression if the mean squared error is small enough, quadratic regression otherwise
def getSegmentParams(segmentsByIDlist_sorted, inPix, drawRegressionLines, inImCopy, inPixCopy, width, height):
    
    segmentParams = []
    maxSegmentID = len(segmentsByIDlist_sorted) - 1
    
    if drawRegressionLines:
        inCopyDraw = ImageDraw.Draw(inImCopy)
        
    for segmentIndex in range(0, maxSegmentID + 1):
        regLine = []
        xList = [x[0] for x in segmentsByIDlist_sorted[segmentIndex][1]]  # list of all x coordinates of this segment
        yList = [x[1] for x in segmentsByIDlist_sorted[segmentIndex][1]]
        
        degree = 2 # degree of polynomial regression used
        
        # compute the coefficients of the regression line:
        if len(xList) <= degree+6 or len(yList) <= degree+6: # to fix "ValueError: On entry to DLASCL parameter number 4 had an illegal value" which occurs when there is not enough data for a regression
            continue
        minX = min(xList)
        maxX = max(xList)
        minY = min(yList)
        maxY = max(yList)
            
        if xList[1:] == xList[:-1] or yList[1:] == yList[:-1]: # because if all the elements in either list are  identical, the regression will fail and the program will exit
            regLine = [xList, yList]
        else: # do the regression
            regressionSuccessful = False
            with warnings.catch_warnings():
                warnings.filterwarnings('error')
                try:
                    regression = np.polyfit(xList, yList, degree)
                    regressionSuccessful = True
                except np.RankWarning: # RankWarning means there's not enough data to do regression properly
                    #print("not enough data for segmentID "+str(segmentID))
                    regressionSuccessful = False
            
            if not regressionSuccessful:
                continue
            
            # compute the values of the regression line (pointsX = all x-coordinates, pointsY = all y-coordinates):
            pointsX, pointsY = getRegLineCoordinates(minX, maxX, regression, height)
            regLine = [pointsX, pointsY]
        
        startPoint = regLine[1][0]  # y coordinate of the regression line starting point
        stopPoint = regLine[1][-1]  # y coordinate of the regression line starting point
        
        if drawRegressionLines:
            for i in range(0, len(pointsY)):
                # get coordinates that lie on this regression line and WITHIN the borders of the input picture
                inPixCopy[min(max(0,pointsX[i]), width-1), min(max(0,pointsY[i]),height-1)] = (255,255,0)
        
        
        # compute the angle of the regression line:
        angle = 0
        if minX != maxX:
            hypotenuse = sqrt((maxX - minX)**2 + (stopPoint - startPoint)**2)
            adjacent = abs(stopPoint - startPoint)
            if stopPoint > startPoint: # both x and y coordinate increase; we have to rotate clockwise by angle
                angle = -degrees(acos(adjacent / hypotenuse))
            elif stopPoint <= startPoint: # rotate counter-clockwise by angle to make segment upright
                angle = degrees(acos(adjacent / hypotenuse))
        
        segmentID = segmentsByIDlist_sorted[segmentIndex][0]
        numOfPixels = len(segmentsByIDlist_sorted[segmentIndex][1]) - 1
        # bboxN contains the absolute coordinates of the segment's not-rotated bounding box and should be used to determine the segment's position in the input image.
        bboxN = [minX, minY, maxX, maxY]
        segmentParams.append([segmentID, regLine, angle, bboxN, degree, numOfPixels, regression])
    return segmentParams


def euclidDist(p1, p2):
    return sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)


# compute a list of random coordinates within this segment where to place complex brushstrokes
# segment is a list of coordinate tuples of this segment
def getStrokePositions(segment, stroke_density, minX, minY, maxX, maxY):
    coordinates = []
    for x in range(minX, maxX + 1, stroke_density):
        for y in range(minY, maxY + 1, stroke_density):
            
            if (x, y) in segment:
                coordinates.append([x, y])
    random.shuffle(coordinates)
    return coordinates



# This function returns the difference between the color of a segment and the colors of its neighboring pixels (the four pixels lying just outside the segment's unrotated bounding box)
def differenceToNeighbors(segmentID, segmentsByIDlistNP, inPix, minX, minY, maxX, maxY):
    segmentRepresentative = segmentsByIDlistNP[segmentID][0]
    segmentColor = np.asarray(inPix[segmentRepresentative[0], segmentRepresentative[1]])
    diffN = np.sum(abs(segmentColor - np.asarray(inPix[minX, minY]))) + np.sum(abs(segmentColor - np.asarray(inPix[maxX, minY]))) + np.sum(abs(segmentColor - np.asarray(inPix[minX, maxY]))) + np.sum(abs(segmentColor - np.asarray(inPix[maxX, maxY]))) # accumulate color distances to the neighbor pixels
    return diffN


def setParameters(width, height, verbose, randSizes=100, longStrokes=False, strokeWidth=None, strokeHeight=None, strokeDensity=None):
    # stroke width and height:
    if width > height:
        factor = 0.85
        factor = 1.0
    else:
        factor = 1.0
    if strokeWidth == None:
        complex_sizeX = int((width + height) * (0.01 * (2.66667 - 0.000166667 * (width + height))) * factor)
    else:
        complex_sizeX = strokeWidth
    
    if strokeHeight == None:
        complex_sizeY = complex_sizeX
    else:
        complex_sizeY = strokeHeight
    
    if longStrokes:
        complex_sizeY = int(complex_sizeX * 1.7)
        complex_sizeX = int(max(1, complex_sizeX * 0.8))
    
    
    # stroke density:
    if strokeDensity != None:
        stroke_density = strokeDensity
    elif strokeWidth != None: # if the user specified strokeWidth but not strokeDensity, we try to guess a value for stroke_density which would nicely cover most of the picture with brush strokes
        stroke_density = max(1, strokeWidth // 3)
    elif strokeHeight != None:
        stroke_density = max(1, strokeHeight // 3)
    else:
        stroke_density = max(1, int((width + height) * 0.01 * (1.66667 - 0.000166667 * (width + height))))
    if width > height:
        stroke_density = int(max(1, stroke_density * factor))
    
    if longStrokes:
        stroke_density = max(1, int(stroke_density * factor ))
    
    if verbose:
        if randSizes < 100:
            print("strokeWidth: random, max. "+str(complex_sizeX)
                  +"\nstrokeHeight: random, max. "+str(complex_sizeY)
                  +"\nstrokeDensity: random, max. "+str(stroke_density))
        else:
            print("strokeWidth: "+str(complex_sizeX)
                  + "\nstrokeHeight: "+str(complex_sizeY)
                  + "\nstrokeDensity: "+str(stroke_density))
    return complex_sizeX, complex_sizeY, stroke_density


def randStrokesParams(randSizes, complex_sizeX, complex_sizeY, stroke_density):
    scaleFactor = randint(randSizes, 100)
    complex_sizeX = max(1, (complex_sizeX * scaleFactor) // 100)
    complex_sizeY = max(1, (complex_sizeY * scaleFactor) // 100)
    stroke_density = max(1, (stroke_density * scaleFactor) // 100)
    return complex_sizeX, complex_sizeY, stroke_density


# make the brush stroke with these startColors and endColors look more vivid:
def makeMoreVivid(startColors, endColors):
    # increase the value of the color channel with the highest value by 50
    maxChannel = startColors[0].argmax()
    endColors[0][maxChannel] = min(255, endColors[0][maxChannel] + 50)
    maxChannel = endColors[-1].argmax()
    startColors[-1][maxChannel] = min(255, startColors[-1][maxChannel] + 50)
    return startColors, endColors


# sample the colors from the positions in the input image where brushstroke is to be placed:
def sampleStartEndColors(inPix, X, Y, width, height, complex_sizeXrand, complex_sizeYrand):
    halfSizeX = complex_sizeXrand // 2
    halfSizeY = complex_sizeYrand // 2
    upperleftCornerX = max(0, X - halfSizeX)
    upperleftCornerY = max(0, Y - halfSizeY)
    scolor1 = np.array(inPix[upperleftCornerX, upperleftCornerY])
    scolor2 = np.array(inPix[min(width-1, upperleftCornerX + complex_sizeXrand), upperleftCornerY])
    startColors = np.array([scolor1, scolor2])
    
    ecolor1 = np.array(inPix[upperleftCornerX, min(height-1, upperleftCornerY + complex_sizeYrand)])
    ecolor2 = np.array(inPix[min(width-1, upperleftCornerX + complex_sizeXrand), min(height-1, upperleftCornerY + complex_sizeYrand)])
    endColors = np.array([ecolor1, ecolor2])
    return startColors, endColors


# segmentsByIDlist: a list where the index is the segmentID and the element behind this index is a list of all tuples (x,y) where x,y are coordinates of a pixel belonging to this regionID
# fill the output image with brush strokes and save it
# segmentParams as a list of elements of the form [segmentID, regLine, angle, bbox, degree]
def paintImg_with_brushstrokes(outfile, outIm, outPix, width, height, segmentParams, segmentsByIDlist, inPix, verbose, randSizes=100, longStrokes=False, directedRotate=False, strokeWidth=None, strokeHeight=None, strokeDensity=None, noHairlines=False, noMargins=False, segBound=None, colDiff=500, ground=False, highlight=False, colorify=0, otherfiles=False, felzScale=None, felzSigma=None, felzMinsize=None, webinterface=False):
    
    # set variables according to parameters passed down from main:
    complex_sizeX, complex_sizeY, stroke_density = setParameters(width, height, verbose, randSizes, longStrokes, strokeWidth, strokeHeight, strokeDensity)
    
    segmentsByIDlistNP = np.asarray(segmentsByIDlist) # only used by differenceToNeighbors()
    smallSegment_maxSize = segBound if segBound != None else (width * height) // 5000
    largeSegment_minSize = segBound if segBound != None else (width * height) // 5000  # increase constant for more complex strokes.
    if verbose:
        print("segBound: "+str(smallSegment_maxSize))
    
    # iterate over the segments from largest to smallest, paint the largest segments with complex brushstrokes, the smallest segments with simple brushstrokes, omit the middle-sized ones (all the segments were colored during segmentation anyway, so this saves time)
    
    smallestSegments = []
    smallSignificantSegments = []
    firstTimeUnderSmallSegmentMaxSize = True
    # density with which complex brushstrokes will be placed within their segments:
    
    for segment in range(0, len(segmentParams)):
        segmentID, regLine, angle, bboxN, degree, numOfPixels, regression = segmentParams[segment]
        if bboxN == None:
            continue
        
        regLineStart = (regLine[0][0], regLine[1][0])  # coordinates of the regression line starting point
        regLineStop = (regLine[0][-1], regLine[1][-1]) # coordinates of the regression line stopping point
        regLineLen = int(round(euclidDist(regLineStart, regLineStop)))
        minX, minY, maxX, maxY = bboxN  # the not-rotated bounding box
    
    
        #paint a simple brushstroke:
        if numOfPixels <= smallSegment_maxSize:
            simple_sizeY = max(1,regLineLen)  # we want the brush stroke to be the same length as the regression line of its segment
            simple_sizeX = max(1, numOfPixels // simple_sizeY)
            if simple_sizeX == 1 or simple_sizeY == 1: # hairline segment
                smallestSegments.append(segmentID)
            else:
                diffN = differenceToNeighbors(segmentID, segmentsByIDlistNP, inPix, minX, minY, maxX, maxY)
                if diffN >= colDiff:  # the color of this small segment is significantly different from the color of surrounding segments
                    X = regLine[0][0]
                    Y = regLine[1][0]
                    color = inPix[X, Y]
                    brushstroke.simple_brushstroke(outIm, X, Y, simple_sizeX, simple_sizeY, angle, color, regLine)
        
        # paint a complex brushstroke:
        elif numOfPixels > largeSegment_minSize:
            if ground and maxY > height * 0.9:
                groundSegment = True  # this is a large segment at the bottom of the image. We assume it's the ground.
            else:
                groundSegment = False
            
            if randSizes < 100:
                complex_sizeXrand, complex_sizeYrand, stroke_densityrand = randStrokesParams(randSizes, complex_sizeX, complex_sizeY, stroke_density)
                coordinates = getStrokePositions(segmentsByIDlist[segmentID], stroke_densityrand, minX, minY, maxX, maxY) # segmentsByIDlist to be replaced by segmentsByIDlist_sorted
            elif groundSegment:
                coordinates = getStrokePositions(segmentsByIDlist[segmentID], int(max(1, stroke_density * 0.4)), minX, minY, maxX, maxY)
            else:
                coordinates = getStrokePositions(segmentsByIDlist[segmentID], stroke_density, minX, minY, maxX, maxY) # segmentsByIDlist to be replaced by segmentsByIDlist_sorted
            
            if coordinates != None:
                if directedRotate:
                    angleStart = -1*int(angle) - 20
                    angleStop = angleStart + 40
                else:
                    angleStart = randint(-90, 90)
                    angleStop = angleStart + 40
                for posIndex in range(0, len(coordinates)):
                    X, Y = coordinates[posIndex]
                    # sample the colors where brushstroke is to be placed:
                    if randSizes < 100: # brush strokes are supposed to have random sizes
                        startColors, endColors = sampleStartEndColors(inPix, X, Y, width, height, complex_sizeXrand, complex_sizeYrand)
                        
                        # make every 5th brush stroke in otherwise homogenous regions look more vivid:
                        if highlight and posIndex % 5 == 4:
                            startColors, endColors = makeMoreVivid(startColors, endColors)
                        
                        brushstroke.complex_brushstroke(outIm, X, Y, complex_sizeXrand, complex_sizeYrand, startColors, endColors, angleStart, angleStop, arcType="log", groundSegment=groundSegment, colorify=colorify, noMargins=noMargins)
                    else:
                        startColors, endColors = sampleStartEndColors(inPix, X, Y, width, height, complex_sizeX, complex_sizeY)
                        
                        # make every 5th brush stroke in otherwise homogenous regions look more vivid:
                        if highlight and posIndex % 5 == 4:
                            startColors, endColors = makeMoreVivid(startColors, endColors)
                        
                        brushstroke.complex_brushstroke(outIm, X, Y, complex_sizeX, complex_sizeY, startColors, endColors, angleStart, angleStop, arcType="log", groundSegment=groundSegment, colorify=colorify, noMargins=noMargins)
    
    # now color in the smallest, hairline thin areas for which no brushstrokes could be generated:
    if not noHairlines:
        for segmentID in smallestSegments: # segmentsByIDlist to be replaced by segmentsByIDlist_sorted
            color = inPix[segmentsByIDlist[segmentID][0][0], segmentsByIDlist[segmentID][0][1]]
            for p in range(0, len(segmentsByIDlist[segmentID])):
                outPix[segmentsByIDlist[segmentID][p][0], segmentsByIDlist[segmentID][p][1]] = color
    
    if not webinterface:
        imgIO.savePixelAccessImg(outfile, outIm) # png


# data structures:
# in segmentsByIDlist_sorted, the segments are sorted by the number of pixels they contain from largest to smallest. Each element of the segmentsByIDlist_sorted list is a list of the form [segmentID, [list of pixel coordinates]]
# in segmentsByIDlist, the segmentID's are the list keys and the list of pixel coordinates for each segmentID is its value
def sortSegmentsBySize(segmentsByIDlist):
    listlen = len(segmentsByIDlist)
    sizes_and_IDs = [[] for i in range(0, listlen)] # list of [numOfPixels, segmentID]
    segmentsByIDlist_sorted = list(sizes_and_IDs) # list copy
    
    for i in range(0, listlen):
        sizes_and_IDs[i] = [len(segmentsByIDlist[i]), i]
    sizes_and_IDs.sort(reverse=True)  # sort inplace by first element (numOfPixels), descending
    
    for i in range(0, listlen):
        segmentsByIDlist_sorted[i] = [sizes_and_IDs[i][1], segmentsByIDlist[sizes_and_IDs[i][1]]]
    
    return segmentsByIDlist_sorted


def saturateImage(inIm, filename, saturation=2.5, otherfiles=False):
    converter = ImageEnhance.Color(inIm)
    saturatedIm = converter.enhance(saturation)
    saturatedPix = saturatedIm.load()
    if otherfiles:
        saturatedIm.save(filename + "_saturated.png")
    return saturatedIm, saturatedPix


# calling this function will start the 'afremize' process. The only obligatory argument is the input file name, 'infile'
def convertImage(infile, inIm=None, path="", input_dir="", output_dir="", verbose=False, strokeWidth=100, strokeHeight=100, randSizes=100, longStrokes=False, directedRotate=False, strokeDensity=70, background='blur', noHairlines=False, noMargins=False, segBound=100, colDiff=500, ground=False, saturation=2.5, highlight=False, colorify=0, otherfiles=False, felzScale=50, felzSigma=4.5, felzMinsize=10, webinterface=False):
    
    warnings.simplefilter('ignore', np.RankWarning) # ignore warnings when the polyfit function doesn't get enough data
    if inIm == None:
        inIm, inPix = imgIO.loadImgAsPixelAccess(path + input_dir + infile)
    else:
        inPix = inIm.load()
    width, height = inIm.size
    
    drawRegressionLines = otherfiles
    if drawRegressionLines:
        inImCopy = inIm.copy()
        inPixCopy = inImCopy.load()
    else:
        inImCopy = None
        inPixCopy = None
    
    filename, outfile = getOutfileName(path, output_dir, infile)
    outIm, outPix = imgIO.createWhiteImg(width, height)
    inIm, inPix = saturateImage(inIm, filename, saturation=saturation, otherfiles=otherfiles)
    inPixNP = np.array(inIm)
    
    segmentsNP, segmentsByIDlist = clustering(inPixNP, width, height, scale=felzScale, sigma=felzSigma, min_size=felzMinsize)
    if otherfiles:
        saveClusteredImage(inPix, segmentsByIDlist, width, height, filename) # optional
    
    segmentsByIDlist_sorted = sortSegmentsBySize(segmentsByIDlist) # sort the segments by their length, prepend regionID to each segment
    
    segmentParams = getSegmentParams(segmentsByIDlist_sorted, inPix, drawRegressionLines, inImCopy, inPixCopy, width, height)
    
    if drawRegressionLines:
        inImCopy.save(filename + "_regLines.png")
    
    outIm, outPix = colorBackground(inIm, inPix, segmentsByIDlist, outIm, outPix, background)
    
    
    paintImg_with_brushstrokes(outfile, outIm, outPix, width, height, segmentParams, segmentsByIDlist, inPix, verbose, randSizes=randSizes, longStrokes=longStrokes, directedRotate=directedRotate, strokeWidth=strokeWidth, strokeHeight=strokeHeight, strokeDensity=strokeDensity, noHairlines=noHairlines, noMargins=noMargins, segBound=segBound, colDiff=colDiff, ground=ground, highlight=highlight, colorify=colorify, otherfiles=otherfiles, felzScale=felzScale, felzSigma=felzSigma, felzMinsize=felzMinsize, webinterface=webinterface) # segmentsByIDlist to be replaced by segmentsByIDlist_sorted
    
    return outIm
