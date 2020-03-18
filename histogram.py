#!/usr/bin/env python3

import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

class Histogram:
    def __init__(self):
        self.images = None
        self.colors = ['b', 'r', 'g', 'c', 'm', 'y', 'k']
        self.colorindex = 0

    def getvals(self, image):
        img = Image.open(image)
        data = img.histogram()
        y_vals = np.array(data)
        x_vals = np.arange(y_vals.size)
        return x_vals, y_vals

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

#h = Histogram()
#h.images = ['burger.png', 'bburg.png', 'malburg.png']
#h.plotter()

