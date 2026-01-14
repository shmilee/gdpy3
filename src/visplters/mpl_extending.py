# -*- coding: utf-8 -*-

# Copyright (c) 2022-2026 shmilee

'''
Extend the matplotlib.

Axes3D ref
----------
1. https://gist.github.com/WetHat/1d6cd0f7309535311a539b42cccca89c
2. mpl_toolkits.mplot3d.art3d.Text3D

scale_bar ref
-------------
1. https://github.com/ppinard/matplotlib-scalebar
'''

from matplotlib.text import Annotation
from matplotlib.patches import FancyArrowPatch
from matplotlib.artist import allow_rasterization
from mpl_toolkits.mplot3d.proj3d import proj_transform
from matplotlib import cbook
from matplotlib.axes import Axes
from mpl_toolkits.mplot3d.axes3d import Axes3D

from matplotlib.patches import Rectangle, FancyBboxPatch
from matplotlib.lines import Line2D


class Annotation3D(Annotation):
    '''
    Annotation object with 3D position.
    '''

    def __str__(self):
        return "Annotation3D(%g, %g, %g, %r)" % (
            self.xy[0], self.xy[1], self.xyz[2], self._text)

    def __init__(self, text, xyz, xyztext=None, **kwargs):
        xy = xyz[:2]
        xytext = None if xyztext is None else xyztext[:2]
        Annotation.__init__(self, text, xy, xytext=xytext, **kwargs)
        self.set_3d_properties(xyz, xyztext=xyztext)

    def set_3d_properties(self, xyz, xyztext=None):
        self.xyz = xyz
        self._z = xyz[2] if xyztext is None else xyztext[2]
        self.stale = True

    @allow_rasterization
    def draw(self, renderer):
        xy = proj_transform(*self.xyz, self.axes.M)[:2]
        _x, _y, _ = proj_transform(self._x, self._y, self._z, self.axes.M)
        with cbook._setattr_cm(self, xy=xy, _x=_x, _y=_y):
            Annotation.draw(self, renderer)
        self.stale = False


def annotate3D(self, text, xyz, xyztext=None, **kwargs):
    '''
    Add anotation `text` to an `Axes3d` instance.

    Parameters
    ----------
    text: str
        The text of the annotation.
    xyz: (float, float, float)
        The point *(x, y, z)* to annotate.
    xyztext : (float, float, float), default: *xyz*
        The position *(x, y, z)* to place the text at.
    **kwargs
        Additional kwargs are passed to Axes.annotate.
    '''
    xy = xyz[:2]
    xytext = None if xyztext is None else xyztext[:2]
    annotation = super(Axes3D, self).annotate(
        text, xy, xytext=xytext, **kwargs)
    annotation.__class__ = Annotation3D
    annotation.set_3d_properties(xyz, xyztext=xyztext)
    return annotation


setattr(Axes3D, 'annotate3D', annotate3D)
setattr(Axes3D, 'annotate2D', Axes.annotate)
setattr(Axes3D, 'annotate', annotate3D)


class FancyArrowPatch3D(FancyArrowPatch):
    '''
    A fancy arrow patch with 3D positions.
    '''

    def __str__(self):
        (x1, y1, z1), (x2, y2, z2) = self._posA_posB_3D
        return f"{type(self).__name__}(({x1:g}, {y1:g}, {z1:g})->({x2:g}, {y2:g}, {z2:g}))"

    def __init__(self, posA, posB, **kwargs):
        FancyArrowPatch.__init__(self, posA=posA[:2], posB=posB[:2], **kwargs)
        self.set_3d_properties(posA, posB)

    def set_3d_properties(self, posA, posB):
        self._posA_posB_3D = [posA, posB]
        self.stale = True

    def do_3d_projection(self, renderer=None):
        (x1, y1, z1), (x2, y2, z2) = self._posA_posB_3D
        xs, ys, zs = proj_transform((x1, x2), (y1, y2), (z1, z2), self.axes.M)
        return min(zs)

    @allow_rasterization
    def draw(self, renderer):
        (x1, y1, z1), (x2, y2, z2) = self._posA_posB_3D
        xs, ys, zs = proj_transform((x1, x2), (y1, y2), (z1, z2), self.axes.M)
        _posA_posB = [(xs[0], ys[0]), (xs[1], ys[1])]
        with cbook._setattr_cm(self, _posA_posB=_posA_posB):
            FancyArrowPatch.draw(self, renderer)
        self.stale = False


