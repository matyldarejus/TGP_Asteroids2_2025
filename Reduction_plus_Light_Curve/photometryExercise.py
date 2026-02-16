"""
Observational Astronomy - Computer Lab - University of Edinburgh

Script containing the functions that create interactive plots for the Photometry Exercise
:Author:
    Macarena G. del Valle-Espinosa
:Date Created:
    October 11, 2023
:Last time modified:
    January 11, 2024 by Macarena G. del Valle-Espinosa
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


def standardPlot(standard, notebook_url="http://localhost:8888"):
    '''
    Function to display the standard star image, change the colorbar and display
    and modified the object and sky apertures 
    INPUTS:
        - standard: np.array image of the standard star
        - notebook_url: the notebook server for the session open. In order to display the interactive plot 
                        the numbers after 'localhost:' must match the notebook url. Default value is set to
                        'http://localhost:8888'
    '''
    
    def standardDisplay(doc):
    
        # Useful tools to add to the plot
        TOOLS = 'box_zoom, pan, crosshair, reset, hover'
        TOOLTIPS = [('(x, y)','($x{3.0f}, $y{3.0f})'), ('value', '@image')]

        # Central plot with the standard star
        plot = figure(tools=TOOLS, tooltips=TOOLTIPS, 
                      x_range=(0,standard.shape[1]), y_range=(0,standard.shape[0]), toolbar_location='below')
        
        color_mapper = LinearColorMapper(palette="Viridis256", low=100, high=1000)
        r = plot.image(image=[standard], color_mapper=color_mapper,
                       dh=standard.shape[0], dw=standard.shape[1], x=0, y=0)
        plot.add_layout(ColorBar(color_mapper=color_mapper, location=(0, 0), 
                                 ticker=FixedTicker(ticks=[0, 100, 500, 1000, 2500, 5000, 1e4])), 'right')
        
        # Initial guess on the location of the standard star
        # This is necesary to create the apertures, which remind hiden till the user interacts with the plot
        X = 50 ; Y = 50
        c = plot.cross(x=X, y=Y, line_width=1.3, color='red', size=10)
        c.visible = False
        aperture = plot.circle(x=X, y=Y, line_width=1.3, line_color='white', radius=3, fill_alpha=0)
        aperture.visible = False
        innerSky = plot.circle(x=X, y=Y, line_width=1.3, line_color='red', radius=aperture.glyph.radius*1.5, fill_alpha=0)
        innerSky.visible = False
        outerSky = plot.circle(x=X, y=Y, line_width=1.3, line_color='red', radius=aperture.glyph.radius*2, fill_alpha=0)
        outerSky.visible = False
        
        # Set of function to update the plot depending on the interaction
        def updateCb(attr, old, new):
            '''Function to change the minimum and maximum value of the image cmap'''
            r.glyph.color_mapper.low = cbim.value[0]
            r.glyph.color_mapper.high = cbim.value[1]
            
        def updateBcLim():
            '''Function to update the minimum and maximum values available at the colorbar'''
            cbim.start = float(minCB.value)
            cbim.end = float(maxCB.value)
            
        def update():
            '''Function to draw the location of the center of the star'''
            # coordinates of spaxels to draw, taken from input text boxes
            c.glyph.x = float(Xp.value)
            c.glyph.y = float(Yp.value)
            c.visible = True
            
        def updateR():
            '''Function to display and update the object and sky apertures'''
            aperture.glyph.x = float(Xp.value)
            aperture.glyph.y = float(Yp.value)
            innerSky.glyph.x = float(Xp.value)
            innerSky.glyph.y = float(Yp.value)
            outerSky.glyph.x = float(Xp.value)
            outerSky.glyph.y = float(Yp.value)
            aperture.glyph.radius = float(Rp.value)
            innerSky.glyph.radius = float(Rp.value)*1.5
            outerSky.glyph.radius = float(Rp.value)*2
            aperture.visible = True
            innerSky.visible = True
            outerSky.visible = True

        # Colobar slider and system to update the limits
        cbim = RangeSlider(title='Colorbar', start=-200, end=5000, value=(100, 1000), step=10, width=500)
        cbim.on_change('value', updateCb)
        buttonColorbar = Button(label='Update colorbar', width=200, align='end')
        minCB = TextInput(title='min', value='-200', width=100)
        maxCB = TextInput(title='max', value='5000', width=100)
        buttonColorbar.on_click(updateBcLim)
        
        blankSpace = Div(width=200, height=100)
        
        # System to change the center of the apertures
        buttonCenter = Button(label='Center of star (x, y)', width=200)
        Xp = TextInput(value="x", width=95)
        Yp = TextInput(value="y", width=95)
        buttonCenter.on_click(update)
        
        # System to change the size of the object aperture
        buttonRadius = Button(label='Update radius', width=200)
        Rp = TextInput(value="3", width=200)
        buttonRadius.on_click(updateR)
        
        # Layout of the overall plot
        buttons = column(blankSpace, buttonCenter, row(Xp, Yp), buttonRadius, Rp)
        layout = gridplot([[column(cbim, row(buttonColorbar, minCB, maxCB),plot), buttons]], merge_tools=False)

        doc.add_root(layout)
    
    # Display the interactive plot
    show(standardDisplay, notebook_url=notebook_url)
    

# Function to create the Bokeh interactive plot on Jupyter Notebook
# This function allows the user to display both filter images, change the colorbars,
# zoom-in the different galaxies and displays the (x,y) coordinates of the pixels tapped

def clusterPlot(cluster_v, cluster_i, notebook_url="http://localhost:8888"):
    '''
    Function to display the galaxy cluster images, zoom-in around the objects and 
    click at the center 
    INPUTS:
        - cluster_v: np.array image of the cluster in the v band
        - cluster_i: np.array image of the cluster in the i band
        - notebook_url: the notebook server for the session open. In order to display the interactive plot 
                        the numbers after 'localhost:' must match the notebook url. Default value is set to
                        'http://localhost:8888'
    '''

    def clusterDisplay(doc):

        # Colormaps for each of the cluster images v and i
        color_mapperV = LinearColorMapper(palette="Viridis256", low=15, high=35)
        color_mapperI = LinearColorMapper(palette="Viridis256", low=150, high=600)

        # List of tools to be added to the plot. These are all interactive
        TOOLS = 'box_zoom, pan, crosshair, tap, reset, hover'
        TOOLTIPS = [('(x, y)','($x{3.0f}, $y{3.0f})'), ('value', '@image')]

        # Empty figure to superpose the plots and tools
        plot = figure(tools=TOOLS, tooltips=TOOLTIPS, 
                      x_range=(0,len(cluster_v)), y_range=(0,len(cluster_v)), toolbar_location='above')

        # Cluster image + colorbar for the v filter. We want to display this one first
        rV = plot.image(image=[cluster_v], color_mapper=color_mapperV,
                        dh=len(cluster_v), dw=len(cluster_v), x=0, y=0)
        plot.add_layout(ColorBar(color_mapper=color_mapperV, location=(0, 0), 
                           ticker=FixedTicker(ticks=np.linspace(15, 35, 5))), 'right')

        # Cluster image + colorbar for the i filter. We set their visibility to False so we can see the v band
        rI = plot.image(image=[cluster_i], color_mapper=color_mapperI,
                        dh=len(cluster_i), dw=len(cluster_i), x=0, y=0)
        plot.add_layout(ColorBar(color_mapper=color_mapperI, location=(0, 0), 
                       ticker=FixedTicker(ticks=np.linspace(150, 600, 5))), 'right')
        rI.visible = False
        plot.right[1].visible = False

        # This function activate and deactivate the image display and colorbar according to the filter selected
        # It also changes the range of the colorbar according to the filter
        def updateIm(attr, old, new):
            if im.value == 'V':
                rV.visible = True
                plot.right[0].visible = True
                rI.visible = False
                plot.right[1].visible = False
                cbim.end = 100
                cbim.step = 10
                cbim.value = (15,35)

            elif im.value == 'I':
                rV.visible = False
                plot.right[0].visible = False
                rI.visible = True
                plot.right[1].visible = True
                cbim.end = 1000
                cbim.step = 10
                cbim.value = (150,600)

        # This function updates the values on the range slider (used to change in real time the color-range of the colorbar)
        def updateCb(attr, old, new):
            for rimg in [rV, rI]:
                rimg.glyph.color_mapper.low = cbim.value[0]
                rimg.glyph.color_mapper.high = cbim.value[1]
        
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

        
        # System to change the filter displayed
        im = Select(title='Filter', value='V', options=['V', 'I'], width=150)
        im.on_change('value', updateIm)
        # System to change the colorbar range slider
        cbim = RangeSlider(title='Colorbar', start=0, end=100, value=(15, 35), step=1, width=200)
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
        inputs = column(im, cbim, buttonColorbar, row(minCB, maxCB), row(textx, texty), row(divX, divZ, divY))
        layout = gridplot([[inputs, plot]], merge_tools=False)
        doc.add_root(layout)
        
    # Display the interactive plot
    show(clusterDisplay, notebook_url=notebook_url)    


# Function to create the Bokeh interactive plot on Jupyter Notebook
# This function displays a 5x5 grid with the previously selected galaxies.
# The function also allows the user to change between filter images, change the colorbars
# and draws apertures of the same size in all the individual galaxies.

def clusterPlotApertures(cluster_v, cluster_i, xcoors, ycoors, notebook_url="http://localhost:8888"):
    '''
    Function to display a zoom around each galaxy. This function also allows to draw 
    apertures around these galaxies with the same size. 
    INPUTS:
        - cluster_v: np.array image of the cluster in the v band
        - cluster_i: np.array image of the cluster in the i band
        - xcoors: x coordinates of the galaxies to be displayed
        - ycoors: y coordinates of the galaxies to be displayed
        - notebook_url: the notebook server for the session open. In order to display the interactive plot 
                        the numbers after 'localhost:' must match the notebook url. Default value is set to
                        'http://localhost:8888'
    '''
    def clusterDisplayGrid(doc):
    
        # Colormaps for each of the cluster images v and i
        color_mapperV = LinearColorMapper(palette="Viridis256", low=15, high=35)
        color_mapperI = LinearColorMapper(palette="Viridis256", low=150, high=600)

        # We want to create a grid of 5x5 with zooms around each galaxy
        # Bokeh DOES NOT preserve the same pixel size once you do a zoom in the image,
        # so the apertures displayed in a zoom image do not correspond with the real size
        # Doing a grid prevents the students from zoom on objects and display 
        # the apertures with the correct sizes
        # This loop creates the cutout images around the x and y coordinates use as input for
        # both filters and hide all cutouts in the i band
        listPlots = []
        for (i, x), y in zip(enumerate(xcoors), ycoors):
            globals()['cluster_v_cut%i'%(i+1)] = cluster_v[int(y-50):int(y+50), int(x-50):int(x+50)]
            globals()['cluster_i_cut%i'%(i+1)] = cluster_i[int(y-50):int(y+50), int(x-50):int(x+50)]
            
            # Figure on the grid with the correcponding zoom to the object
            globals()['plot_cut%i'%(i+1)] = figure(x_range=(20, 80), y_range=(20, 80))
            listPlots.append(eval('plot_cut%i'%(i+1)))
            globals()['rV_%i'%(i+1)] = eval('plot_cut%i'%(i+1)).image(image=[eval('cluster_v_cut%i'%(i+1))], 
                                                  color_mapper=color_mapperV,
                                                  dh=eval('cluster_v_cut%i'%(i+1)).shape[0], 
                                                  dw=eval('cluster_v_cut%i'%(i+1)).shape[1], x=0, y=0)
            globals()['rI_%i'%(i+1)] = eval('plot_cut%i'%(i+1)).image(image=[eval('cluster_i_cut%i'%(i+1))], 
                                                  color_mapper=color_mapperI,
                                                  dh=eval('cluster_i_cut%i'%(i+1)).shape[0], 
                                                  dw=eval('cluster_i_cut%i'%(i+1)).shape[1], x=0, y=0)
            
            eval('rI_%i'%(i+1)).visible = False
            
            # Object and sky apertures in each of the figures
            globals()['aperture_%i'%(i+1)] = eval('plot_cut%i'%(i+1)).circle(x=50, y=50, line_width=1.3, 
                                                                             line_color='white', radius=3, fill_alpha=0)
            eval('aperture_%i'%(i+1)).visible = False
            globals()['innerSky_%i'%(i+1)] = eval('plot_cut%i'%(i+1)).circle(x=50, y=50, line_width=1.3, 
                                                                             line_color='red', 
                                                                             radius=eval('aperture_%i'%(i+1)).glyph.radius*1.5, 
                                                                             fill_alpha=0)
            eval('innerSky_%i'%(i+1)).visible = False
            globals()['outerSky_%i'%(i+1)] = eval('plot_cut%i'%(i+1)).circle(x=50, y=50, line_width=1.3, 
                                                                             line_color='red', 
                                                                             radius=eval('aperture_%i'%(i+1)).glyph.radius*2, 
                                                                             fill_alpha=0)
            eval('outerSky_%i'%(i+1)).visible = False
            
            
        # This function activate and deactivate the image display and colorbar according to the filter selected
        # It also changes the range of the colorbar according to the filter
        def updateIm(attr, old, new):
            if im.value == 'V':
                for i in range(len(xcoors)):
                    eval('rV_%i'%(i+1)).visible = True
                    eval('rI_%i'%(i+1)).visible = False
                cbim.end = 100
                cbim.step = 10
                cbim.value = (15,35)

            elif im.value == 'I':
                for i in range(len(xcoors)):
                    eval('rV_%i'%(i+1)).visible = False
                    eval('rI_%i'%(i+1)).visible = True
                cbim.end = 1000
                cbim.step = 10
                cbim.value = (150,600)

        # This function updates the values on the range slider (used to change in real time the color-range of the colorbar)
        def updateCb(attr, old, new):
            for rimg in ['rV', 'rI']:
                for i in range(len(xcoors)):
                    eval(rimg+'_%i'%(i+1)).glyph.color_mapper.low = cbim.value[0]
                    eval(rimg+'_%i'%(i+1)).glyph.color_mapper.high = cbim.value[1]
            
        def updateBcLim():
            cbim.start = float(minCB.value)
            cbim.end = float(maxCB.value)
            
        # this function is called when the buttons are clicked
        def updateR():
            for i in range(len(xcoors)):
                eval('aperture_%i'%(i+1)).glyph.radius = float(Rp.value)
                eval('innerSky_%i'%(i+1)).glyph.radius = float(Rp.value)*1.5
                eval('outerSky_%i'%(i+1)).glyph.radius = float(Rp.value)*2
                eval('aperture_%i'%(i+1)).visible = True
                eval('innerSky_%i'%(i+1)).visible = True
                eval('outerSky_%i'%(i+1)).visible = True

        # Filter selector
        im = Select(title='Filter', value='V', options=['V', 'I'], width=150)
        im.on_change('value', updateIm)
            
        # Colobar slider and system to update the limits
        cbim = RangeSlider(title='Colorbar', start=-200, end=500, value=(15, 35), step=1, width=500)
        cbim.on_change('value', updateCb)
        buttonColorbar = Button(label='Update colorbar', width=200, align='end')
        minCB = TextInput(title='min', value='-200', width=100)
        maxCB = TextInput(title='max', value='5000', width=100)
        buttonColorbar.on_click(updateBcLim)
        
        blankSpace = Div(width=200, height=50)
                
        # System to change the size of the object aperture
        buttonRadius = Button(label='Update radius', width=200)
        Rp = TextInput(value="3", width=200)
        buttonRadius.on_click(updateR)
        
        # Layout of the overall plot
        buttons = column(im, blankSpace, buttonRadius, Rp)
        grid = gridplot(listPlots, ncols=5, width=150, height=150)
        layout = gridplot([[column(cbim, row(buttonColorbar, minCB, maxCB),grid), buttons]], merge_tools=False)
        doc.add_root(layout)
    
    # Display the interactive plot
    show(clusterDisplayGrid, notebook_url=notebook_url)
    


