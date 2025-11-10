"""
Observational Astronomy - Computer Lab - University of Edinburgh

Script containing the functions that create interactive plots for the Astrometry Exercise
:Author:
    Macarena G. del Valle-Espinosa
:Date Created:
    January 09, 2024
:Last time modified:
    January 12, 2024 by Macarena G. del Valle-Espinosa
"""

from __future__ import annotations 

import bokeh
import yaml

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from astropy.io import fits

from bokeh import events
from bokeh.io import show, output_notebook
from bokeh.layouts import row, column, gridplot
from bokeh.models import *

from bokeh.plotting import figure, curdoc
from bokeh.themes import Theme


# Function to create the Bokeh interactive plot on Jupyter Notebook
# This function allows the user to display one image, change the colorbar,
# zoom-in the different stars and displays the (x,y) coordinates of the pixels tapped

def polyxenaPlot(polyxena, notebook_url="http://localhost:8888"):
    '''
    Function to display the polyxena image, zoom-in around the objects and 
    click at the center 
    INPUTS:
        - polyxena: np.array image of the polyxena field of view
        - notebook_url: the notebook server for the session open. In order to display the interactive plot 
                        the numbers after 'localhost:' must match the notebook url. Default value is set to
                        'http://localhost:8888'
    '''

    def polyxenaDisplay(doc):

        # Colormap for the image
        color_mapper = LinearColorMapper(palette="Viridis256", low=3000, high=8500)

        # List of tools to be added to the plot. These are all interactive
        TOOLS = 'box_zoom, pan, crosshair, tap, reset, hover'
        TOOLTIPS = [('(x, y)','($x{3.0f}, $y{3.0f})'), ('value', '@image')]

        # Empty figure to superpose the plots and tools
        plot = figure(tools=TOOLS, tooltips=TOOLTIPS, 
                      x_range=(0,len(polyxena)), y_range=(0,len(polyxena)), toolbar_location='above')

        # Polyxena image + colorbar 
        r = plot.image(image=[polyxena], color_mapper=color_mapper,
                        dh=len(polyxena), dw=len(polyxena), x=0, y=0)
        plot.add_layout(ColorBar(color_mapper=color_mapper, location=(0, 0), 
                           ticker=FixedTicker(ticks=np.linspace(15, 35, 5))), 'right')


        # This function updates the values on the range slider (used to change in real time the color-range of the colorbar)
        def updateCb(attr, old, new):
            r.glyph.color_mapper.low = cbim.value[0]
            r.glyph.color_mapper.high = cbim.value[1]
        
        def updateBcLim():
            cbim.start = float(minCB.value)
            cbim.end = float(maxCB.value)

        # Function to collect the x and y coordinates of an event (in this case, a click with the mouse)
        '''WARNING!!!! Unless you know JavaScript, please DO NOT change this function'''
        def display_event(divX: Div, divY: Div, attributes: list[str] = []) -> CustomJS:
            """
            Function to build a suitable CustomJS to display the current event
            in the div model.
            """
            style = 'float: left; clear: left; font-size: 13px'
            return CustomJS(args=dict(divX=divX, divY=divY), code=f"""
                const attrs = {attributes};
                const args = [];
                for (let i = 0; i < attrs.length; i++) {{
                    const val = JSON.stringify(cb_obj[attrs[i]], function(key, val) {{
                        return val.toFixed ? Number(val.toFixed(2)) : val;
                    }})
                    args.push(attrs[i] + '=' + val)
                }}
                const line = "<span style={style!r}><b>" + cb_obj.event_name + "</b>(" + args.join(", ") + ")</span>\\n";
                const xy = args.join(", ");
                const vals = xy.split(", ");
                const xval = vals[0].split("x=")[1];
                const lineX = xval + ", \\n";
                const textX = divX.text.concat(lineX);
                const linesX = textX.split(", \\n");
                if (linesX.length > 35)
                    linesX.shift();
                divX.text = linesX.join(", \\n");
                const yval = vals[1].split("y=")[1];
                const lineY = yval + ", \\n";
                const textY = divY.text.concat(lineY);
                const linesY = textY.split(", \\n");
                if (linesY.length > 35)
                    linesY.shift();
                divY.text = linesY.join(", \\n");
            """)

        
        # System to change the colorbar range slider
        cbim = RangeSlider(title='Colorbar', start=0, end=10000, value=(3000, 8500), step=100, width=200)
        cbim.on_change('value', updateCb)
        buttonColorbar = Button(label='Update colorbar', width=120)
        minCB = TextInput(title='min', value='-200', width=60)
        maxCB = TextInput(title='max', value='5000', width=60)
        buttonColorbar.on_click(updateBcLim)
        
        # System to store the x and y coordinates tapped on the plot
        textx = bokeh.models.TextInput(value='x values', width=100)
        texty = bokeh.models.TextInput(value='y values', width=100)
        divX = Div(width=50) # Bokeh instance to store the x 
        divZ = Div(width=50) 
        divY = Div(width=50) # Bokeh instance to store the y
        point_attributes = ['x','y'] # Values to save
        plot.js_on_event(events.DoubleTap, display_event(divX, divY, attributes=point_attributes))

        # Deactivating the automatic selection of `tap` to prevent students for clicking by mistake
        plot.toolbar.active_tap = None
        
        # Layout of the overall plot
        inputs = column(cbim, buttonColorbar, row(minCB, maxCB), row(textx, texty), row(divX, divZ, divY))
        layout = gridplot([[inputs, plot]], merge_tools=False)
        doc.add_root(layout)
        
    # Display the interactive plot
    show(polyxenaDisplay, notebook_url=notebook_url)    


