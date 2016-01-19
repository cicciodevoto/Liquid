# The MIT License (MIT)

# Copyright (c) 2016 Francesco Devoto

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

"""Environment for testing the software
The nomenclature and the procedures follow the article: Eggert et al. 2002 PRB, 65, 174105
"""

from __future__ import (absolute_import, division, print_function, unicode_literals)
import six

import sys
import os

import scipy.constants as sc
from scipy import fftpack
from scipy import signal
from scipy.interpolate import UnivariateSpline
import matplotlib.pyplot as plt
import numpy as np

from modules.Utility import *
from modules.LiquidStructure import *
from modules.InterpolateData import *
from modules.Optimization import *
from modules.Minimization import *

# import cmath
# from cmath import exp, pi

if __name__ == '__main__':
    N = 1 # sc.N_A
    
    Q, I_Q = read_file("./data/cea_files/HT2_034T++.chi")
    Qbkg, I_Qbkg = read_file("./data/cea_files/HT2_036T++.chi")

    # s = UnivariateSpline(Q, I_Q, k=3, s=0.5)
    # I_Qs = s(Q)

    # plt.figure(3)
    # plt.plot(Q, I_Q)
    # plt.plot(Q, I_Qs)
    # plt.grid()
    # plt.show()
    
    minQ = 3
    maxQ = 109
    QmaxIntegrate = 90
    
    min_index = np.where(Q<=minQ)
    max_index = np.where((Q>QmaxIntegrate) & (Q<=maxQ))
    validation_index = np.where(Q<=maxQ)
    integration_index = np.where(Q<=QmaxIntegrate)
    
    calculation_index = np.where((Q>minQ) & (Q<=QmaxIntegrate))
    
    elementList = {"Ar":1}
    s =  0.5
    rho0 = 24.00
    
    # remember the electron unit in atomic form factor!!!
    fe_Q, Ztot = calc_eeff(elementList, Q)
    Iincoh_Q = calc_Iincoh(elementList, Q)
    J_Q = calc_JQ(Iincoh_Q, Ztot, fe_Q)
    Sinf = calc_Sinf(elementList, fe_Q, Q, Ztot)
    Isample_Q = calc_IsampleQ(I_Q, s, I_Qbkg)
    
    alpha = calc_alpha(J_Q, Sinf, Q, Isample_Q, fe_Q, Ztot, rho0, integration_index)
    Icoh_Q = calc_Icoh(N, alpha, Isample_Q, Iincoh_Q)
    
    S_Q, S_Qs = calc_SQ(N, Icoh_Q, Ztot, fe_Q, Sinf, Q, min_index, max_index, calculation_index)
    
    
    plt.figure(1)
    #plt.plot(Q[validation_index], S_Q)
    plt.plot(Q[validation_index], S_Qs)
    plt.grid()
    plt.show
    
    i_Q = calc_iQ(S_Q, Sinf)
#    i_Q = calc_iQ(S_Qs, Sinf)
    Qi_Q = Q[validation_index] * i_Q
    
    DeltaQ = np.diff(Q)
    meanDeltaQ = np.mean(DeltaQ)
    r = fftpack.fftfreq(Q[validation_index].size, meanDeltaQ)
    mask = np.where(r>0)
    
    F_r = calc_Fr(r[mask], Q[integration_index], i_Q[integration_index])
    
    plt.figure(2)
    plt.plot(r[mask], F_r)
    plt.grid()
    plt.show
    
    iteration = 4
    rmin = 0.24
    F_rInt = calc_optimize_Fr(iteration, F_r, rho0, i_Q[integration_index], Q[integration_index], Sinf, J_Q[integration_index], r[mask], rmin)
    
    plt.figure(2)
    plt.plot(r[mask], F_rInt)
    plt.show()


    
