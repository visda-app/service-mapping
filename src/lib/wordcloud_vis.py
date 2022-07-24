"""
A library to visualize a set of texts in a word cloud format
"""


import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import random
from dataclasses import dataclass

from uuid import uuid4

from math import sin, cos
import numpy as np
from copy import deepcopy
from typing import List


def _get_text_with_height(text, font_size, silent_mode=True):
    fig, ax = plt.subplots()
    if silent_mode:
        plt.close(fig)  # Avoid displaying the plot

    plt_text = ax.text(
        0, 0, text,
        horizontalalignment='center',
        verticalalignment='center',
        fontsize=font_size,
        visible=True,
    )
    r = fig.canvas.get_renderer()
    bb = plt_text.get_window_extent(renderer=r).transformed(fig.gca().transData.inverted())
    if silent_mode:
        fig.clear()
    return bb.width, bb.height


@dataclass(unsafe_hash=False)
class Pos:
    x: float
    y: float
        
    def __hash__(self):
        return hash((self.x, self.y))


@dataclass
class Circle:
    c: Pos
    r: float
    layer_number: int = 0

        
@dataclass 
class Rectangle:
    c: Pos  # center of the rectangle
    width: float
    height: float
    layer_number: int = 0
    label: str= None
    uuid: str= None
        
    def __post_init__(self):
        if self.uuid is None:
            self.uuid = str(uuid4())
        if self.width < 0:
            self.width = -self.width
        if self.height < 0:
            self.height = -self.height
            
            
@dataclass
class TextBoxItem:
    text: str
    font_size: float
    c: Pos = None
    width: float = None
    height: float = None
    layer_number: int = None
    bbox_uuid: str = None
    bbox: Rectangle = None
    
    def __post_init__(self):
        self.font_size = round(self.font_size, 2)

        if self.width is None or self.height is None:
            width, height = _get_text_with_height(self.text, self.font_size)
        if self.width is None:
            self.width = round(width, 3)
        if self.height is None:
            self.height = round(height, 3)


def find_bound(shapes):
    x_min = float('inf')
    x_max = float('-inf')
    y_min = float('inf')
    y_max = -float('inf')
    for shape in shapes:
        if type(shape) == Circle:
            x_min = min(x_min, shape.c.x - shape.r)
            x_max = max(x_max, shape.c.x + shape.r)
            y_min = min(y_min, shape.c.y - shape.r)
            y_max = max(y_max, shape.c.y + shape.r)
        if type(shape) == Rectangle or type(shape) == TextBoxItem:
            x_min = min(x_min, shape.c.x - shape.width / 2)
            x_max = max(x_max, shape.c.x + shape.width / 2)
            y_min = min(y_min, shape.c.y - shape.height / 2)
            y_max = max(y_max, shape.c.y + shape.height / 2)
    return x_min, x_max, y_min, y_max


def draw(shapes, text_font_scale):
    x_min, x_max, y_min, y_max = find_bound(shapes)

    fig, ax = plt.subplots(figsize=(x_max - x_min, y_max - y_min))
    ax.axis([x_min, x_max, y_min, y_max])
    
    color_list = list(mcolors.TABLEAU_COLORS)
    color_index = 0

    for shape in shapes:
        color_name = color_list[color_index]
        color_index = (color_index + 1) % len(color_list)

        if shape.layer_number is not None:
            color_name = color_list[shape.layer_number % len(color_list)]
        if type(shape) == Circle:
            circle = plt.Circle(
                (shape.c.x, shape.c.y),
                shape.r,
                fill=False,
                color=color_name,
            )
            ax.add_patch(circle)
        if type(shape) == Rectangle:
            c = shape.c
            hw = shape.width / 2
            hh = shape.height / 2
            ax.plot(
                [c.x - hw, c.x + hw, c.x + hw, c.x - hw, c.x - hw], 
                [c.y - hh, c.y - hh, c.y + hh, c.y + hh, c.y - hh],
                color=color_name,
            )
#             d = 0.1
#             ax.plot(
#                 [c.x - hw + d, c.x + hw - d, c.x + hw - d, c.x - hw + d, c.x - hw + d],
#                 [c.y - hh + d, c.y - hh + d, c.y + hh - d, c.y + hh - d, c.y - hh + d],
#                 color=color_name,
#             )
        if type(shape) == TextBoxItem:
            c = shape.c
            hw = shape.width / 2
            hh = shape.height / 2
            ax.text(
                c.x, c.y, shape.text,
                horizontalalignment='center',
                verticalalignment='center',
                fontsize=shape.font_size * text_font_scale,
                visible=True,
                color=color_name,
            )


def _is_point_in_rect(p: Pos, rect: Rectangle):
    """
    Checks if a point is inside a rectangle
    """
    x1 = rect.c.x - rect.width / 2
    x2 = rect.c.x + rect.width / 2
    y1 = rect.c.y - rect.height / 2
    y2 = rect.c.y + rect.height / 2
    if (p.x >= x1 and p.x <= x2 and p.y >= y1 and p.y <= y2):
        return True
    return False


def _does_line_bifurcate_rect(line: Rectangle, rect: Rectangle):
    if line.width != 0 and line.height != 0:
        raise Exception(f"Invalid line {line}")
    if line.width == 0:
        p1 = Pos(line.c.x, line.c.y - line.height / 2)
        p2 = Pos(line.c.x, line.c.y + line.height / 2)
        if (
            p1.y <= rect.c.y - rect.height / 2 
            and p2.y >= rect.c.y + rect.height / 2
            and p1.x >= rect.c.x - rect.width / 2 
            and p1.x <= rect.c.x + rect.width / 2
        ):
            return True
    if line.height == 0:
        p1 = Pos(line.c.x - line.width / 2, line.c.y)
        p2 = Pos(line.c.x + line.width / 2, line.c.y)
        if (
            p1.x <= rect.c.x - rect.width / 2 
            and p2.x >= rect.c.x + rect.width / 2
            and p1.y >= rect.c.y - rect.height / 2 
            and p1.y <= rect.c.y + rect.height / 2
        ):
            return True
    return False


