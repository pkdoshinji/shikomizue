#!/usr/bin/env python3

'''
Implementation of the Histogram class for plotting superimposed RGB histograms
of input and output image files associated with the shikomizue steganographic
binary tool
'''

import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

#Histogram class
class Histogram:
    def __init__(self):
        self.images = None #Should be entered as a list
        self.colors = ['b', 'r', 'g', 'c', 'm', 'y', 'k']
        self.colorindex = 0
    
    
    #Get the data values for the RGB histogram
    def getvals(self, image):
        img = Image.open(image)
        data = img.histogram()
        y_vals = np.array(data)
        x_vals = np.arange(y_vals.size)
        return x_vals, y_vals


    #When plotter() is called, a superimposed histogram plot is created from
    #all of the images in self.images
    def plotter(self, output_name=None):
        fig = plt.figure()
        ax = plt.subplot(111)

        for image in self.images:
            #print(image)
            (xvals, yvals) = self.getvals(image)
            #print(xvals,yvals)
            ax.plot(xvals, yvals, color=self.colors[self.colorindex], label=f'{image}')
            ax.legend()
            self.colorindex = (self.colorindex + 1)%(len(self.colors))
        plt.show()


