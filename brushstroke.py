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
from __future__ import print_function
import numpy as np
from PIL import Image
from scipy.interpolate import interp1d
from random import randint
import random
from math import log, floor, ceil, sin, cos, radians, sqrt
from skimage.segmentation import felzenszwalb

# own imports:
import imgIO


# returns an ndarray of offsets from the left margin of a brush stroke that form an arc
def createCosArc(sizeY, bulgeSize):
    if sizeY == 1:
        return np.zeros(1)
    if sizeY == 2:
        return np.zeros(2)
    startdegr = -90
    stopdegr = 90
    arc = np.zeros(sizeY)
    middle = sizeY // 2
    stepsize = max((abs(startdegr) + stopdegr) / sizeY, 0.00000001)
    degrees = np.zeros(sizeY) # degrees contains the x values, arc the correspnding cos(x) values
    degrees[0] = startdegr
    for i in range(1, len(degrees)):
        degrees[i] = degrees[i-1] + stepsize
    i = 0
    # degr is a value between 0 and 1 (between cos(startdegr) and cos(stopdegr))
    for degr in degrees:
        arc[i] = floor(cos(radians(degr)) * bulgeSize)
        i = i + 1
    return arc.astype(int)


# returns an ndarray of offsets from the left margin of a brush stroke that form an log curve-shaped arc
def createLogArc(sizeY, bulgeSize):
    if sizeY == 1:
        return np.zeros(1)
    if sizeY == 2:
        return np.zeros(2)
    arc = np.zeros(sizeY)
    stepsize = 10 / sizeY # we use values between log(1) and log(11)
    logparam = 1.1
    for i in range(len(arc)-1, -1, -1): # reverse values in arc to create stronger curvature at the bottom of the brush stroke
        arc[i] = log(logparam, 2)
        logparam = logparam + stepsize
    arcMax = max(arc)
    arcScale = bulgeSize / arcMax
    arc = arc * arcScale
    return arc.astype(int)


# for each given x value the corresponding value is computed (by interpolating from the given y values)
def createPolynomialCubic(x, y):
    shortx = np.linspace(0, len(x), num=len(y), endpoint=True) # because we cannot interpolate if x and y are not of the same length
    f = interp1d(shortx, y, kind='cubic') # perform cubic spline interpolation
    template = f(x)
    return template


def createPolynomialLinear(x, y):
    shortx = np.linspace(0, len(x), num=len(y), endpoint=True) # because we cannot interpolate if x and y are not of the same length
    f = interp1d(shortx, y) # perform linear spline interpolation
    template = f(x)
    return template


# create a random curve to use as template for cutting of parts of brush stroke
def buildCutoffTemplates(sizeX, sizeY):
    xtempl = range(0, sizeX)
    stop1 = max(1, int(sizeY*0.2))
    tmp1 = randint(int(sizeY*0.1), max(1, int(sizeY*0.3)))
    tmp2 = randint(int(sizeY*0.05), stop1)
    tmp3 = randint(int(sizeY*0.05), stop1)
    tmp4 = randint(int(sizeY*0.05), stop1)
    tmp5 = randint(int(sizeY*0.1), stop1)
    ytempl = [tmp1, tmp2, tmp3, tmp4, tmp5]
    upperTemplate = createPolynomialCubic(xtempl, ytempl)
    
    stop2 = max(1, int(sizeY*0.03))
    tmp1 = randint(int(sizeY*0.15), int(sizeY*0.2))
    tmp2 = randint(0, stop2)
    tmp3 = randint(0, stop2)
    tmp4 = randint(0, stop2)
    tmp5 = randint(0, stop2)
    tmp6 = randint(int(sizeY*0.15), int(sizeY*0.2))
    ytempl = [tmp1, tmp2, tmp3, tmp4, tmp5, tmp6]
    lowerTemplate = createPolynomialCubic(xtempl, ytempl)
    return abs(upperTemplate.astype(int)), abs(lowerTemplate.astype(int))



