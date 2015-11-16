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

from PIL import Image, ImageDraw

# converts the pixel access object pic into a numpy array
def pixelAccessToNumpy(pixelAccess):
    return numpy.array(pixelAccess)


# converts the numpy array nparray into a pixel access object. not working
def numpyToPixelAccess(nparray):
    im = Image.fromarray(nparray)
    pix = im.load()
    return 


# returns an image object. Problem: this actually doesn't work
#def numpyToImage(nparray):
    #return Image.fromarray(nparray)


# loads picture filename and returns its pixel access object
def loadImgAsPixelAccess(filename):
    im = Image.open(filename)
    #draw = ImageDraw.Draw(im)
    return [im, im.load()]


def saveNPimg(outfile, ndarray):
    imsave(outfile, ndarray)


# im is what the Image.open() function returned
def savePixelAccessImg(outfile, im):
    im.save(outfile)


# creates and returns a white image and it pixel access object
# each color value of the pixel access object will be (255, 255, 255, 255)
def createWhiteImg(width, height):
    im = Image.new("RGBA", (width, height), "white")
    pix = im.load()
    return [im, pix]


# creates and returns a transparent image and it pixel access object
# each color value of the pixel access object will be (0, 0, 0, 0)
def createTransparentImg(width, height):
    im = Image.new("RGBA", (width, height))
    pix = im.load()
    return [im, pix]
