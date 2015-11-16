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


# This implementation was tested with Python 2.7.9 :: Anaconda 2.2.0 (64-bit)
# and partly with Python 2.7.10 :: Anaconda 2.3.0 (64-bit)

import os
from optparse import OptionParser

# own imports:
import afremize


if __name__ == "__main__":
    
    parser = OptionParser()
    parser.add_option("-f", "--file", dest="infile",
                      help="Name of the input image to convert. If not specified, all images in the 'input_images' directory will be converted and moved to the 'input_done' directory. The output file name will be created by appending '__out' to the input file name. If a file with an appended '__out' already exists, it will NOT be overwritten, instead, one additional '__out' will be appended to the new filename.", metavar="FILE")
    parser.add_option("-v", "--verbose",
                      action="store_true", dest="verbose", default=False,
                      help="Print status messages and parameter values to stdout. [default: %default]")
    
    parser.add_option("-b", "--background",
                      dest="background", default='cluster',
                      help="Choose which kind of background should be used for the output image: the blurred input image, colored Felzenszwalb clusters, or no background at all. background: blur, cluster, none [default: %default]")
    parser.add_option("-S", "--saturation",
                      dest="saturation", default=2.5,
                      help="Saturation level of the output image. A value of 1.0 would mean no saturation level adjustment. [default: %default]")
    parser.add_option("-g", "--ground",
                      action="store_true", dest="ground", default=False,
                      help="If set, program will try to identify segments comprising the ground in the input image (fallen leaves, a road, dirt...) and paint them with long, multicolored brush strokes. [default: %default]")
    
    parser.add_option("-L", "--noHairlines",
                      action="store_true",  dest="noHairlines", default=False,
                      help="If set, the fine outlines of objects (with either height or width of 1 pixel) will not be painted. Omitting them makes the picture look smoother, although sometimes too many details will be lost. [default: %default]")
    parser.add_option("-M", "--noMargins",
                      action="store_true",  dest="noMargins", default=False,
                      help="If set, the lower edges of complex brush strokes will NOT be whitened to simulate a 3D color buildup. [default: %default]")
    parser.add_option("-s", "--randSizes",
                      dest="randSizes", default=100,
                      help="If set to a value below 100 (30 produces nice results), the multicolored brush strokes in image will have random sizes, the upper bound of their width being strokeWidth, and the lower bound being (upper bound * randSizes // 100). If set to 100, all multicolored brush strokes will have the same size, STROKEWIDTH. [default: %default]")
    parser.add_option("-l", "--longStrokes",
                      action="store_true", dest="longStrokes", default=False,
                      help="If set, the width:height ratio of multicolored brush strokes will be (STROKEWIDTH*0.7) : (STROKEWIDTH*1.3) (long strokes). The height may be smaller if the segment's bounding box is more quadratic than longitudinal. If not set, the ratio will be STROKEWIDTH:STROKEWIDTH (quadratic strokes). Setting this option doubles the runtime. [default: %default]")
    parser.add_option("-d", "--directed",
                      action="store_true", dest="directedRotate", default=False,
                      help="If set, the orientation of the multicolored brush strokes will depend on their segments' orientation. If not set, multicolored strokes will have a random orientation. [default: %default]")
    
    parser.add_option("-W", "--width",
                      dest="strokeWidth",
                      help="Width of each multicolored brush stroke, in pixels. See also --longStrokes and --randSizes. [default: around 2% of the circumference of the image]")
    parser.add_option("-H", "--height",
                      dest="strokeHeight",
                      help="Height of each multicolored brush stroke, in pixels. See also --longStrokes and --randSizes. [default: around 2% of the circumference of the image]")
    parser.add_option("-D", "--density",
                      dest="strokeDensity",
                      help="Length of the intervals (in pixels) at which multicolored brush strokes should be placed. Increase this value if brush strokes appear to be too regularly placed or there are too few of them. If STROKEWIDTH or STROKEHEIGHT is set manually (or set to be random), the program will try to find the best corresponding density. However, you can also set density manually. Note that increasing density can drastically increase the runtime of the program. [default: around 0.5% of the circumference of the image]")
    parser.add_option("-B", "--segBound",
                      dest="segBound",
                      help="This value corresponds to the maximum number of pixels a segment must have to be classified as a small segment (for simple, single-colored brush strokes), and also to the minimum value (when increased by 1) a segment must have to be classified as a large segment (for multicolored, multi-colored brush strokes). Decrease segBound if you want to see more multicolored brush strokes and less details. [default: (image_width * image_height) / 5000]")
    parser.add_option("-C", "--smallSeg", "--colDiff",
                      dest="colDiff", default=500,
                      help="Minimum amount of color difference a small segment must have from its surrounding regions in order for the small segment to be painted at all, with a simple brush stroke. If the color difference of a segment is lower than the smallSeg value, the small segment will not be painted at all. Increase this value is there are too many simple brushstrokes (thin, curved lines) cluttering the image. Decrease if there are not enough details visible. A value of 3060 will make all simple brush strokes (and as a consequence, all small segments except for the hairlines) disappear from the resulting image. Values in range: 0..3060. [default: %default]")
    parser.add_option("--highlight",
                      action="store_true", dest="highlight", default=False,
                      help="If set, every 5th stroke in regions that would otherwise look very homogenous will get a slightly brighter color. If not set, no additional color manipulation will be performed on the colors sampled for the multicolored brush strokes. [default: %default]")
    parser.add_option("--colorify",
                      dest="colorify", default=0,
                      help="Sets the amount by which the most prominent color channels in each multicolored brush stroke will be intensified. Too high values have a rather kitschy effect. Values in range 0..255 [default: %default]")
    parser.add_option("--otherfiles",
                      action="store_true", dest="otherfiles", default=False,
                      help="If set, the program will create additional files that help the user understand the intermediate stages of creating the resulting image. The file 'FILE_clustered.png' visualizes the detected Felzenszwalb clusters using their actual colors. The file 'FILE_clustered_randomColor.png' visualizes the detected Felzenszwalb clusters using random colors. The file 'FILE_regLines.png' shows the quadratic regression lines for each Felzenszwalb segment. The file 'FILE_saturated.png' shows the level of saturation used for the output image. [default: %default]")
    parser.add_option("--felzScale",
                      dest="felzScale", default=50,
                      help="The first parameter ('scale') for the Felzenszwalb clustering. Description: Free parameter. Higher means larger clusters. [default: %default]")
    parser.add_option("--felzSigma",
                      dest="felzSigma", default=4.5,
                      help="The second parameter ('sigma') for the Felzenszwalb clustering. Description: Width of Gaussian kernel used in preprocessing. [default: %default]")
    parser.add_option("--felzMinsize",
                      dest="felzMinsize", default=10,
                      help="The third parameter ('min_size') for the Felzenszwalb clustering. Description: Minimum component size. Enforced using postprocessing. [default: %default]")
    
    (options, args) = parser.parse_args()
    
    
    infile              = options.infile
    verbose             = options.verbose
    background          = options.background
    saturation          = float(options.saturation)
    ground              = options.ground
    noHairlines         = options.noHairlines
    noMargins           = options.noMargins
    randSizes           = min(100, max(1, int(options.randSizes)))
    longStrokes         = options.longStrokes
    directedRotate      = options.directedRotate
    strokeWidth         = None if options.strokeWidth == None else int(options.strokeWidth)
    strokeHeight        = None if options.strokeHeight == None else int(options.strokeHeight)
    strokeDensity       = None if options.strokeDensity == None else int(options.strokeDensity)
    segBound            = None if options.segBound == None else int(options.segBound)
    colDiff             = int(options.colDiff)
    highlight           = options.highlight
    colorify            = int(options.colorify)
    otherfiles          = options.otherfiles
    felzScale           = int(float(options.felzScale))
    felzSigma           = float(options.felzSigma)
    felzMinsize         = int(float(options.felzMinsize))
    
    if options.infile == None:
        infile = None
        #infile = "pics/autumn/autumn.jpg"
        #infile = "pics/autumn/fog/autumn.jpg"
        #infile = "pics/Denisa/Deniska.jpg"
        #infile = "pics/Garten/Garten.bmp" #segmentID 12
        #infile = "pics/Garten_600x333.png"
        #infile = "pics/Halbauer_Weg/Halbauer_Weg.jpg"
        #infile = "pics/Haus/Haus.jpg"
        #infile = "pics/lena/lena.bmp"
        #infile = "pics/lena_50x50/lena_50x50.png"
        #infile = "pics/Lenocka.jpg"
        #infile = "pics/Lenocka/Lenocka_retouched_small.png"
        #infile = "pics/lines.bmp"
        #infile = "pics/lines2.bmp"
        #infile = "pics/Nico/Nico.jpg"
        #infile = "pics/Nico/Nico_2520x1800.jpg"
        #infile = "pics/Nico/Nico_600x429.jpg"
        #infile = "pics/red_bench/red_bench.jpg"
        #infile = "pics/big/red_ground_huge.jpg"
        #infile = "pics/Rote_Blaetter/Rote_Blaetter.jpg"
        #infile = "pics/Ruska_zoznamka/Ruska_zoznamka.jpg"
        #infile = "pics/Teufelssee/Teufelssee_Grass.jpg"
        #infile = "pics/Teufelssee/Teufelssee_Mensch.jpg"
        #infile = "pics/Twilight/Twilight.jpg"
        #infile = "pics/Tanne/Tanne.jpg"
        #infile = "pics/Trunks/Trunks.jpg"
        #infile = "pics/Weisse_Baumstaemme/Weisse_Baumstaemme.jpg"
        #infile = "pics/white_blanket/white_blanket.jpg"
    
    if verbose:
        print("Starting Afremize with the options:\n"
              +"\nverbose: "+str(verbose)
              +"\nbackground: "+str(background)
              +"\nsaturation: "+str(saturation)
              +"\nground: "+str(ground)
              +"\nnoHairlines: "+str(noHairlines)
              +"\nnoMargins: "+str(noMargins)
              +"\nhighlight: "+str(highlight)
              +"\ncolorify: "+str(colorify)
              +"\nrandSizes: "+str(randSizes)
              +"\nlongStrokes: "+str(longStrokes)
              +"\ndirected: "+str(directedRotate)
              +"\notherfiles: "+str(otherfiles)
              +"\ncolDiff: "+str(colDiff)
              +"\nfelzScale: "+str(felzScale)
              +"\nfelzSigma: "+str(felzSigma)
              +"\nfelzMinsize: "+str(felzMinsize))
    
    
    if infile == None:
        path = ""
        input_dir = "input_images/"
        output_dir = "output_images/"
        input_done = "input_done/"
        
        if not os.path.isdir(path + input_dir):
            os.makedirs(path + input_dir)
        if not os.path.isdir(path + output_dir):
            os.makedirs(path + output_dir)
        if not os.path.isdir(path + input_done):
            os.makedirs(path + input_done)
    
        for infile in os.listdir(path + "input_images/"):
        
            print("\nconverting file: "+ str(infile))
            afremize.convertImage(
                infile,
                path=path,
                input_dir=input_dir,
                output_dir=output_dir,
                verbose=verbose,
                strokeWidth=strokeWidth,
                strokeHeight=strokeHeight,
                randSizes=randSizes,
                longStrokes=longStrokes,
                directedRotate=directedRotate,
                strokeDensity=strokeDensity,
                background=background,
                noHairlines=noHairlines,
                noMargins=noMargins,
                segBound=segBound,
                colDiff=colDiff,
                saturation=saturation,
                ground=ground,
                highlight=highlight,
                colorify=colorify,
                otherfiles=otherfiles,
                felzScale=felzScale,
                felzSigma=felzSigma,
                felzMinsize=felzMinsize
                )
            os.rename(path + input_dir + infile, path + input_done + infile)
    else:
        path = ""
        input_dir = ""
        output_dir = ""
        input_done = ""
        
        print("\nconverting file: "+ str(infile))
        afremize.convertImage(
            infile,
            path=path,
            input_dir=input_dir,
            output_dir=output_dir,
            verbose=verbose,
            strokeWidth=strokeWidth,
            strokeHeight=strokeHeight,
            randSizes=randSizes,
            longStrokes=longStrokes,
            directedRotate=directedRotate,
            strokeDensity=strokeDensity,
            background=background,
            noHairlines=noHairlines,
            noMargins=noMargins,
            segBound=segBound,
            colDiff=colDiff,
            saturation=saturation,
            ground=ground,
            highlight=highlight,
            colorify=colorify,
            otherfiles=otherfiles,
            felzScale=felzScale,
            felzSigma=felzSigma,
            felzMinsize=felzMinsize
            )
    if infile == None:
        print("Please specify at least one input file. Example:\npython main.py -f 'name_of_input_image.png'")
