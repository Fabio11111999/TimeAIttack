# src/utilities.py
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Mapping, Optional, Tuple

import numpy as np
import pyglet
import pyglet.graphics
from numpy.typing import NDArray
from pyglet import shapes
from pyglet.window import key

import graphics_constants

Vector2 = NDArray[np.float64]


def dist(p1: Vector2, p2: Vector2) -> float:
    """
    Euclidean distance between two 2D points.

    :param p1: First point.
    :param p2: Second point.
    :return: Euclidean distance.
    """
    return float(np.linalg.norm(p2 - p1))


def included(x: float, a: float, b: float) -> bool:
    """
    Return whether x lies between a and b (inclusive).

    :param x: Value to test.
    :param a: Interval endpoint A.
    :param b: Interval endpoint B.
    :return: True when min(a,b) <= x <= max(a,b).
    """
    return min(a, b) <= x <= max(a, b)


def cos_deg(angle_deg: float) -> float:
    """
    Cosine of angle given in degrees.

    :param angle_deg: Angle in degrees.
    :return: Cosine of the angle.
    """
    return math.cos(math.radians(angle_deg))


def sin_deg(angle_deg: float) -> float:
    """
    Sine of angle given in degrees.

    :param angle_deg: Angle in degrees.
    :return: Sine of the angle.
    """
    return math.sin(math.radians(angle_deg))


def norm(v: Vector2) -> float:
    """
    Euclidean norm of a vector.

    :param v: 1-D numpy array of shape (2 , ) representing a vector.
    :return: Norm (length).
    """
    return float(np.linalg.norm(v))


def normalized(v: Vector2) -> Vector2:
    """
    Return unit vector pointing in same direction as v.
    If v has length 0, returns v unchanged (still zeros).

    :param v: 1-D numpy array shape (2,).
    :return: Normalized vector (same dtype).
    """
    n = norm(v)
    if n == 0.0:
        return v
    return v / n


def rotate(v: Vector2, angle_deg: float) -> Vector2:
    """
    Rotate a 2D vector by angle (degrees), counterclockwise.

    :param v: Vector to rotate.
    :param angle_deg: Angle in degrees.
    :return: Rotated vector.
    """
    c = cos_deg(angle_deg)
    s = sin_deg(angle_deg)
    rot = np.array([[c, -s], [s, c]], dtype=float)
    return rot @ v


def angle(v: Vector2) -> float:
    """
    Angle (in degrees) of the vector measured from +X axis (0..360).

    Uses atan2 for robust quadrant handling.

    :param v: Vector (x,y).
    :return: Angle in degrees in range [0, 360).
    """
    a = math.degrees(math.atan2(v[1], v[0]))
    return a + 360 if a < 0 else a


def vec_from_angle(angle_deg: float) -> Vector2:
    """
    Unit vector for an angle given in degrees.

    :param angle_deg: Angle in degrees.
    :return: numpy array [cos(angle), sin(angle)]
    """
    return np.array([cos_deg(angle_deg), sin_deg(angle_deg)], dtype=float)


@dataclass
class Segment:
    """
    Simple axis-agnostic segment representation.
    Coordinates can be floats or ints (we cast where needed).
    """

    p1: Vector2
    p2: Vector2

    @property
    def x1(self) -> float:
        return float(self.p1[0])

    @property
    def y1(self) -> float:
        return float(self.p1[1])

    @property
    def x2(self) -> float:
        return float(self.p2[0])

    @property
    def y2(self) -> float:
        return float(self.p2[1])


@dataclass
class Line:
    """
    Immutable line (infinite) representation in Ax + By = C form,
    constructed from two points (x1,y1)-(x2,y2).
    """

    x1: float
    y1: float
    x2: float
    y2: float
    A: float = 0.0
    B: float = 0.0
    C: float = 0.0

    def __post_init__(self) -> None:
        self.A = self.y2 - self.y1
        self.B = self.x1 - self.x2
        self.C = self.A * self.x1 + self.B * self.y1


def line_intersection(l1: Line, l2: Line) -> Tuple[bool, Optional[Vector2]]:
    """
    Compute intersection of two infinite lines.

    :param l1: First Line.
    :param l2: Second Line.
    :return: (are_parallel, intersection_point_or_None). If parallel -> (True, None).
    """
    det = l1.A * l2.B - l1.B * l2.A
    if math.isclose(det, 0.0):
        return True, None
    x = (l2.B * l1.C - l1.B * l2.C) / det
    y = (l1.A * l2.C - l2.A * l1.C) / det
    return False, np.array([x, y], dtype=float)


def _point_in_segment_bbox(p: Vector2, s: Segment, eps: float = 1e-9) -> bool:
    """
    Helper to determine if point (px,py) lies within the bounding box of segment s,
    including endpoints. Uses a small epsilon for float robustness.

    :param p: point to analyze
    :param s: segment to analyze
    :return: True if the point lies on the segment
    """
    in_x = (np.minimum(s.p1[0], s.p2[0]) - eps) <= p[0] <= (np.maximum(s.p1[0], s.p2[0]) + eps)
    in_y = (np.minimum(s.p1[1], s.p2[1]) - eps) <= p[1] <= (np.maximum(s.p1[1], s.p2[1]) + eps)
    return bool(in_x and in_y)


