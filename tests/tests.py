import matplotlib.pyplot as plt
import src as spatplotlib
import os

def test_basic():
    plt.plot([0, 1], [0, 1])
    spatplotlib.show()

def test_basic_tiles():
    plt.plot([0, 1], [0, 1])
    spatplotlib.show(tiles='esri_natgeo')

def test_scatter():
    plt.scatter([0, 10, 0, 10], [0, 0, 10, 10], c=[1, 2, 3, 4])
    spatplotlib.show()

test_basic_tiles()
