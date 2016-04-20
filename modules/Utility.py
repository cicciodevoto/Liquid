# The MIT License (MIT)

# Copyright (c) 2015 Francesco Devoto

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Module containing useful functions used in LASDiA.

The nomenclature and the procedure follow the article:
Eggert et al. 2002 PRB, 65, 174105.

For the functions arguments and the returns I followed this convetion for the notes:
arguments: description - type
returns: description - type.

For the variables name I used this convention:
if the variable symbolizes a mathematical function, its argument is preceded by an underscore: f(x) -> f_x
otherwise it is symbolized with just its name.
"""

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.axes3d import Axes3D

import sys
import os

import numpy as np
import scipy.constants as sc
from scipy import fftpack
from scipy.integrate import simps
from scipy import interpolate
from scipy import signal
import math
import random
from collections import Counter
import re
import imp
import time
import datetime

def read_file(path):
    """Read the file and return x and y as numpy vectors

    arguments:
    path: file path to read - string

    returns:
    xVect: abscissa values - array
    yVect: ordinate values - array
    """

    file = open(path, "r")
    file_name = file.name
    ext = os.path.splitext(file_name)[1]

    dimension = "nano"
    scale_factor = 1

    if ext == ".chi":
        # Read and ignore the first 4 lines:
        header1 = file.readline()
        header2 = file.readline()
        header3 = file.readline()
        header4 = file.readline()
        # I move the factor scale from nm to A into the other functions
        # if dimension.lower() in header2.lower():
            # scale_factor = 10
    elif ext == ".xy":
        # Read and ignore the first 17 lines:
        header1 = file.readline()
        header2 = file.readline()
        header3 = file.readline()
        header4 = file.readline()
        header5 = file.readline()
        header6 = file.readline()
        header7 = file.readline()
        header8 = file.readline()
        header9 = file.readline()
        header10 = file.readline()
        header11 = file.readline()
        header12 = file.readline()
        header13 = file.readline()
        header14 = file.readline()
        header15 = file.readline()
        header16 = file.readline()
        header17 = file.readline()


    # Read all the file in one time and close the file:
    lines = file.readlines()
    file.close()

    # Set the variables:
    # in our case the variables are: Q and I(Q)
    x = []
    y = []

    # Scan the rows of the file stored in lines, and put the values into the variables:
    for line in lines:
        columns = line.split()
        x.append(float(columns[0]))
        y.append(float(columns[1]))

    # Modify the variables as numpy array:
    xVect = np.array(x)
#    xVect /= scale_factor
    yVect = np.array(y)

    return (xVect, yVect)


def write_file(path, xVar, yVar, xName, yName):
    """Function to write on file
    """
    
    dir = os.path.dirname(path)
    
    if not os.path.exists(dir):
        os.makedirs(dir)
    
    file = open(path, "w")
    file_name = file.name

    output = np.column_stack((xVar.flatten(), yVar.flatten()))
    file.write(xName + " \t " + yName + "\n")
    np.savetxt(file_name, output, delimiter='\t')
    file.close()


def write_results(path, molecule, scale_factor, rho0):
    """Function to write scale factor and rho0 on file
    """
    
    file = open(path, "a")
    file_name = file.name
    
    ts = time.time()
    timeStamp = datetime.datetime.fromtimestamp(ts).strftime("%Y%m%d_%H:%M:%S")
    
    file.write(timeStamp + " \t " + molecule + " \t " + str(scale_factor) + " \t " + str(rho0) + "\n")
    file.close()


def molToelemList(molecule):
    """Function from molecule to elementList
    """

    elemlist = re.findall('[A-Z][a-z]*|\d+', re.sub('[A-Z][a-z]*(?![\da-z])', '\g<0>1', molecule))
    elementList = dict(zip(elemlist[0::2], elemlist[1::2]))

    elementList = dict((k,int(v)) for k,v in elementList.items())

    return elementList


def path_xyz_file(molecule):
    """Function for the GUI to determinate the xyz file path from the molecule
    """

    path = "./xyzFiles/" + molecule + ".xyz"

    return path


def read_xyz_file(path):
    """Function to read the xyz file
    """

    file = open(path, "r")
    file_name = file.name
    ext = os.path.splitext(file_name)[1]

    numAtoms = int(file.readline())
    comment = file.readline()

    lines = file.readlines()
    file.close()

    element = []
    x = []
    y = []
    z = []

    for line in lines:
        columns = line.split()
        element.append(columns[0])
        x.append(float(columns[1]))
        y.append(float(columns[2]))
        z.append(float(columns[3]))

    xVect = np.array(x)
    xVect /= 10.0
    yVect = np.array(y)
    yVect /= 10.0
    zVect = np.array(z)
    zVect /= 10.0
    # elementPosition = {}

    # for line in lines:
        # elem, x, y, z = line.split()
        # elementPosition[elem] = [x, y, z]

    return (numAtoms, element, xVect, yVect, zVect)


def calc_distMol(x1, y1, z1, x2, y2, z2):
    """Function to calculate di distance between 2 points
    """

    d = np.sqrt( (x1-x2)**2 + (y1-y2)**2 + (z1-z2)**2)

    return d


def read_inputFile(path):
    """Function to read variables from the inputFile.txt
    """

    file = open(path)
    variables = imp.load_source('data', '', file)
    file.close()
    return variables


def setArray(min, max, step):
    """Function to generate the numpy array for s and rho0
    """

    if min == max:
        a = np.arange(min, max+step, step)
    else:
        a = np.arange(min, max, step)

    return a


def plot_raw_data(xVar, yVar, plotName, xName, yName, labName):
    """Function to plot
    """

    plt.figure(plotName)
    plt.plot(xVar, yVar, label=labName)
    plt.xlabel(xName)
    plt.ylabel(yName)
    plt.legend()
    plt.grid(True)
    plt.draw()
    # plt.show
    
    
def plot_data(xVar, yVar, plotName, xName, yName, labName):
    """Function to plot
    """

    plt.figure(plotName)
    plt.clf()
    plt.plot(xVar, yVar, label=labName)
    plt.xlabel(xName)
    plt.ylabel(yName)
    plt.legend()
    plt.grid(True)
    plt.draw()
    
    
def plot_chi2(s, rho0, chi2):
    """
    """
    
    # plot 2d chi2
    plt.figure('chi2s')
    plt.plot(s,chi2[0, : ])
    plt.xlabel('s')
    plt.ylabel('chi2')
    plt.grid()
    plt.show

    plt.figure('chi2rho0')
    plt.plot(rho0,chi2[ : ,0])
    plt.xlabel('rho0')
    plt.ylabel('chi2')
    plt.grid()
    plt.draw()
    
    
def plot3d_chi2(s, rho0, chi2):
    """
    """
    
    # plot the 3d chi2 and its profile
    x, y = np.meshgrid(s, rho0)
    fig = plt.figure('chi2 3D')
    ax = Axes3D(fig)
    ax.set_xlabel('s')
    ax.set_ylabel(r'$\rho_0$ (atoms/$nm^3$)')
    ax.set_zlabel(r'$\chi^2$')
    ax.plot_surface(x, y, chi2, rstride=1, cstride=1, cmap='rainbow')

    plt.figure('chi2 Profile')
    plt.contour(s, rho0, chi2, 200)
    plt.xlabel('s')
    plt.ylabel(r'$\rho_0$ (atoms/$nm^3$)')
    plt.draw()
        
