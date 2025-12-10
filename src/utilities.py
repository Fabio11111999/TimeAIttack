import numpy as np
import math
from pyglet import shapes
from pyglet.window import key


def dist(x1: float, y1: float, x2: float, y2: float) -> float:
    """
    Calculate distance between 2 points in 2d space

    :param x1: x coordinate of first point
    :param y1: y coordinate of first point
    :param x2: x coordinate of second point
    :param y2: y coordinate of second point
    :return: The distance between the 2 points
    """
    return math.sqrt(((x2 - x1) ** 2) + ((y2 - y1) ** 2))


# Checks if x is included between a and b
def included(x, a, b):
    if min(a, b) <= x <= max(a, b):
        return True
    return False


# Cos of an angle in degrees
def cos(x):
    return math.cos(math.radians(x))


# Sin of an angle in degrees
def sin(x):
    return math.sin(math.radians(x))


# Norm of a vector
def norm(x):
    return np.linalg.norm(x)


# Normalize a vector
def normalized(v):
    if norm(v) == 0:
        return v
    return v / norm(v)


# Rotate a vector by an angle in degrees
def rotate(v, angle):
    rot = np.array([[cos(angle), -sin(angle)], [sin(angle), cos(angle)]])
    return np.dot(rot, v)


# Angle of a vector in degrees
def angle(v):
    angle = np.rad2deg(np.arctan(v[1] / v[0]))
    if v[0] < 0 and v[1] > 0:
        angle += 180
    if v[0] < 0 and v[1] < 0:
        angle += 180
    return angle


# Vector of norm 1 given its angle in degrees
def vec_from_angle(angle):
    return np.array([cos(angle), sin(angle)])


# Generic Segment
class segment:
    def __init__(self, x1, y1, x2, y2):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2

    def __str__(self):
        return "[(" + str(self.x1) + ", " + str(self.y1) + "), (" + str(self.x2) + ", " + str(self.y2) + ")]"


# Builds a line from a segment (or simply 2 points)
class line:
    def __init__(self, x1, y1, x2, y2):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.A = y2 - y1
        self.B = x1 - x2
        self.C = self.A * x1 + self.B * y1
        # line = Ax + By = C

    def __str__(self):
        return (
            "[("
            + str(self.x1)
            + ", "
            + str(self.y1)
            + "), ("
            + str(self.x2)
            + ", "
            + str(self.y2)
            + "), A = "
            + str(self.A)
            + ", B = "
            + str(self.B)
            + ", C = "
            + str(self.C)
            + "]"
        )


# Returns [are lines parallel? ,  intersection if they aren't]
def line_intersection(line1, line2):
    det = line1.A * line2.B - line1.B * line2.A
    if det == 0:
        # Lines are parallel
        return [True, [0, 0]]
    x = (line2.B * line1.C - line1.B * line2.C) / det
    y = (line1.A * line2.C - line2.A * line1.C) / det
    return [False, [x, y]]


# Given 2 segments returns whether they intersect
def segment_intersect(s1, s2):
    line1 = line(s1.x1, s1.y1, s1.x2, s1.y2)
    line2 = line(s2.x1, s2.y1, s2.x2, s2.y2)
    parallel = line_intersection(line1, line2)[0]
    if parallel:
        return False
    intersection = line_intersection(line1, line2)[1]
    if (
        (
            included(intersection[0], s1.x1, s1.x2)
            or math.isclose(intersection[0], s1.x1)
            or math.isclose(intersection[0], s1.x2)
        )
        and (
            included(intersection[0], s2.x1, s2.x2)
            or math.isclose(intersection[0], s2.x1)
            or math.isclose(intersection[0], s2.x2)
        )
        and (
            included(intersection[1], s1.y1, s1.y2)
            or math.isclose(intersection[1], s1.y1)
            or math.isclose(intersection[1], s1.y2)
        )
        and (
            included(intersection[1], s2.y1, s2.y2)
            or math.isclose(intersection[1], s2.y1)
            or math.isclose(intersection[1], s2.y2)
        )
    ):
        return True
    return False


