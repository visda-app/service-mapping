from lib.wordcloud_vis import random


from lib.wordcloud_vis import (
    TextBoxItem,
    Rectangle,
    Circle,
    Pos,
    draw,
    _is_colliding,
    _is_point_in_rect,
    _does_line_bifurcate_rect,
    _fit_text_items_in_circle,
)

def test_is_point_in_rect():
    rect = Rectangle(Pos(1, 1), 2, 2)
    test_points = [
        {'p': Pos(1, 1), 'res': True},
        {'p': Pos(4, 1), 'res': False},
    ]
    for p in test_points:
        assert _is_point_in_rect(p['p'], rect) == p['res']


def test_does_line_bifuricate_rect():
    line = Rectangle(Pos(0, 0), 0, 2)
    rect = Rectangle(Pos(0, 0), 2, 1)
    assert _does_line_bifurcate_rect(line, rect)

    line = Rectangle(Pos(0, 0), 2, 0)
    rect = Rectangle(Pos(0, 0), 1, 1)
    assert _does_line_bifurcate_rect(line, rect)

    line = Rectangle(Pos(0, 0), 1, 0)
    rect = Rectangle(Pos(0, 0), 2, 1)
    assert not _does_line_bifurcate_rect(line, rect)


def test_is_colliding():
    rect = Rectangle(Pos(1, 1), 2, 2)
    rects = [
        {'rect': Rectangle(Pos(1, 1), 1, 1), 'res': True},
        {'rect': Rectangle(Pos(1, 1), 3, 3), 'res': True},
        {'rect': Rectangle(Pos(2, 1), 1, 1), 'res': True},
        {'rect': Rectangle(Pos(1, 1), 3, 0.5), 'res': True},
        {'rect': Rectangle(Pos(1, 1), 0.5, 3), 'res': True},
        {'rect': Rectangle(Pos(4, 1), 1, 1), 'res': False},
    ]
    for r in rects:
        assert _is_colliding(r['rect'], rect) == r['res'], f"{r} collision check with {rect}?"


def test__fit_text_items_in_circle():
    random.seed(1)
    sentence = (
        "Lorem ipsum dolor sit amet, "
        "consectetur adipiscing elit, "
        # "sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."
        # "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."
    )
    texts = [
        TextBoxItem(text=s.strip(), font_size=random.uniform(16, 100))
        for s in sentence.split()
    ]

    max_r = 2
    fitted_texts, drawn_rects = _fit_text_items_in_circle(texts, max_r)

    shapes = [Circle(Pos(0, 0), max_r, layer_number=0)]  +  fitted_texts # + drawn_rects

    draw(shapes, text_font_scale=0.15)

KEYWORDS = [
    {'word': 'cable', 'count': 9, 'relevance_score': 3.11},
    {'word': 'snapon', 'count': 3, 'relevance_score': 2.44},
    {'word': 'copper', 'count': 2, 'relevance_score': 1.39},
    {'word': 'cabled', 'count': 1, 'relevance_score': 0.5},
    {'word': 'coleman', 'count': 1, 'relevance_score': 0.31},
    {'word': 'amperage', 'count': 1, 'relevance_score': 0.25},
    {'word': 'these', 'count': 1, 'relevance_score': 0.21},
]

