import itertools
import json
from json.encoder import JSONEncoder
import warnings

import matplotlib
from matplotlib import ticker
from matplotlib.colors import colorConverter
from matplotlib.path import Path
from matplotlib.markers import MarkerStyle
from matplotlib.transforms import Affine2D

from string import Formatter

import numpy as np

def _many_to_one(input_dict):
    """Convert a many-to-one mapping to a one-to-one mapping"""
    return dict((key, val)
                for keys, val in input_dict.items()
                for key in keys)

LINESTYLES = _many_to_one({('solid', '-', (None, None)): 'none',
                           ('dashed', '--'): "6,6",
                           ('dotted', ':'): "2,2",
                           ('dashdot', '-.'): "4,4,2,4",
                           ('', ' ', 'None', 'none'): None})


PATH_DICT = {Path.LINETO: 'L',
             Path.MOVETO: 'M',
             Path.CURVE3: 'S',
             Path.CURVE4: 'C',
             Path.CLOSEPOLY: 'Z'}


def SVG_path(path, transform=None, simplify=False):
    """Construct the vertices and SVG codes for the path

    Parameters
    ----------
    path : matplotlib.Path object

    transform : matplotlib transform (optional)
        if specified, the path will be transformed before computing the output.

    Returns
    -------
    vertices : array
        The shape (M, 2) array of vertices of the Path. Note that some Path
        codes require multiple vertices, so the length of these vertices may
        be longer than the list of path codes.
    path_codes : list
        A length N list of single-character path codes, N <= M. Each code is
        a single character, in ['L','M','S','C','Z']. See the standard SVG
        path specification for a description of these.
    """
    if transform is not None:
        path = path.transformed(transform)

    vc_tuples = [(vertices if path_code != Path.CLOSEPOLY else [],
                  PATH_DICT[path_code])
                 for (vertices, path_code)
                 in path.iter_segments(simplify=simplify)]

    if not vc_tuples:
        # empty path is a special case
        return np.zeros((0, 2)), []
    else:
        vertices, codes = zip(*vc_tuples)
        vertices = np.array(list(itertools.chain(*vertices))).reshape(-1, 2)
        return vertices, list(codes)


class StrMethodTickFormatterConvertor(object):
    STRING_FORMAT_D3 = "d3-format"

    SUPPORTED_OUTPUT_FORMATS = (
        STRING_FORMAT_D3,
    )

    def __init__(self, formatter, output_format=STRING_FORMAT_D3):
        assert output_format in self.SUPPORTED_OUTPUT_FORMATS, "Unknown output_format"
        if not isinstance(formatter, matplotlib.ticker.StrMethodFormatter):
            raise ValueError("Formatter must be of type `matplotlib.ticker.StrMethodFormatter`")
        self.formatter = formatter
        self.output_format = output_format

    @property
    def is_output_d3(self):
        return self.output_format == self.STRING_FORMAT_D3

    def export_mpl_format_str_d3(self, mpl_format_str):
        prefixes = []
        suffixes = []
        before_x = True
        format_spec_for_d3 = ""
        for literal_text, field_name, format_spec, conversion in Formatter().parse(mpl_format_str):
            if before_x:
                prefixes.append(literal_text)
            else:
                suffixes.append(literal_text)

            if field_name == "x" and format_spec and format_spec_for_d3 and self.is_output_d3:
                raise ValueError("D3 doesn't support multiple conversions")

            if field_name == "x":
                before_x = False
                format_spec_for_d3 = format_spec

        prefix = "".join(prefixes)
        suffix = "".join(suffixes)
        return {
            "format_string": format_spec_for_d3,
            "prefix": prefix,
            "suffix": suffix
        }

    @property
    def output(self):
        # just incase we want to support something other than d3
        if self.is_output_d3:
            return self.export_mpl_format_str_d3(self.formatter.fmt)


def get_marker_style(line):
    """Get the style dictionary for matplotlib marker objects"""
    style = {}
    style['alpha'] = line.get_alpha()
    if style['alpha'] is None:
        style['alpha'] = 1

    style['facecolor'] = export_color(line.get_markerfacecolor())
    style['edgecolor'] = export_color(line.get_markeredgecolor())
    style['edgewidth'] = line.get_markeredgewidth()

    style['marker'] = line.get_marker()
    markerstyle = matplotlib.markers.MarkerStyle(line.get_marker())
    markersize = line.get_markersize()
    markertransform = (markerstyle.get_transform()
                       + matplotlib.transforms.Affine2D().scale(markersize, -markersize))
    style['markerpath'] = SVG_path(markerstyle.get_path(),
                                   markertransform)
    style['markersize'] = markersize
    style['zorder'] = line.get_zorder()
    return style


def get_text_style(text):
    """Return the text style dict for a text instance"""
    style = {}
    style['alpha'] = text.get_alpha()
    if style['alpha'] is None:
        style['alpha'] = 1
    style['fontsize'] = text.get_size()
    style['color'] = export_color(text.get_color())
    style['halign'] = text.get_horizontalalignment()  # left, center, right
    style['valign'] = text.get_verticalalignment()  # baseline, center, top
    style['malign'] = text._multialignment # text alignment when '\n' in text
    style['rotation'] = text.get_rotation()
    style['zorder'] = text.get_zorder()
    return style


