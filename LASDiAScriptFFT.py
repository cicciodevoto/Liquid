# The MIT License (MIT)

# Copyright (c) 2015-2016 European Synchrotron Radiation Facility

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

"""LASDiA main script file.
This script is mainly used for testing the software, but it can be used to run LASDiA
in text mode.

The nomenclature and the procedures follow the article: Eggert et al. 2002 PRB, 65, 174105.

For the variables name I used this convention:
if the variable symbolizes a mathematical function, its argument is preceded by
an underscore: f(x) -> f_x
otherwise it is symbolized with just its name.
"""


from __future__ import (absolute_import, division, print_function, unicode_literals)
import six

import sys
import matplotlib.pyplot as plt
import numpy as np
import time
# from itertools import product
# from timeit import default_timer as timer
from scipy.integrate import simps
from scipy import fftpack
from scipy import interpolate
from scipy import signal
import math

from modules import Formalism
from modules import Geometry
from modules import IgorFunctions
from modules import KaplowMethod
from modules import MainFunctions
from modules import Minimization
from modules import Optimization
from modules import Utility
from modules import UtilityAnalysis

from PyQt5.QtWidgets import QApplication, QVBoxLayout, QWidget


if __name__ == "__main__":
    
    #---------------------------Files reading----------------------------------
    
    variables = Utility.read_inputFile("./inputFile.txt")
    
    elementList = Utility.molToelemList(variables.molecule)
    elementParameters = Utility.read_parameters(elementList, variables.element_params_path)
    
    path = Utility.path_xyz_file(variables.molecule)
    numAtoms, element, x, y, z = Utility.read_xyz_file(path)
    
    Q, I_Q = Utility.read_file(variables.data_file)
    Qbkg, Ibkg_Q  = Utility.read_file(variables.bkg_file)
    
    Utility.plot_data(Qbkg, Ibkg_Q, "GR", "r", "G(r)", "G(r)", "y")
    #--------------------Preliminary calculation-------------------------------

    # Q, I_Q, Qbkg, Ibkg_Q = UtilityAnalysis.check_data_length(Q, I_Q, Qbkg, Ibkg_Q,
        # variables.minQ, variables.maxQ)
    
    
    Q = np.linspace(0.0, variables.maxQ, 2048, endpoint=True)
    interI_Q = interpolate.interp1d(Q, I_Q)
    I_Q = interI_Q(Q)
    

    
    fe_Q, Ztot = MainFunctions.calc_eeff(elementList, Q, elementParameters)
    Iincoh_Q = MainFunctions.calc_Iincoh(elementList, Q, elementParameters)
    # Utility.write_file("./iincoh.txt", Q, Iincoh_Q)
    # Utility.plot_data(Q, Iincoh_Q, "GR", "r", "G(r)", "G(r)", "y")
    # print(len(Iincoh_Q))
    J_Q = MainFunctions.calc_JQ(Iincoh_Q, Ztot, fe_Q)
    Sinf, Sinf_Q = MainFunctions.calc_Sinf(elementList, fe_Q, Q, Ztot, elementParameters)
    
    dampingFunction = UtilityAnalysis.calc_dampingFunction(Q, variables.dampingFactor,
        variables.QmaxIntegrate, variables.typeFunction)

    #-------------------Intra-molecular components-----------------------------

    iintra_Q = Optimization.calc_iintra(Q, fe_Q, Ztot, variables.QmaxIntegrate, 
        variables.maxQ, elementList, element, x, y, z, elementParameters)
    iintradamp_Q = UtilityAnalysis.calc_iintradamp(iintra_Q, Q, variables.QmaxIntegrate, 
        dampingFunction)
    rintra, Fintra_r = UtilityAnalysis.calc_FFT_QiQ(Q, iintradamp_Q, variables.QmaxIntegrate)
    
    # ---------------------Geometrical correction------------------------------
    
    two_theta = UtilityAnalysis.Qto2theta(Q)
    
    # abs_corr_factor = Geometry.calc_absorption_correction(variables.abs_length,
        # two_theta, variables.dac_thickness, 0)
    
    # print(len(Q))
    # print(np.amin(Q))
    # print(np.amax(Q))
    abs_corr_factor = Geometry.absorptionIgor(Q)
    
    # Utility.write_file("./abs_corr_factor.txt", Q, A)
    # Utility.plot_data(Q, A, "GR", "r", "G(r)", "G(r)", "y")
    
    I_Q = I_Q /(abs_corr_factor)
    Ibkg_Q  = Ibkg_Q / (abs_corr_factor)
    
    
    # ------------------------Starting minimization----------------------------
    
    scaleFactor = 0.45 #variables.scaleFactor
    density = variables.density
    
    Isample_Q = MainFunctions.calc_IsampleQ(I_Q, scaleFactor, Ibkg_Q)
    Utility.plot_data(Q, Isample_Q, "GR", "r", "G(r)", "G(r)", "y")
    
    alpha = MainFunctions.calc_alpha(J_Q[Q<=variables.QmaxIntegrate], Sinf, 
        Q[Q<=variables.QmaxIntegrate], Isample_Q[Q<=variables.QmaxIntegrate],
        fe_Q[Q<=variables.QmaxIntegrate], Ztot, density)
    Icoh_Q = MainFunctions.calc_Icoh(alpha, Isample_Q, Iincoh_Q)

    S_Q = MainFunctions.calc_SQ(Icoh_Q, Ztot, fe_Q, Sinf, Q, variables.minQ, 
        variables.QmaxIntegrate, variables.maxQ)
    
    # Utility.plot_data(Q, S_Q, "S_Q", "Q", "S(Q)", "S(Q)", "y")
    
    Ssmooth_Q = UtilityAnalysis.calc_SQsmoothing(Q, S_Q, Sinf, 
        variables.smoothingFactor, 
        variables.minQ, variables.QmaxIntegrate, variables.maxQ)
    SsmoothDamp_Q = UtilityAnalysis.calc_SQdamp(Ssmooth_Q, Sinf,
        dampingFunction)
    
    Q, SsmoothDamp_Q = UtilityAnalysis.rebinning(Q, SsmoothDamp_Q, 0.0, 
        variables.maxQ, variables.NumPoints)
    
    chi2 = Optimization.FitRemoveGofRPeaks(Q, SsmoothDamp_Q, Sinf, 
        variables.QmaxIntegrate, rintra, Fintra_r, variables.iterations, 
        variables.rmin, density, J_Q)
    
    # print(chi2)
    
    plt.show()