# Function to create the Bokeh interactive plot on Jupyter Notebook
# This functions allows the user to display the image in a 5x5 grid, change the colorbar,
# and marks the centres of the selected stars

def polyxenaPlotCentres(polyxena, xcoors, ycoors, notebook_url="http://localhost:8888"):
    '''
    Function to display a zoom around each sta. This function also draws 
    a cross in the centre of each star
    INPUTS:
        - polyxena: np.array image of the polyxena field of view
        - xcoors: x coordinates of the stars to be displayed
        - ycoors: y coordinates of the stars to be displayed
        - notebook_url: the notebook server for the session open. In order to display the interactive plot 
                        the numbers after 'localhost:' must match the notebook url. Default value is set to
                        'http://localhost:8888'
    '''
    def polyxenaDisplayGrid(doc):
    
        # Colormaps for each of the cluster images v and i
        color_mapper = LinearColorMapper(palette="Viridis256", low=3000, high=8500)

        # We want to create a grid of 5x5 with zooms around each star
        # Bokeh DOES NOT preserve the same pixel size once you do a zoom in the image,
        # so the apertures displayed in a zoom image do not correspond with the real size
        # Doing a grid prevents the students from zoom on objects and display 
        # the apertures with the correct sizes
        # This loop creates the cutout images around the x and y coordinates used as input
        listPlots = []
        for (i, x), y in zip(enumerate(xcoors), ycoors):
            globals()['polyxena_cut%i'%(i+1)] = polyxena[int(y-30):int(y+30), int(x-30):int(x+30)]
            
            # Figure on the grid with the correcponding zoom to the object
            globals()['plot_cut%i'%(i+1)] = figure(x_range=(0, 60), y_range=(0, 60))
            listPlots.append(eval('plot_cut%i'%(i+1)))
            globals()['r_%i'%(i+1)] = eval('plot_cut%i'%(i+1)).image(image=[eval('polyxena_cut%i'%(i+1))], 
                                                  color_mapper=color_mapper,
                                                  dh=eval('polyxena_cut%i'%(i+1)).shape[0], 
                                                  dw=eval('polyxena_cut%i'%(i+1)).shape[1], x=0, y=0)
            
            # Object and cross in each of the figures
            globals()['c_%i'%(i+1)] = eval('plot_cut%i'%(i+1)).cross(x=30, y=30, line_width=1.3, color='red', size=10)
            

        # This function updates the values on the range slider (used to change in real time the color-range of the colorbar)
        def updateCb(attr, old, new):
            for i in range(len(xcoors)):
                eval('r_%i'%(i+1)).glyph.color_mapper.low = cbim.value[0]
                eval('r_%i'%(i+1)).glyph.color_mapper.high = cbim.value[1]
            
        def updateBcLim():
            cbim.start = float(minCB.value)
            cbim.end = float(maxCB.value)
            
        # Colobar slider and system to update the limits
        cbim = RangeSlider(title='Colorbar', start=1500, end=10000, value=(3000, 8500), step=1, width=500)
        cbim.on_change('value', updateCb)
        buttonColorbar = Button(label='Update colorbar', width=200, align='end')
        minCB = TextInput(title='min', value='-200', width=100)
        maxCB = TextInput(title='max', value='5000', width=100)
        buttonColorbar.on_click(updateBcLim)
        
        blankSpace = Div(width=200, height=50)
        
        # Layout of the overall plot
        grid = gridplot(listPlots, ncols=5, width=150, height=150)
        layout = gridplot([[column(cbim, row(buttonColorbar, minCB, maxCB),grid)]], merge_tools=False)
        doc.add_root(layout)
    
    # Display the interactive plot
    show(polyxenaDisplayGrid, notebook_url=notebook_url)
    