def get_dasharray(obj):
    """Get an SVG dash array for the given matplotlib linestyle

    Parameters
    ----------
    obj : matplotlib object
        The matplotlib line or path object, which must have a get_linestyle()
        method which returns a valid matplotlib line code

    Returns
    -------
    dasharray : string
        The HTML/SVG dasharray code associated with the object.
    """
    if obj.__dict__.get('_dashSeq', None) is not None:
        return ','.join(map(str, obj._dashSeq))
    else:
        ls = obj.get_linestyle()
        dasharray = LINESTYLES.get(ls, 'not found')
        if dasharray == 'not found':
            warnings.warn(f"line style '{ls}' not understood. Defaulting to solid line.")
            dasharray = LINESTYLES['solid']
        return dasharray


def export_color(color):
    """Convert matplotlib color code to hex color or RGBA color"""
    if color is None or colorConverter.to_rgba(color)[3] == 0:
        return 'none'
    elif colorConverter.to_rgba(color)[3] == 1:
        rgb = colorConverter.to_rgb(color)
        return '#{0:02X}{1:02X}{2:02X}'.format(*(int(255 * c) for c in rgb))
    else:
        c = colorConverter.to_rgba(color)
        return "rgba(" + ", ".join(str(int(val * 255))
                                        for val in c[:3])+', '+str(c[3])+")"


def get_path_style(path, fill=True):
    """Get the style dictionary for matplotlib path objects"""
    style = dict()
    style['alpha'] = path.get_alpha()
    if style['alpha'] is None:
        style['alpha'] = 1
    style['edgecolor'] = export_color(path.get_edgecolor())
    if fill:
        style['facecolor'] = export_color(path.get_facecolor())
    else:
        style['facecolor'] = 'none'
    style['edgewidth'] = path.get_linewidth()
    style['dasharray'] = get_dasharray(path)
    style['zorder'] = path.get_zorder()
    return style


def get_line_style(line):
    """Get the style dictionary for matplotlib line objects"""
    style = dict()
    style['alpha'] = line.get_alpha()
    if style['alpha'] is None:
        style['alpha'] = 1
    style['color'] = export_color(line.get_color())
    style['linewidth'] = line.get_linewidth()
    style['dasharray'] = get_dasharray(line)
    style['zorder'] = line.get_zorder()
    style['drawstyle'] = line.get_drawstyle()
    return style


def iter_rings(data, pathcodes):
    ring = []
    # TODO: Do this smartly by finding when pathcodes changes value and do
    # smart indexing on data, instead of iterating over each coordinate
    for point, code in zip(data, pathcodes):
        if code == 'M':
            # Emit the path and start a new one
            if len(ring):
                yield ring
            ring = [point]
        elif code == 'L' or code == 'Z' or code == 'S':
            ring.append(point)
        else:
            raise ValueError('Unrecognized code: {}'.format(code))

    if len(ring):
        yield ring


def get_figure_properties(fig):
    return {'figwidth': fig.get_figwidth(),
            'figheight': fig.get_figheight(),
            'dpi': fig.dpi}


def get_grid_style(axis):
    gridlines = axis.get_gridlines()
    if axis._major_tick_kw['gridOn'] and len(gridlines) > 0:
        color = export_color(gridlines[0].get_color())
        alpha = gridlines[0].get_alpha()
        dasharray = get_dasharray(gridlines[0])
        return dict(gridOn=True,
                    color=color,
                    dasharray=dasharray,
                    alpha=alpha)
    else:
        return {"gridOn": False}


def get_axis_properties(axis):
    """Return the property dictionary for a matplotlib.Axis instance"""
    props = {}
    label1On = axis._major_tick_kw.get('label1On', True)

    if isinstance(axis, matplotlib.axis.XAxis):
        if label1On:
            props['position'] = "bottom"
        else:
            props['position'] = "top"
    elif isinstance(axis, matplotlib.axis.YAxis):
        if label1On:
            props['position'] = "left"
        else:
            props['position'] = "right"
    else:
        raise ValueError("{0} should be an Axis instance".format(axis))

    # Use tick values if appropriate
    locator = axis.get_major_locator()
    props['nticks'] = len(locator())
    if isinstance(locator, ticker.FixedLocator):
        props['tickvalues'] = list(locator())
    else:
        props['tickvalues'] = None

    # Find tick formats
    props['tickformat_formatter'] = ""
    formatter = axis.get_major_formatter()
    if isinstance(formatter, ticker.NullFormatter):
        props['tickformat'] = ""
    elif isinstance(formatter, ticker.StrMethodFormatter):
        convertor = StrMethodTickFormatterConvertor(formatter)
        props['tickformat'] = convertor.output
        props['tickformat_formatter'] = "str_method"
    elif isinstance(formatter, ticker.PercentFormatter):
        props['tickformat'] = {
            "xmax": formatter.xmax,
            "decimals": formatter.decimals,
            "symbol": formatter.symbol,
        }
        props['tickformat_formatter'] = "percent"
    elif hasattr(ticker, 'IndexFormatter') and isinstance(formatter, ticker.IndexFormatter):
        # IndexFormatter was dropped in matplotlib 3.5
        props['tickformat'] = [text.get_text() for text in axis.get_ticklabels()]
        props['tickformat_formatter'] = "index"
    elif isinstance(formatter, ticker.FixedFormatter):
        props['tickformat'] = list(formatter.seq)
        props['tickformat_formatter'] = "fixed"
    elif not any(label.get_visible() for label in axis.get_ticklabels()):
        props['tickformat'] = ""
    else:
        props['tickformat'] = None

    # Get axis scale
    props['scale'] = axis.get_scale()

    # Get major tick label size (assumes that's all we really care about!)
    labels = axis.get_ticklabels()
    if labels:
        props['fontsize'] = labels[0].get_fontsize()
    else:
        props['fontsize'] = None

    # Get associated grid
    props['grid'] = get_grid_style(axis)

    # get axis visibility
    props['visible'] = axis.get_visible()

    return props