def segment_intersection(s1: Segment, s2: Segment) -> Tuple[bool, Optional[Vector2]]:
    """
    Compute intersection between two segments (finite).

    :param s1: First segment.
    :param s2: Second segment.
    :return: (intersected, point) where intersected is True and point is (x,y) if intersect,
             otherwise (False, None).
    """
    l1 = Line(float(s1.x1), float(s1.y1), float(s1.x2), float(s1.y2))
    l2 = Line(float(s2.x1), float(s2.y1), float(s2.x2), float(s2.y2))
    parallel, ipt = line_intersection(l1, l2)
    if parallel or ipt is None:
        return False, None
    if _point_in_segment_bbox(ipt, s1) and _point_in_segment_bbox(ipt, s2):
        return True, ipt
    return False, None


def load_track_segments(path: str) -> List[Segment]:
    """
    Read outer.txt and inner.txt from the given path and return a list of Segment objects
    describing the borders (outer then inner).

    :param path: Directory path ending with slash where outer.txt and inner.txt are located.
    :return: List[Segment]
    """
    outer_points: List[Tuple[int, int]] = []
    inner_points: List[Tuple[int, int]] = []

    with open(path + "outer.txt", "r") as fh:
        for row in fh:
            p = row.split()
            if not p:
                continue
            outer_points.append((int(float(p[0])), int(float(p[1]))))

    with open(path + "inner.txt", "r") as fh:
        for row in fh:
            p = row.split()
            if not p:
                continue
            inner_points.append((int(float(p[0])), int(float(p[1]))))

    outer_segments: List[Segment] = []
    inner_segments: List[Segment] = []

    # build closed ring segments (last->first included)
    for i in range(len(outer_points)):
        prev = np.array(outer_points[i - 1], dtype=float)
        cur = np.array(outer_points[i], dtype=float)
        outer_segments.append(Segment(prev, cur))

    for i in range(len(inner_points)):
        prev = np.array(inner_points[i - 1], dtype=float)
        cur = np.array(inner_points[i], dtype=float)
        inner_segments.append(Segment(prev, cur))

    return outer_segments + inner_segments


def load_track_lines(path: str, batch: pyglet.graphics.Batch) -> List[shapes.Line]:
    """
    Create pyglet Line shapes for all track segments and return them.

    :param path: Path to the track folder.
    :param batch: pyglet.graphics.Batch to put shapes into.
    :return: List of pyglet shapes.Line objects.
    """
    segments = load_track_segments(path)
    lines = []
    for s in segments:
        lines.append(
            shapes.Line(
                float(s.x1), float(s.y1), float(s.x2), float(s.y2), color=graphics_constants.white_color, batch=batch
            )
        )
    return lines


def read_position(path: str) -> Tuple[int, int, int]:
    """
    Read starting position file (starting_position.txt) with "x y heading".

    :param path: Path to track folder.
    :return: (x, y, heading) as integers.
    """
    with open(path + "starting_position.txt", "r") as fh:
        first = fh.readline().strip()
    parts = first.split()
    return int(parts[0]), int(parts[1]), int(parts[2])


def load_gates_segments(path: str) -> List[Segment]:
    """
    Read gates.txt, where each line is "x1 y1 x2 y2", return Segment objects.

    :param path: Path to track folder.
    :return: List of Segment objects for gates.
    """
    gates: List[Segment] = []
    with open(path + "gates.txt", "r") as fh:
        for row in fh:
            p = row.split()
            if not p:
                continue
            p1 = np.array([float(p[0]), float(p[1])], dtype=float)
            p2 = np.array([float(p[2]), float(p[3])], dtype=float)
            gates.append(Segment(p1, p2))
    return gates


def load_gates_lines(path: str, gates_batch: pyglet.graphics.Batch) -> List[shapes.Line]:
    """
    Create pyglet Line shapes for all gates and return them.

    :param path: Track folder path.
    :param gates_batch: pyglet Batch for gates.
    :return: List of pyglet shapes.Line for gates.
    """
    gates = load_gates_segments(path)
    lines = []
    for g in gates:
        lines.append(
            shapes.Line(
                float(g.x1),
                float(g.y1),
                float(g.x2),
                float(g.y2),
                color=graphics_constants.green_color,
                batch=gates_batch,
            )
        )
    return lines


def load_finish_line_line(path: str, finish_line_batch: pyglet.graphics.Batch) -> pyglet.shapes.Line:
    """
    Return the first gate as the finish-line shape (yellow).

    :param path: track folder path.
    :param finish_line_batch: pyglet Batch to attach the shape to.
    :return: pyglet shapes.Line representing finish line.
    """
    gates = load_gates_segments(path)
    if not gates:
        raise FileNotFoundError("gates.txt is empty or missing")
    g = gates[0]
    return shapes.Line(
        float(g.x1),
        float(g.y1),
        float(g.x2),
        float(g.y2),
        color=graphics_constants.yellow_color,
        batch=finish_line_batch,
    )


def fill_keys(keys: Dict[int, bool]) -> None:
    """
    Ensure the provided dict has entries for WASD (97,100,119,115) set to False when missing.

    :param keys: Mutable dict mapping key codes to bool.
    """
    required = [97, 100, 119, 115]  # ASCII codes for a, d, w, s
    for code in required:
        keys.setdefault(code, False)


KEYS_TO_TRACK: List[int] = [
    key.W,
    key.A,
    key.S,
    key.D,
    key.UP,
    key.DOWN,
    key.LEFT,
    key.RIGHT,
    key.SPACE,
]


def get_dict_keys(keys: Mapping[int, bool]) -> Dict[int, bool]:
    """
    Extract only the keys we track (WASD + arrows + space) from any mapping-like
    object supporting __getitem__, such as KeyStateHandler.
    """
    return {k: bool(keys[k]) for k in KEYS_TO_TRACK}
