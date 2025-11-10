"""
Observational Astronomy - Computer Lab - University of Edinburgh

Script containing the functions that create interactive plots for the Astrometry Exercise
:Author:
    Lea Ferellec
:Date Created:
    September 13, 2023
:Last Modified:
    January 12, 2024 by Lea Ferellec
"""

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt 
from astropy.visualization import (ZScaleInterval, LinearStretch,
                                   ImageNormalize)   
from scipy.optimize import curve_fit,least_squares
from mpl_point_clicker import clicker
import lineid_plot





def display_2d(image_array,title):
    '''
    Function to display a 2D-image with z-scale brightness scaling.
    INPUTS:
        - image_array: np.array image to display
        - title: string to use as the title of your plot
    '''
    plt.figure(figsize=(10,3))
    interval = ZScaleInterval()
    vmin,vmax=interval.get_limits(image_array)
    norm = ImageNormalize(vmin=vmin, vmax=vmax, stretch=LinearStretch())
    plt.imshow(image_array,cmap='viridis',norm=norm)
    plt.title(title)
    plt.show()
    
def background(image,y1,y2,y3,y4):
    '''
    Function to fit a polynomial profile to each column of the 2D-spectrum within the y ranges y1 to y2 and y3 to y4.
    INPUTS:
        - image: np.array containing your @D-spectrum
        - y1,y2,y3,y4: y-coordinates delimiting the 2 ranges containing the background.
    OUTPUTS:
        - bkg_array: fitted 2D-spectrum of the sky background.
    '''
    if not(y1<y2<y3<y4) or not(0<=y1<=63) or not(0<=y2<=63) or not(73<=y3<=135) or not(73<=y4<=135):
        raise Exception("Error: y-values are inconsistent, make sure that they are given in increasing order and that they are not out of bounds.")
    else:
        n = min(image.shape)
        N = max(image.shape)
        bkg_array = np.zeros_like(image)
        x=np.concatenate((np.arange(y1,y2),np.arange(y3,y4))) 
        fit=[]
        for col in range(N):
            if col<=1 or col>=N-2:
                column=image[:,col]
                bkg=np.concatenate((column[y1:y2],column[y3:y4]))
            else:
                column=np.median([image[:,col-1],image[:,col],image[:,col+1]],axis=0)
                bkg=np.concatenate((column[y1:y2],column[y3:y4]))
            f=np.polyfit(x,bkg,2)
            fit_func=np.poly1d(f)
            fit=fit_func(np.arange(n))
            for i in range(n):
                bkg_array[i][col]=fit[i]
        return bkg_array

def gauss(x, H, A, x0, sigma):
    '''
    Gaussian function formatted for curve fitting.
    '''
    return H + A * np.exp(-(x - x0) ** 2 / (2 * sigma ** 2))

def fit_gaussian_centroid(x,y,p0):
    '''
    Fits a Gaussian profile to y=f(x) with initial guesses p0
    '''
    parameters, covariance = curve_fit(gauss, x, y,p0=p0)
    return parameters    
    
def centroid_peak(width, x, y, centre):
    '''
    Returns the x-coordinate of the center of the fitted Gaussian profile
    '''
    x_zoom=x[centre-width:centre+width]
    y_zoom=y[centre-width:centre+width]
    centre_fit=fit_gaussian_centroid(x_zoom,y_zoom,[0,y_zoom[width],x_zoom[width],1])
    return centre_fit[2]
         
def get_centroid_locations(pix, spectrum): 
    '''
    Fits a Gaussian profile to every emission line to obtain more accurate pixel-coordinates 
    INPUTS:
        -pix: list of pixel coordinates for the arc lines
        -spectrum: 1D-spectrum of the arc lamp
    OUTPUTS:
        -pix_refined: list of more accurate pixel coordinates (fitted Gaussian centroids) for the arc lines
    '''
    N=len(spectrum)
    pix_refined=[]
    for p in pix:
        pix_refined.append(centroid_peak(5, np.arange(N), spectrum, int(p)))
    return pix_refined

def calibration(pix_refined,wav,pix_axis):
    '''
    Fits a polynomial relation between the pixel coordinates and wavelengths. Displays a plot of the residuals of the fits and calculates the RMS. 
    INPUTS:
        -pix_refined: list of pixel coordinates for the arc lines
        -wav: list of wavelengths corresponding to the lines in pix_refined
        -pix_axis: list of pixels to convert to the calibrated wavelength, i.e. the entire pixel axis of 
         the 1D-spectra that we have.
    OUTPUTS:
        -wav_axis: Calibrated wavelength x-axis for the 1D-spectra.
    '''
    fit=np.polyfit(pix_refined,wav,3)
    wavcal_func=np.poly1d(fit)

    wav_axis=wavcal_func(pix_axis)

    wav2=wavcal_func(pix_refined)
    RMS=np.sqrt(np.sum((wav2-wav)**2)/len(pix_refined))
    print("RMS: ",RMS, " Angstroms")
    
    plt.figure(figsize=(9,6))
    plt.scatter(wav,wav2-wav, c='k',marker='+', label="RMS: "+ str(round(RMS,3)) +"A")
    plt.title("Residuals of the wavelength calibration fit")
    plt.xlabel("Input Wavelengths (A)")
    plt.ylabel("Residuals (A)")
    plt.axhline(0,c="gray",ls="--",zorder=-10)
    plt.legend()
    plt.show()
    
    return wav_axis


def plot_lines(arc_spectrum, pix_refined, wav_labels,x_label,y_label,title, fontsize):
    '''
    Displays the arc spectrum and labels the lines for which the wavelengths have been specified.
    INPUTS:
        -arc_spectrum: array containing the 1D-spectrum ofthe arc lamp.
        -pix_refined: list of pixel_coordinates of the lines.
        -wav_labels: list of strings representing the wavelengths of the lines.
        -x_label: string for the x-label of the plot
        -y_label: string for the y-label of the plot
        -title: string for the title of the plot
    '''
    fig,ax=plt.subplots(figsize=(9,6))
    plt.plot(arc_spectrum)  
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.title(title)

    plt.ylim(-50000,1.2*max(arc_spectrum))
    pk = lineid_plot.initial_plot_kwargs()
    pk['color'] = 'lightblue'
    lineid_plot.plot_line_ids(range(len(arc_spectrum)), arc_spectrum, pix_refined, wav_labels,ax=ax,arrow_tip=1.01*max(arc_spectrum),box_loc=1.1*max(arc_spectrum),plot_kwargs=pk)
    for i in ax.findobj(mpl.text.Annotation):
        i.set_fontsize(fontsize)
    plt.show()