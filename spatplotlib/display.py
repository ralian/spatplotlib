import json
import os
import uuid
import base64

import matplotlib.pyplot as plt
from .exporter import Exporter

from .leaflet_renderer import LeafletRenderer
from .links import JavascriptLink, CssLink
from .utils import FloatEncoder
from . import maptiles, htmlbase, htmlipynb

# TODO need newer versions of these
# We download explicitly the CSS and the JS.
_leaflet_js = JavascriptLink('https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js')
_leaflet_css = CssLink('https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.css')
_attribution = '<a href="https://github.com/ralian/spatplotlib">spatplotlib</a>'

def fig_to_html(fig=None, generator=htmlbase.format, tiles=None, crs=None,
                epsg=None, embed_links=False, float_precision=6):
    """
    Convert a Matplotlib Figure to a Leaflet map

    Parameters
    ----------
    fig : figure, default gcf()
        Figure used to convert to map
    template : string, default 'htmlbase.py'
        The Jinja2 template to use
    tiles : string or tuple
        The tiles argument is used to control the map tile source in the
        Leaflet map. Several simple shortcuts exist: 'osm', 'mapquest open',
        and 'mapbox bright' may be specified to use those tiles.

        The argument may be a tuple of two elements. The first element is the
        tile URL to use in the map's TileLayer, the second argument is the
        attribution to display.  See
        http://leafletjs.com/reference.html#tilelayer for more information on
        formatting the URL.

        See also maptiles.mapbox() for specifying Mapbox tiles based on a
        Mapbox map ID.
    crs : dict, default assumes lon/lat
        pyproj definition of the current figure. If None, then it is assumed
        the plot is longitude, latitude in X, Y.
    epsg : int, default 4326
        The EPSG code of the current plot. This can be used in place of the
        'crs' parameter.
    embed_links : bool, default False
        Whether external links (except tiles) shall be explicitly embedded in
        the final html.
    float_precision : int, default 6
        The precision to be used for the floats in the embedded geojson.

    Note: only one of 'crs' or 'epsg' may be specified. Both may be None, in
    which case the plot is assumed to be longitude / latitude.

    Returns
    -------
    String of html of the resulting webpage

    """

    tiles = maptiles.tiles[tiles] if tiles is not None else maptiles.osm

    if fig is None:
        fig = plt.gcf()
    dpi = fig.get_dpi()

    renderer = LeafletRenderer(crs=crs, epsg=epsg)
    exporter = Exporter(renderer)
    exporter.run(fig)

    FloatEncoder._formatter = ".{}f".format(float_precision)
    params = {
        'geojson': json.dumps(renderer.geojson(), cls=FloatEncoder),
        'width': fig.get_figwidth()*dpi,
        'height': fig.get_figheight()*dpi,
        'mapid': str(uuid.uuid4()).replace('-', ''),
        'tile_url': tiles[0],
        'attribution': _attribution + ' | ' + tiles[1],
        'links': [_leaflet_js,_leaflet_css],
        'embed_links': embed_links,
    }
    return generator.__call__(**params)


def fig_to_geojson(fig=None, **kwargs):
    """
    Returns a figure's GeoJSON representation as a dictionary

    All arguments passed to fig_to_html()

    Returns
    -------
    GeoJSON dictionary

    """
    if fig is None:
        fig = plt.gcf()
    renderer = LeafletRenderer(**kwargs)
    exporter = Exporter(renderer)
    exporter.run(fig)

    return renderer.geojson()


def save_html(fig=None, fileobj='_map.html', **kwargs):
    if isinstance(fileobj, str):
        fileobj = open(fileobj, 'w')
    if not hasattr(fileobj, 'write'):
        raise ValueError("fileobj should be a filename or a writable file")
    html = fig_to_html(fig, **kwargs)
    fileobj.write(html)
    fileobj.close()


def display(fig=None, closefig=True, **kwargs):
    """
    Convert a Matplotlib Figure to a Leaflet map. Embed in IPython notebook.

    Parameters
    ----------
    fig : figure, default gcf()
        Figure used to convert to map
    closefig : boolean, default True
        Close the current Figure
    """
    if fig is None:
        fig = plt.gcf()
    if closefig:
        plt.close(fig)

    html = base64.b64encode(fig_to_html(fig, **kwargs).encode('utf8')).decode('utf8')
    width = '100%'
    height = int(60. * fig.get_figheight())
    iframe_html = f"""<iframe src="data:text/html;base64,{html}" width="{width}" height="{height}"></iframe>'"""
    from IPython.display import HTML
    return HTML(iframe_html)

def show(fig=None, path='_map.html', **kwargs):
    """
    Convert a Matplotlib Figure to a Leaflet map. Open in a browser

    Parameters
    ----------
    fig : figure, default gcf()
        Figure used to convert to map
    path : string, default '_map.html'
        Filename where output html will be saved

    See fig_to_html() for description of keyword args.

    """
    import webbrowser
    fullpath = os.path.abspath(path)
    with open(fullpath, 'w') as f:
        save_html(fig, fileobj=f, **kwargs)
    webbrowser.open('file://' + fullpath)