def get_axes_properties(ax):
    props = {'axesbg': export_color(ax.patch.get_facecolor()),
             'axesbgalpha': ax.patch.get_alpha(),
             'bounds': ax.get_position().bounds,
             'dynamic': ax.get_navigate(),
             'axison': ax.axison,
             'frame_on': ax.get_frame_on(),
             'patch_visible':ax.patch.get_visible(),
             'axes': [get_axis_properties(ax.xaxis),
                      get_axis_properties(ax.yaxis)]}

    for axname in ['x', 'y']:
        axis = getattr(ax, axname + 'axis')
        domain = getattr(ax, 'get_{0}lim'.format(axname))()
        lim = domain
        if (
            (
                hasattr(matplotlib.dates, '_SwitchableDateConverter') and
                isinstance(axis.converter, matplotlib.dates._SwitchableDateConverter)
            ) or (
                hasattr(matplotlib.dates, 'DateConverter') and
                isinstance(axis.converter, matplotlib.dates.DateConverter)
            ) or (
                hasattr(matplotlib.dates, 'ConciseDateConverter') and
                isinstance(axis.converter, matplotlib.dates.ConciseDateConverter)
            )
        ):
            scale = 'date'
            try:
                import pandas as pd
                from pandas.tseries.converter import PeriodConverter
            except ImportError:
                pd = None

            if (pd is not None and isinstance(axis.converter,
                                              PeriodConverter)):
                _dates = [pd.Period(ordinal=int(d), freq=axis.freq)
                          for d in domain]
                domain = [(d.year, d.month - 1, d.day,
                           d.hour, d.minute, d.second, 0)
                          for d in _dates]
            else:
                domain = [(d.year, d.month - 1, d.day,
                           d.hour, d.minute, d.second,
                           d.microsecond * 1E-3)
                          for d in matplotlib.dates.num2date(domain)]
        else:
            scale = axis.get_scale()

        if scale not in ['date', 'linear', 'log']:
            raise ValueError("Unknown axis scale: "
                             "{0}".format(axis.get_scale()))

        props[axname + 'scale'] = scale
        props[axname + 'lim'] = lim
        props[axname + 'domain'] = domain

    return props


class FloatEncoder(JSONEncoder):
    _formatter = ".3f"

    def iterencode(self, o, _one_shot=False):
        """Encode the given object and yield each string
        representation as available.
        For example::
            for chunk in JSONEncoder().iterencode(bigobject):
                mysocket.write(chunk)
        """
        c_make_encoder_original = json.encoder.c_make_encoder
        json.encoder.c_make_encoder = None

        if self.check_circular:
            markers = {}
        else:
            markers = None
        if self.ensure_ascii:
            _encoder = json.encoder.encode_basestring_ascii
        else:
            _encoder = json.encoder.encode_basestring

        def floatstr(o, allow_nan=self.allow_nan,
                     _repr=lambda x: format(x, self._formatter),
                     _inf=float("inf"), _neginf=-float("inf")):
            # Check for specials.  Note that this type of test is processor
            # and/or platform-specific, so do tests which don't depend on the
            # internals.
            if o != o:
                text = 'NaN'
            elif o == _inf:
                text = 'Infinity'
            elif o == _neginf:
                text = '-Infinity'
            else:
                return _repr(o)

            if not allow_nan:
                raise ValueError(
                    "Out of range float values are not JSON compliant: " +
                    repr(o))

            return text

        if (_one_shot and json.encoder.c_make_encoder is not None
                and self.indent is None):
            _iterencode = json.encoder.c_make_encoder(
                markers, self.default, _encoder, self.indent,
                self.key_separator, self.item_separator, self.sort_keys,
                self.skipkeys, self.allow_nan)
        else:
            _iterencode = json.encoder._make_iterencode(
                markers, self.default, _encoder, self.indent, floatstr,
                self.key_separator, self.item_separator, self.sort_keys,
                self.skipkeys, _one_shot)
        json.encoder.c_make_encoder = c_make_encoder_original
        return _iterencode(o, 0)