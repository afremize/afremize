# afremize

## ABOUT

'Afremize' is an implementation of the algorithm I proposed in my Computer Science bachelor thesis with the title

#### 'Maschinelles Generieren von impressionistischen Bildern im Stil von Leonid Afremov'
#### ('Machine-Generating of impressionist, Leonid Afremov-style paintings').
 
The thesis was inspired by the beautiful work of the impressionist painter Leonid Afremov. Check out his website:               
<http:www.afremov.com>


##  SYSTEM REQUIREMENTS

This Afremize implementation has been tested on Linux, using the Python distribution 'Anaconda':

Python 2.7.9 :: Anaconda 2.2.0 (64-bit)

Download link:

<http://continuum.io/downloads>
 - please choose the "Linux 64-Bit — Python 2.7" version

Anaconda can be installed and used in parallel with other Python distributions.
During installation, you will be asked whether to add Anaconda to your $PATH. If you're unsure what this means, answer with yes (this can be changed at a later time).

Your system should have at least 1.5 GB RAM available in order to convert a 2700x1500 picture.



##  USAGE

To start the program, open a Terminal window, navigate to the directory with the python source files and type in:


    python main.py -f "path/to/input_picture.png"


Currently, only RGB pictures are supported. The above command starts the Afremize program with the default parameters. These were optimized especially for 2700x1500 pictures. For other dimensions, the program tries to compute the optimum parameter values as well.

For a list of all supported configuration options, type into Terminal:
    
    python main.py --help

In case the default parameters do not produce pleasing results, turn on detailed information printing with the --verbose flag, as well as creating of help files which will help you understand how exactly the conversion process did its job and maybe how it can be improved:
    
    python main.py -f "path/to/input_picture.png" --verbose --otherfiles

In case there are, for example, overall to few details visible in the output picture, try making the brush strokes smaller. In case the --verbose flag showed during the previous conversion that the strokeWidth parameter had a value of 80, try making it 50 (using the same input picture) and see what happens:
    
    python main.py -f "path/to/input_picture.png" --verbose --otherfiles --width=50

Or try to turn on stroke size randomization, with stroke size values between 40% and 100% of their maximum size (strokeWidth):
    
    python main.py -f "path/to/input_picture.png" --verbose --otherfiles --width=50 --randSizes=40

In a similar manner, you can alter the brush stroke density, or the ratio between simple, single-colored and complex, multi-colored brush strokes, as well as saturation, or the background picture used, and much more.



##  RUNTIME

On an i5 computer with 8 GB RAM, a 2700x1500 input picture needs about 2-4 minutes to convert.

This depends on the level of detail in the input picture and on the configuration options you use.


##  CONTACT

If you have questions about afremize, direct them at

    afremize@gmail.com

I'll try to get back to you.