# This function is responsible for the faint hairlines along the length of the brush stroke
# It computes the RGBA values for one specific point y along the y-axis (the gradient along the y-axis starts with the color startColors_x at coordinate upperTemplate_x and ends with endColors_x at coordinate sizeY - lowerTemplate_x)
# gradientStart: offset from upper margin of brush stroke at which the color gradient starts
# gradientStop: offset from lower margin of brush stroke at which the color gradient stops
def computeYcolorGradient(y, sizeY, sizeYedge, startColors_x, endColors_x, gradientStart, gradientStop, whitenMargin, progressStop, RGBdists, A):
    
    if y < gradientStart:
        return startColors_x
    
    if whitenMargin:
        whiteMarginSize = max(3, sizeY // 30)
        blackMarginSize = max(1, whiteMarginSize // 10)
        if y >= (sizeYedge - blackMarginSize): # darken the edge
            darkenAmount = 50
            endColors_x_tmp  = np.array([0,0,0,255])
            for colIndex in range(0,len(endColors_x)-1):
                endColors_x_tmp[colIndex] = max(0, endColors_x[colIndex] - darkenAmount)
            return endColors_x_tmp
        if y > (sizeYedge - whiteMarginSize): # whiten the area directly above the edge
            whitenAmount = 50
            endColors_x_tmp  = np.array([0,0,0,255])
            for colIndex in range(0,len(endColors_x)-1):
                endColors_x_tmp[colIndex] = min(255, endColors_x[colIndex] + whitenAmount)
            return endColors_x_tmp
    
    if y > (sizeYedge - gradientStop):
        return endColors_x
    
    yprogress = (y - gradientStart) / progressStop  #(y - gradientStart) / (sizeYedge - gradientStop - gradientStart) # how far along the y-axis are we?
    RGBprogress = (RGBdists * yprogress).astype(int)
    RGB = startColors_x - RGBprogress
    
    return RGB[0], RGB[1], RGB[2], A



# create a vector 'colors' of length sizeXedge of RGBA values with smooth color transitions (unlike in the original color vector 'seed')
def interpolateColors(seed, sizeXedge):
    # from the given startColors, create a linear polynomial to smooth color transitions along x-axis:
    # we'll use linear interpolation because cubic interpolation needs at least 4 entries
    colorsR = createPolynomialLinear(range(0, sizeXedge), seed[:,0]).astype(int)
    colorsR = np.expand_dims(colorsR, 1) # transform array of shape (sizeXedge,) to (sizeXedge, 1)
    colorsG = createPolynomialLinear(range(0, sizeXedge), seed[:,1]).astype(int)
    colorsG = np.expand_dims(colorsG, 1)
    colorsB = createPolynomialLinear(range(0, sizeXedge), seed[:,2]).astype(int)
    colorsB = np.expand_dims(colorsB, 1)
    colorsA = np.zeros([sizeXedge, 1], dtype=int)
    colorsA = colorsA + 255
    # now put the color channels back together:
    colors = np.append(colorsR, colorsG, axis=1)
    colors = np.append(colors, colorsB, axis=1)
    colors = np.append(colors, colorsA, axis=1)
    return colors


def getStreakGradientPoints(streakWidth, streakWidthMin, streakWidthMax, gradientStart, gradientStop, sizeYedge):
    if streakWidth == 0:
        gradientStart = randint(0, (4*sizeYedge)//5) # distance from upper margin at which gradient starts
        gradientStop = 0 # distance from lower margin at which gradient stops
        streakWidth = streakWidth + 1
    # we have either not yet reached streakWidthMin or we just continue to enlarge streak just by chance:
    elif streakWidth < streakWidthMin or random.choice([True, False]):
        # increase by 1, descrease by 1 or do not change:
        gradientStart = min(255,max(0, gradientStart - random.choice([-2,0,2])))
        gradientStop = min(255,max(0, gradientStop - random.choice([-2,0,2])))
        if (gradientStart + gradientStop) == sizeYedge:
            gradientStart = max(gradientStart - 1, 0)
            gradientStop = max(gradientStop - 1, 0)
        streakWidth = streakWidth + 1
    else: # this is responsible for the thin long streaks with width 1 between the broader streaks:
        gradientStart = randint(0, (4*sizeYedge)//5)
        gradientStop = 0
        streakWidth = 0
        streakWidthMin = randint(1, max(1,streakWidthMax))
    
    # to not group the hairlines into streaks, uncomment the following two lines:
    #gradientStart = randint(0, sizeYedge-1)
    #gradientStop = randint(0, sizeYedge-1-gradientStart)
    return gradientStart, gradientStop, streakWidth, streakWidthMin


# startColors is a numpy array of shape (x,4) containing x many RGBA values to use from the top of the brush stroke
def complex_brushstroke(outIm, X, Y, sizeX, sizeY, startColors, endColors, angleStart=-60, angleStop=10, arcType='log', groundSegment=False, colorify=0, noMargins=False):
    
    if colorify > 0:
        for i in range(0, len(startColors)):
            maxChannel = startColors[i].argmax()
            if random.choice([True, False]):
                startColors[i][maxChannel] = min(255, startColors[i][maxChannel] + colorify)
            else:
                startColors[i][maxChannel] = max(0, startColors[i][maxChannel] - colorify)
        for i in range(0, len(endColors)):
            maxChannel = startColors[i].argmax()
            if random.choice([True, False]):
                endColors[i][maxChannel] = min(255, endColors[i][maxChannel] + colorify)
            else:
                endColors[i][maxChannel] = max(0, endColors[i][maxChannel] - colorify)
            
    
    if groundSegment:
        sizeX = max(1, int(sizeX * 0.4))
        sizeY = max(1, int(sizeY * 2))
        angle = randint(80,100)
        capSize = randint(int(sizeX * 0.3), int(sizeX * 0.5))
        upperTemplate, lowerTemplate = build_simple_CutoffTemplates(sizeX, capSize)
        bulgeSize = int(sizeX * (3/5))
        if arcType == "cos":
            bulgeSize = int(sizeX * (2/5))
        whitenMargin = False
    else:
        angle = randint(angleStart, angleStop)  # rotate each brushstroke clockwise by -10 to 60 degrees
        upperTemplate, lowerTemplate = buildCutoffTemplates(sizeX, sizeY)
        bulgeSize = int(sizeX * (2/5))
        if arcType == "cos":
            bulgeSize = int(sizeX * (1/5))
        if noMargins:
            whitenMargin = False
        else:
            whitenMargin = random.choice([True, False])
    
    # need to subtract bulgeSize//2 from sizeXedge to make brush strokes narrower because the polynomial template cutoffs (cutting of from top and bottom) make them wider. Subtracting the stroke width by bulgeSize instead of bulgeSize//2 would make the strokes too narrow.
    strokeim, strokepix = imgIO.createTransparentImg(sizeX + int(ceil(bulgeSize/2)), sizeY)
    sizeXedge = sizeX - bulgeSize//2 # the number of pixels along the x-axis that will actually be colored in
    
    startColors = interpolateColors(startColors, sizeXedge) # from startColors, create a vector of length sizeXedge of RGBA values with smooth color transitions (unlike in the original startColors)
    endColors = interpolateColors(endColors, sizeXedge)
    
    if arcType == "log":
        arc = createLogArc(sizeY, bulgeSize)
    elif arcType == "cos":
        arc = createCosArc(sizeY, bulgeSize)
    arcLen = len(arc)
    
    # group hairlines into color streaks (smudges) along the brush stroke length:
    streakWidthMax = sizeXedge // 4
    streakWidthMin = randint(1, max(1,streakWidthMax))
    streakWidth = 0
    sizeYedge = sizeY - upperTemplate[0] - lowerTemplate[0]
    gradientStart = randint(sizeYedge//3, max(1,sizeYedge//2 -1)) # distance from upper margin at which gradient starts
    gradientStop = 0
    
    for x in range(0, sizeXedge):
        sizeYedge = sizeY - upperTemplate[x] - lowerTemplate[x] # y-size of the visible portion of brush stroke
        
        gradientStart, gradientStop, streakWidth, streakWidthMin = getStreakGradientPoints(streakWidth, streakWidthMin, streakWidthMax, gradientStart, gradientStop, sizeYedge)
        
        if sizeYedge == 1:
            strokepix[x + arc[0], 0] = (startColors[0][0], startColors[0][1], startColors[0][2], 255)
        else:
            progressStop = sizeYedge - gradientStop - gradientStart # size of range for which color gradient is computed. The rest uses constant colors.
            
            RGBdists = startColors[x] - endColors[x]  # color distances between start and end colors. This is sort of a gradient maximum. With this, and the spatial distance from a startColor pixel, we can compute the gradient for any y value between upperTemplate[x] (startColors) and sizeYedge (endColors).
            A = 255
            
            for y in range(upperTemplate[x], sizeYedge):
                # if we are below the area our upperTemplate tells us not to paint and above the area lowerTemplate tells us not to paint:
                
                # compute color gradient along y-axis (highly variable gradientStart and gradientStop values cause color streaks along the length of the brush stroke):
                R, G, B, A = computeYcolorGradient(y, sizeY, sizeYedge, startColors[x], endColors[x], gradientStart, gradientStop, whitenMargin, progressStop, RGBdists, A)
                strokepix[x + arc[y], y] = (R, G, B, A)
    
    strokeim = strokeim.rotate(angle, resample=Image.BICUBIC, expand=True)
    strokeim_bbox = strokeim.getbbox()
    strokeim = strokeim.crop(strokeim_bbox) # crop away unnecessary empty margins caused by rotation

    strokeimWidth, strokeimHeight = strokeim.size
    xMidpoint = int(round(strokeimWidth / 2))
    yMidpoint = int(round(strokeimHeight / 2))
    
    outIm.paste(strokeim, (X - xMidpoint, Y - yMidpoint), strokeim)
    del strokepix
    del strokeim



# create a simple arc shaped curve based on the cos function
def build_simple_CutoffTemplates(sizeX, capSize):
    upperTemplate = createCosArc(sizeX, capSize)
    # we want the ends of upperTemplate to contain the highest values:
    upperTemplate = [abs(int(capSize - upperTemplate[i])) for i in range(0, len(upperTemplate))]
    lowerTemplate = upperTemplate
    return upperTemplate, lowerTemplate


def euclidDist(p1, p2):
    return sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)


# this function computes the normed normal vector of a line defined by the two points start, end (which are tuples of the point coordinates), as well as the distance of this line from origin (0,0)
def getLineVectors(start, end):
    v = (end[0] - start[0], end[1] - start[1]) # vector between end points of regLine
    n = (-v[1], v[0])
    n_normed = (n[0] / np.linalg.norm(n), n[1] / np.linalg.norm(n)) # normed normal vector
    if (start[0] * n[0] + start[1] * n[1]) >= 0:
        n_normed = (n[0] / np.linalg.norm(n), n[1] / np.linalg.norm(n)) # normed normal vector
    else:
        n_normed = (-n[0] / np.linalg.norm(n), -n[1] / np.linalg.norm(n)) # normed normal vector
    distLineOrigin = start[0] * n_normed[0] + start[1] * n_normed[1]  # offset der Geraden vom Ursprung
    return n_normed, distLineOrigin


# this function computes the distance between the point pnt and a line defined by its normed normal vector and its distance from origin
def pointLineDist(pnt, n_normed, distLineOrigin):
    dist = abs((pnt[0] * n_normed[0] + pnt[1] * n_normed[1]) - distLineOrigin)
    return dist


def create_arc_from_regLine(regLine):
    # The regression line regLine contains all x coordinates in its first element (a list) and all y coordinates in its second element (also a list).
    # First, we create the line equation r for the line defined by the start point and the end point of regLine, and its normal vector normal_vec
    # For each point P in regLine, we compute the line equation for the normal line n (n is the line defined by the normal vector of r which crosses P) and the cross_section of the lines n and r. This cross-section is also the point on line r which is closest to the point P.
    # The array 'arc' returned by this function contains the Euclidean distance between each point P and its corresponding point cross_section.
    # While regLine describes the curvature of a segment at its position in the input image, arc describes the curvature as a set of distances of each point in regLine from a straight line connecting the end points of regLine.
    regLineLen = len(regLine[0])
    arc = [[] for i in range(0, regLineLen)]
    start = (regLine[0][0], regLine[1][0])
    end = (regLine[0][-1], regLine[1][-1])

    n_normed, distLineOrigin = getLineVectors(start, end)
    for p in range(0, regLineLen):
        arc[p] = int(pointLineDist((regLine[0][p], regLine[1][p]), n_normed, distLineOrigin))
    
    # if regLine's midpoint is to the left of the line connecting its endpoints, we need to flip arc values:
    lineMidpoint_y = (start[1] + end[1]) / 2
    
    posSlope = regLine[1][0] > regLine[1][-1] # line connecting regLine endpoints has positive slope
    midPointAbove = regLine[1][int(len(regLine[1]) / 2)] < lineMidpoint_y
    
    if (not posSlope) and (not midPointAbove):
        maxarc = max(arc)
        for i in range(0, len(arc)):
            arc[i] = maxarc - arc[i]
    
    if posSlope and midPointAbove:
        maxarc = max(arc)
        reversed_arc = [[] for i in range(0, regLineLen)]
        tmp_reversed_arc= [[] for i in range(0, regLineLen)]
        for i in range(0, len(arc)):
            reversed_arc[regLineLen - i - 1] = maxarc - arc[i]
        return reversed_arc
    return arc


    
def findMarkerPixel(markerColor, strokepixTmp, width, height):
    brushStart = [0,0]
    R,G,B,A = markerColor
    dists = []
    for x in range(0, width):
        for y in range(0, height):
            
            if strokepixTmp[x, y] != (0,0,0,0) and abs(strokepixTmp[x, y][0] - R) < 200 and abs(strokepixTmp[x, y][1] - G) < 200 and abs(strokepixTmp[x, y][2] - B) < 200 and abs(strokepixTmp[x, y][3] - A) < 200:
            
                dists.append([abs(strokepixTmp[x, y][0] - R) + abs(strokepixTmp[x, y][1] - G) + abs(strokepixTmp[x, y][2] - B) + abs(strokepixTmp[x, y][3] - A), [x, y]])
    
    if dists != []:
        brushStartDist = dists[0][0]
        brushStart = dists[0][1]
        for i in range(0, len(dists)):
            if dists[i][0] < brushStartDist:
                brushStartDist = dists[i][0]
                brushStart = dists[i][1]
    else:
        return False
    return brushStart



def getBrushStart(template_midpoint, strokeim, angle, color):
    # mark the starting point of the brush stroke in the brush stroke image:
    strokeimTmp = strokeim.copy()
    strokepixTmp = strokeimTmp.load()
    
    R = 0 if color[0] > 128 else 255
    G = 0 if color[1] > 128 else 255
    B = 0 if color[2] > 128 else 255
    markerColor = (R, G, B, 255)  # let markerColor be as different from segment color as possible so that we can find it again after the rotation
    strokepixTmp[template_midpoint[0], template_midpoint[1]] = markerColor # we mark the pixel that needs to coincide with regLine start to find it again after rotation
    width, height = strokeimTmp.size
    imgMidpoint = [width // 2, height // 2]
    distMarkerMidpoint = euclidDist(template_midpoint, [imgMidpoint[0], imgMidpoint[1]])  # distance between marker pixel and brushstroke image midpoint
    
    # rotate brush stroke image
    strokeimTmp = strokeimTmp.rotate(360 - angle, resample=Image.BICUBIC, expand=True)            
    strokeimTmp_bbox = strokeimTmp.getbbox() # because after rotating, there will be big empty areas around the segment
    strokeimTmp = strokeimTmp.crop(strokeimTmp_bbox)
    strokepixTmp = strokeimTmp.load() # reload the pixelAccess object after rotating the image
    widthRot, heightRot = strokeimTmp.size
    
    # find the starting point of the brush stroke in the rotated image:
    brushStart = findMarkerPixel(markerColor, strokepixTmp, widthRot, heightRot)
    
    # if brushstart pixel was not found, compute it trigonometrically (less precise):
    # imgMidpoint = center point of the brushstroke image rotation
    # template_midpoint = brushStart coordinates before rotation
    # [x_tmp, y_tmp] = brushStart coordinates after rotation
    # Pbetw_midpoint_and_marker = point halfway between imgMidpoint and template_midpoint
    # markerMovement = distance between template_midpoint and [x_tmp, y_tmp]
    if not brushStart:
        # law of cosines (Kosinussatz): c^2 = a^2 + b^2 - 2ab*cos(gamma)
        markerMovement = sqrt(2*(distMarkerMidpoint**2) + 2 * distMarkerMidpoint * distMarkerMidpoint * cos(radians(abs(angle))))
        if markerMovement > 0:
            Pbetw_midpoint_and_marker = [min(imgMidpoint[0], template_midpoint[0]) + (abs(imgMidpoint[0] - template_midpoint[0]) // 2), min(imgMidpoint[1], template_midpoint[1]) + (abs(imgMidpoint[1] - template_midpoint[1]) // 2)]
            
            h = sqrt(distMarkerMidpoint**2 - euclidDist(imgMidpoint, Pbetw_midpoint_and_marker)**2)
            
            if angle <= 0:
                x_tmp = int(Pbetw_midpoint_and_marker[0] + ((h * ( template_midpoint[1] - imgMidpoint[1] )) / distMarkerMidpoint))
                y_tmp = int(Pbetw_midpoint_and_marker[1] - ((h * ( template_midpoint[0] - imgMidpoint[0] )) / distMarkerMidpoint))
            else:
                x_tmp = int(Pbetw_midpoint_and_marker[0] - ((h * ( template_midpoint[1] - imgMidpoint[1] )) / distMarkerMidpoint))
                y_tmp = int(Pbetw_midpoint_and_marker[1] + ((h * ( template_midpoint[0] - imgMidpoint[0] )) / distMarkerMidpoint))
            return [x_tmp, y_tmp]
        if markerMovement == 0:
            return template_midpoint # probably angle was close to 0
    else:
        return brushStart
    
    return [0,0]


# make arc look a bit less computer-generated and a bit more hand-drawn
def randomizeArc(arc):
    offset = 0
    hysterese = 0
    hystereseMax = randint(0, int(len(arc) * 0.01))
    hystereseMax_before_plateau = hystereseMax
    hystereseMaxRoof = int(len(arc) * 0.01)
    modus = 2  # 0: offset increase, 1: offset descrease, 2: plateau
    modus_before_plateau = 0
    for i in range(0, len(arc)):
        if hysterese >= hystereseMax:
            if modus == 0 or modus == 1: # we are just entering a plateau
                modus_before_plateau = modus
                modus = 2
                hystereseMax_before_plateau = hystereseMax
                randIncr = int(len(arc) * 0.01)
                if random.choice([True, False]):
                    hystereseMax = min(hystereseMaxRoof, randint(hystereseMax_before_plateau, hystereseMax_before_plateau + randIncr))
                else:
                    hystereseMax = min(hystereseMaxRoof, max(0, randint(hystereseMax_before_plateau - randIncr, hystereseMax_before_plateau)))
            else: # we are coming down from a plateau
                if modus_before_plateau == 0:
                    modus = 1
                else:
                    modus = 0
                randIncr = int(len(arc) * 0.01)
                if random.choice([True, False]):
                    hystereseMax = min(hystereseMaxRoof, randint(hystereseMax_before_plateau, hystereseMax_before_plateau + randIncr))
                else:
                    hystereseMax = min(hystereseMaxRoof,max(0, randint(hystereseMax_before_plateau - randIncr, hystereseMax_before_plateau)))
            hysterese = 0
        if modus == 0 and randint(0,5) == 0:
            offset += 1
        elif modus == 1 and randint(0,5) == 0:
            offset -= 1
        arc[i] = max(0, arc[i] + offset)
        hysterese += 1
    return arc



# startColors is a numpy array of shape (x,4) containing x many RGBA values to use from the top of the brush stroke
#  X, Y are the coordinates of the pixel where the center of the simple brushstroke is about to be placed
# capSize is the distance between the brush stroke cap apex and closest point in the brushstroke which has maximal width (the caps being the rounded ends of a brush stroke)
# unlike in complex_brushstroke(), sizeX has the same value as sizeXedge would
def simple_brushstroke(outIm, X, Y, sizeX, sizeY, angle, color, regLine):
    if sizeX > 1 and sizeY > 1:  # because computing a curved brush strokes for these small sizes fails (no curvature for width 1) and painting a line of with 1 looks ugly
        capSize = randint(int(sizeX * 0.3), int(sizeX * 0.5))
        bulgeSize = int(sizeX * 0.75)
        
        arc = create_arc_from_regLine(regLine)
        arc = randomizeArc(arc)
        sizeY = len(arc)
        if sizeY <= 1:
            return
        
        strokeim, strokepix = imgIO.createTransparentImg(sizeX + max(arc) + 1, sizeY)
        upperTemplate, lowerTemplate = build_simple_CutoffTemplates(sizeX, capSize)
        
        for x in range(0, sizeX):
            for y in range(0, sizeY):
                # if we are below the area our upperTemplate tells us not to paint and above the area lowerTemplate tells us not to paint:
                if y >= upperTemplate[x] and y <= (sizeY - lowerTemplate[x]):
                    strokepix[x + arc[y], y] = (color[0], color[1], color[2], 255)
        
        if angle < 0:
            template_midpoint = ((sizeX//2) + arc[0], upperTemplate[sizeX//2])  # len(upperTemplate) = sizeX
        elif angle > 0:
            template_midpoint = ((sizeX//2) + arc[-1], sizeY - max(1, lowerTemplate[sizeX//2]))  # len(upperTemplate) = sizeX
        else:  # angle == 0
            template_midpoint = ((sizeX//2) + arc[0], upperTemplate[sizeX//2])
            brushStart = template_midpoint
        if angle != 0:
            brushStart = getBrushStart(template_midpoint, strokeim, angle, color)  # get the coordinates of the brush stroke apex within the brushstroke image. These have to be subtracted from the X,Y position where the upper left corner of the brushstroke image should be pasted into the resulting image outIm
        
        # angle sais by how many degrees we need to rotate a segment to make it upright, so we need 360-angle here to revert it again
        strokeim = strokeim.rotate(360 - angle, resample=Image.BICUBIC, expand=True)
        strokeim_bbox = strokeim.getbbox() # because after rotating, there will be big empty areas around the segment
        strokeim = strokeim.crop(strokeim_bbox)
        strokepix = strokeim.load() # reload the pixelAccess object after rotating the image
        
        # now we paste the generated brush stroke so that the start of the regression line has the same coordinates as the start of the brush stroke (e.g. the midpoint of its left cap)
        outIm.paste(strokeim, (X - brushStart[0], Y - brushStart[1]), strokeim)
