import matplotlib.pyplot as plt
import src as spatplotlib
import os

def test_basic():
    plt.plot([0, 1], [0, 1])
    with open('test_basic.html', 'w') as fout:
        fout.write(spatplotlib.fig_to_html())
    os.system("start file://" + os.path.realpath('test_basic.html'))

def test_basic_tiles():
    plt.plot([0, 1], [0, 1])
    with open('test_basic_tiles.html', 'w') as fout:
        fout.write(spatplotlib.fig_to_html(tiles='osm'))
    os.system("start file://" + os.path.realpath('test_basic_tiles.html'))


def test_scatter():
    plt.scatter([0, 10, 0, 10], [0, 0, 10, 10], c=[1, 2, 3, 4])
    with open('test_scatter.html', 'w') as fout:
        fout.write(spatplotlib.fig_to_html())
    os.system("start file://" + os.path.realpath('test_scatter.html'))

test_scatter()