# Given a segment and a line returns where they intersect
def segment_intersection(s1, s2):
    line1 = line(s1.x1, s1.y1, s1.x2, s1.y2)
    line2 = line(s2.x1, s2.y1, s2.x2, s2.y2)
    parallel = line_intersection(line1, line2)[0]
    if parallel:
        return False
    intersection = line_intersection(line1, line2)[1]
    if (
        (
            included(intersection[0], s1.x1, s1.x2)
            or math.isclose(intersection[0], s1.x1)
            or math.isclose(intersection[0], s1.x2)
        )
        and (
            included(intersection[0], s2.x1, s2.x2)
            or math.isclose(intersection[0], s2.x1)
            or math.isclose(intersection[0], s2.x2)
        )
        and (
            included(intersection[1], s1.y1, s1.y2)
            or math.isclose(intersection[1], s1.y1)
            or math.isclose(intersection[1], s1.y2)
        )
        and (
            included(intersection[1], s2.y1, s2.y2)
            or math.isclose(intersection[1], s2.y1)
            or math.isclose(intersection[1], s2.y2)
        )
    ):
        return intersection
    return False


# Given the path of the track load all borders as segments
def load_track_segments(path):
    in_outer = open(path + "outer.txt", "r")
    in_inner = open(path + "inner.txt", "r")
    inner, outer, inner_points, outer_points = [], [], [], []
    for row in in_outer:
        p = row.split()
        outer_points.append([int(float(p[0])), int(float(p[1]))])
    for row in in_inner:
        p = row.split()
        inner_points.append([int(float(p[0])), int(float(p[1]))])
    for i in range(len(outer_points)):
        outer.append(segment(outer_points[i - 1][0], outer_points[i - 1][1], outer_points[i][0], outer_points[i][1]))
    for i in range(len(inner_points)):
        inner.append(segment(inner_points[i - 1][0], inner_points[i - 1][1], inner_points[i][0], inner_points[i][1]))
    return outer + inner


# Given the path of the track build the lines of the borders and place them into a batch
def load_track_lines(path, batch):
    segments = load_track_segments(path)
    track_lines = []
    for s in segments:
        track_lines.append(shapes.Line(s.x1, s.y1, s.x2, s.y2, color=(255, 255, 255), batch=batch))
    return track_lines


# Given the path of a track read the starting position of the car
def read_position(path):
    infile = open(path + "starting_position.txt", "r")
    position = infile.readlines()[0]
    return [int(position.split()[0]), int(position.split()[1]), int(position.split()[2])]


# Given the path of a track load all the gates as segments
def load_gates_segments(path):
    infile = open(path + "gates.txt")
    gates = []
    for row in infile:
        p = row.split()
        gates.append(segment(int(float(p[0])), int(float(p[1])), int(float(p[2])), int(float(p[3]))))
    return gates


# Given the path of a track build  the lines of the gates and place them into a batch
def load_gates_lines(path, gates_batch):
    gates = load_gates_segments(path)
    gates_lines = []
    for i in range(0, len(gates)):
        g = gates[i]
        gates_lines.append(shapes.Line(g.x1, g.y1, g.x2, g.y2, color=(0, 255, 0), batch=gates_batch))
    return gates_lines


# Given the path of a track build the line of the finish line and place it into a batch
def load_finish_line_line(path, finish_line_batch):
    g = load_gates_segments(path)[0]
    finish_line_line = shapes.Line(g.x1, g.y1, g.x2, g.y2, color=(255, 255, 0), batch=finish_line_batch)
    return finish_line_line


def fill_keys(keys):
    b = [97, 100, 119, 115]
    for x in b:
        if x not in keys:
            keys[x] = False


KEYS_TO_TRACK = [key.W, key.A, key.S, key.D, key.UP, key.DOWN, key.LEFT, key.RIGHT, key.SPACE]


def get_dict_keys(keys):
    return {k: keys[k] for k in KEYS_TO_TRACK}