def _get_rect_corners(r: Rectangle):
    return [
        Pos(r.c.x - r.width / 2, r.c.y - r.height / 2),
        Pos(r.c.x + r.width / 2, r.c.y - r.height / 2),
        Pos(r.c.x - r.width / 2, r.c.y + r.height / 2),
        Pos(r.c.x + r.width / 2, r.c.y + r.height / 2),
    ]


def _get_rect_lines(r: Rectangle):
    return[
        Rectangle(Pos(r.c.x - r.width / 2, r.c.y), 0, r.height),
        Rectangle(Pos(r.c.x + r.width / 2, r.c.y), 0, r.height),
        Rectangle(Pos(r.c.x, r.c.y - r.height / 2), r.width, 0),
        Rectangle(Pos(r.c.x, r.c.y + r.height / 2), r.width, 0),
    ]


def _is_colliding(rect1: Rectangle, rect2: Rectangle):
    if rect1 is None or rect2 is None:
        return False
    rect1_points = _get_rect_corners(rect1)
    rect2_points = _get_rect_corners(rect2)
    if any([_is_point_in_rect(p, rect2) for p in rect1_points]):
        return True
    if any([_is_point_in_rect(p, rect1) for p in rect2_points]):
        return True
    if any(_does_line_bifurcate_rect(l, rect2) for l in _get_rect_lines(rect1) ): 
        return True
    if any(_does_line_bifurcate_rect(l, rect1) for l in _get_rect_lines(rect2) ): 
        return True
    return False




def _is_colliding_with_any(rect: Rectangle, rects: list):
    for r in rects:
        if _is_colliding(r, rect):
            return True
    return False


def theta(r):
    a_prime_number = 173
    return (a_prime_number * r) ** 5


def _generate_xy_coords_in_circle(max_r, num_items):
    num_steps = 10 * num_items
    radius = max_r * np.sqrt(np.array(range(num_steps)) / num_steps)
    coords = [Pos(r * cos(theta(r)), r * sin(theta(r))) for r in radius]
    return coords


def fit_rectangles_in_circle_non_colliding(
    rects: List[Rectangle],
    radius: float,
    forbidden_coords: set=set(),
    layer_number: int=0
):
    """
    Finds the positions of rectangles in a circle such that they don't collide
    and the taller rectangles are closer to the center
    """
    rects = deepcopy(rects)
    rects.sort(key=lambda x: -x.height)
    search_space_coords = _generate_xy_coords_in_circle(radius, len(rects) )
    forbidden_coords = deepcopy(forbidden_coords)
    drawn_rects = []
    not_drawn_rects = []
    blocked_coords = set()
    for rect in rects:
        seen_coords = set()
        for i, xy in enumerate(search_space_coords):
            if xy in blocked_coords or xy in forbidden_coords:
                continue
            seen_coords.add(xy)
            rect.c = Pos(xy.x, xy.y)
            rect.layer_number = layer_number
            if not _is_colliding_with_any( rect, drawn_rects ):
                drawn_rects.append(rect)
                forbidden_coords.add(xy)
                # blocks those coordinate point inside the rect
                for xy in seen_coords:
                    if xy not in blocked_coords and _is_point_in_rect(xy, rect):
                        blocked_coords.add(xy)
                break
        if i == len(search_space_coords) - 1:
            not_drawn_rects.append(rect)

    return drawn_rects, not_drawn_rects, blocked_coords, forbidden_coords


def _fit_text_items_in_circle(texts: List[TextBoxItem], radius):
    texts = deepcopy(texts)

    rectangles = []
    for t in texts:
        rect = Rectangle(c=None, width=t.width, height=t.height)
        t.bbox_id = rect.uuid
        rectangles.append(rect)

    not_drawn_items = rectangles
    drawn_rects = []
    forbidden_coords = set()
    blocked_coords = []
    layer_number = 1
    while not_drawn_items:
        drawn_rects_, not_drawn_items, blocked_coords_, forbidden_coords = fit_rectangles_in_circle_non_colliding(
            not_drawn_items, radius, forbidden_coords, layer_number
        )
        blocked_coords.extend(blocked_coords_)
        drawn_rects.extend(drawn_rects_)
        # print(f"Iteration #{layer_number}: len(drawn_rects)={len(drawn_rects)}, len(not_drawn_rects)={len(not_drawn_items)}")
        layer_number += 1
    
    rects_by_id = {r.uuid: r for r in drawn_rects}

    for text in texts:
        # print(f"rects_by_id[text.bbox_id]={rects_by_id[text.bbox_id]}")
        text.bbox = rects_by_id[text.bbox_id]
        text.layer_number = text.bbox.layer_number
        text.c = text.bbox.c
    return texts


def _get_text_item_from_text(texts: List[dict], font_scale=1):
    """
    Input
        texts:  A list of dictionaries 
                [{'text': 'example', 'frequency': 3}, ...]
    """
    font_scale = 1
    text_tiems = [
        TextBoxItem(t['text'], font_size=font_scale * t['frequency']) for t in texts
    ]
    return text_tiems


def get_fitted_texts_in_circle(texts: List[dict], radius):
    text_items = _get_text_item_from_text(texts)
    drawn_texts = _fit_text_items_in_circle(text_items, radius)