def arrow3D(self, posA, posB, **kwargs):
    '''
    Add an 3d `arrow` to an `Axes3d` instance.

    Parameters
    ----------
    posA, posB : (float, float, float)
        (x, y, z) coordinates of arrow tail and arrow head respectively.
    **kwargs
        Additional kwargs are passed to `~matplotlib.patches.FancyArrowPatch`.
    '''
    arrow = FancyArrowPatch3D(posA, posB, **kwargs)
    self.add_artist(arrow)
    return arrow


setattr(Axes3D, 'arrow3D', arrow3D)
setattr(Axes3D, 'arrow2D', Axes.arrow)
setattr(Axes3D, 'arrow', Axes.arrow)


def scale_bar(ax, position, length, width, direction="horizontal",
              label=None, label_pos="right", label_pad=None,
              num_ticks=3, tick_pos="top", tick_length=0.1,
              tick_label_pad=None, tick_label_format=None,
              color="black", linewidth=1, fontsize=10,
              box_color=None, box_alpha=0.8,
              box_padding=None, box_corner_radius=0.0,
              box_style="round", mutation_scale=1.0):
    """
    Add a simplified scale bar to the axes with customizable options.

    Parameters
    ----------
    ax: matplotlib axes object
    position: (x, y) data coordinates for bottom-left corner of scale bar
    length: length of the scale bar in data units
    width: width of the scale bar in data units
    direction: scale bar direction ("horizontal" or "vertical")
    label: text label for scale bar (e.g., "m", "km") - shown as unit label
    label_pos: position of unit label relative to scale bar ("top", "bottom", "left", "right")
    label_pad: padding between unit label and scale bar in the label_pos direction
    num_ticks: number of ticks (including ends)
    tick_pos: position of tick relative to scale bar ("top", "bottom", "left", "right")
    tick_length: tick length in data units
    tick_label_pad: padding between tick labels and scale bar in the tick_pos direction
    tick_label_format: format string for tick labels (e.g., "{:.1f}")
    color: color of scale bar and ticks
    linewidth: line width
    fontsize: font size for labels
    box_color: background color for border box, None to disable box
    box_alpha: transparency of border box
    box_padding: padding around elements in data units as (horizontal_pad, vertical_pad) or single value for both
    box_corner_radius: corner radius of the box in data units (only for round box style)
    box_style: style of the box ("round", "round4", "roundtooth", "sawtooth", "square")
    mutation_scale: scale factor for box style mutation (affects tooth size, etc.)

    Returns
    -------
    Dictionary of created artists
    """
    x0, y0 = position
    # Create scale bar body
    bar = Rectangle(
        (x0, y0),
        length if direction == "horizontal" else width,
        width if direction == "horizontal" else length,
        linewidth=linewidth,
        edgecolor=color,
        facecolor=color,
        zorder=6,
    )
    ax.add_patch(bar)

    # set default tick_pos
    if direction == "horizontal" and tick_pos not in ("top", "bottom"):
        tick_pos = "top"
    elif direction == "vertical" and tick_pos not in ("left", "right"):
        tick_pos = "right"

    # Set default paddings if not specified
    if label_pad is None:
        label_pad = tick_length * 1.2
    if tick_label_pad is None:
        tick_label_pad = tick_length * 1.2

    # Track bounds for box calculation
    if direction == "horizontal":
        bar_width = length
        bar_height = width
        min_x = x0
        max_x = x0 + bar_width
        if tick_pos == "top":
            min_y = y0
            max_y = y0 + bar_height + tick_length
        else:  # bottom
            min_y = y0 - tick_length
            max_y = y0 + bar_height
    else:  # vertical
        bar_width = width
        bar_height = length
        min_y = y0
        max_y = y0 + bar_height
        if tick_pos == "right":
            min_x = x0
            max_x = x0 + bar_width + tick_length
        else:  # left
            min_x = x0 - tick_length
            max_x = x0 + bar_width

    # Create ticks and labels
    ticks = []
    tick_labels = []
    for i in range(num_ticks):
        t = i / (num_ticks - 1) if num_ticks > 1 else 0
        x_tick = x0 + t * length
        # Create tick line, get position of tick label
        if direction == "horizontal":
            x_tick = x0 + t * bar_width
            if tick_pos == "top":
                tick_line = Line2D(
                    [x_tick, x_tick],
                    [y0 + bar_height, y0 + bar_height + tick_length],
                    color=color,
                    linewidth=linewidth,
                    zorder=6,
                )
                tick_label_x = x_tick
                tick_label_y = y0 + bar_height + tick_label_pad
                ha = 'center'
                va = 'bottom'
            else:  # bottom
                tick_line = Line2D(
                    [x_tick, x_tick],
                    [y0, y0 - tick_length],
                    color=color,
                    linewidth=linewidth,
                    zorder=6,
                )
                tick_label_x = x_tick
                tick_label_y = y0 - tick_label_pad
                ha = 'center'
                va = 'top'
        else:  # vertical
            y_tick = y0 + t * bar_height
            if tick_pos == "right":
                tick_line = Line2D(
                    [x0 + bar_width, x0 + bar_width + tick_length],
                    [y_tick, y_tick],
                    color=color,
                    linewidth=linewidth,
                    zorder=6,
                )
                tick_label_x = x0 + bar_width + tick_label_pad
                tick_label_y = y_tick
                ha = 'left'
                va = 'center'
            else:  # left
                tick_line = Line2D(
                    [x0, x0 - tick_length],
                    [y_tick, y_tick],
                    color=color,
                    linewidth=linewidth,
                    zorder=6,
                )
                tick_label_x = x0 - tick_label_pad
                tick_label_y = y_tick
                ha = 'right'
                va = 'center'
        ax.add_line(tick_line)
        ticks.append(tick_line)
        # Create tick label (scale value)
        if i == 0:
            tick_label_text = "0"
        elif i == num_ticks - 1:
            if tick_label_format:
                tick_label_text = tick_label_format.format(length)
            elif float(length).is_integer():
                tick_label_text = str(int(length))
            else:
                tick_label_text = f"{length:.2f}"
        else:
            label_value = t * length
            if tick_label_format:
                tick_label_text = tick_label_format.format(label_value)
            elif float(label_value).is_integer():
                tick_label_text = str(int(label_value))
            else:
                tick_label_text = f"{label_value:.2f}"
        # Position tick label based on label_pos
        tick_label = ax.text(
            tick_label_x,
            tick_label_y,
            tick_label_text,
            fontsize=fontsize,
            color=color,
            ha=ha,
            va=va,
            zorder=6,
        )
        tick_labels.append(tick_label)

    # Create unit label (e.g., "m", "km")
    unit_label = None
    if label:
        if direction == "horizontal":
            if label_pos == "top":
                label_x = x0 + bar_width / 2
                label_y = y0 + bar_height + label_pad
                ha = 'center'
                va = 'bottom'
            elif label_pos == "bottom":
                label_x = x0 + bar_width / 2
                # Find the lowest tick label position
                tick_label_bottom = min(tick_label.get_position()[1]
                                        for tick_label in tick_labels)
                label_y = tick_label_bottom - label_pad
                ha = 'center'
                va = 'top'
            elif label_pos == "left":
                label_x = x0 - label_pad
                label_y = y0 + bar_height / 2
                ha = 'right'
                va = 'center'
            elif label_pos == "right":
                label_x = x0 + bar_width + label_pad
                label_y = y0 + bar_height / 2
                ha = 'left'
                va = 'center'
        else:  # vertical
            if label_pos == "top":
                label_x = x0 + bar_width / 2
                label_y = y0 + bar_height + label_pad
                ha = 'center'
                va = 'bottom'
            elif label_pos == "bottom":
                label_x = x0 + bar_width / 2
                label_y = y0 - label_pad
                ha = 'center'
                va = 'top'
            elif label_pos == "left":
                label_x = x0 - label_pad
                label_y = y0 + bar_height / 2
                ha = 'right'
                va = 'center'
            elif label_pos == "right":
                # Find the rightmost tick label position
                tick_label_right = max(tick_label.get_position()[0]
                                       for tick_label in tick_labels)
                label_x = tick_label_right + label_pad
                label_y = y0 + bar_height / 2
                ha = 'left'
                va = 'center'
        unit_label = ax.text(
            label_x,
            label_y,
            label,
            fontsize=fontsize,
            color=color,
            ha=ha,
            va=va,
            zorder=6,
        )

    # Create border box
    box = None
    if box_color and box_alpha > 0:
        # Process box_padding
        if box_padding is None:
            if direction == "horizontal":
                box_padding = (bar_width * 0.05, bar_height * 0.5)
            else:
                box_padding = (bar_width * 0.5, bar_height * 0.05)
        elif isinstance(box_padding, (int, float)):
            box_padding = (box_padding, box_padding)
        elif len(box_padding) != 2:
            raise ValueError(
                "box_padding must be a single value or a tuple of (horizontal, vertical)")
        h_pad, v_pad = box_padding
        # Initialize bounds based on bar and ticks
        left = min_x - h_pad
        right = max_x + h_pad
        bottom = min_y - v_pad
        top = max_y + v_pad
        # Adjust bounds to include unit label if present
        if unit_label:
            # Get unit label position
            label_pos_data = unit_label.get_position()
            # Estimate text extents (approximate based on fontsize)
            # In a more precise implementation, you might want to use
            # renderer to get exact text dimensions
            text_width_est = len(label) * fontsize * 0.006
            text_height_est = fontsize * 0.012
            if label_pos == "top":
                top = max(top, label_pos_data[1] + text_height_est + v_pad)
            elif label_pos == "bottom":
                bottom = min(bottom, label_pos_data[1]-text_height_est-v_pad)
            elif label_pos == "left":
                left = min(left, label_pos_data[0] - text_width_est - h_pad)
            elif label_pos == "right":
                right = max(right, label_pos_data[0] + text_width_est + h_pad)
        width = right - left
        height = top - bottom
        # Create box with specified style
        if box_style == "square":
            # Use Rectangle for square corners
            box = Rectangle(
                (left, bottom),
                width,
                height,
                linewidth=linewidth * 0.5,
                edgecolor=color,
                facecolor=box_color,
                alpha=box_alpha,
                zorder=5,  # Box behind scale bar
            )
        else:
            # Use FancyBboxPatch for special box styles
            # Build boxstyle string based on box_style parameter
            if box_style in ["round", "round4"]:
                # Calculate relative corner radius for rounded styles
                if box_corner_radius > 0:
                    min_dim = min(width, height)
                    if min_dim > 0:
                        relative_radius = box_corner_radius / min_dim
                        # Cap the relative radius to prevent extreme values
                        relative_radius = min(relative_radius, 0.5)
                    else:
                        relative_radius = 0.1
                else:
                    relative_radius = 0.1
                boxstyle_str = f"{box_style},pad=0,rounding_size={relative_radius}"
            elif box_style in ["roundtooth", "sawtooth"]:
                # Tooth styles - mutation_scale control size
                boxstyle_str = f"{box_style},pad=0.1"
            else:
                # Default to round style with minimal rounding
                boxstyle_str = f"round,pad=0.1,rounding_size=0.1"
            # Create the box with mutation_scale parameter
            box = FancyBboxPatch(
                (left, bottom),
                width,
                height,
                boxstyle=boxstyle_str,
                linewidth=linewidth * 0.5,
                edgecolor=color,
                facecolor=box_color,
                alpha=box_alpha,
                zorder=5,  # Box behind scale bar
                mutation_scale=mutation_scale,
            )
        ax.add_patch(box)

    return {
        'bar': bar,
        'ticks': ticks,
        'tick_labels': tick_labels,
        'unit_label': unit_label,
        'box': box
    }
