from typing import List, Mapping

import numpy as np
import pyglet
from pyglet.window import key

import car_stats
import utilities
from src.make_replay import Replay

Vector2 = np.ndarray


class Car:
    def __init__(
        self,
        x: float,
        y: float,
        heading: float,
        borders: List[utilities.Segment],
        gates: List[utilities.Segment],
        driven: bool,
        replay: Replay,
    ):
        self.x: float = x
        self.y: float = y
        self.start_x: float = x
        self.start_y: float = y
        self.car_heading: float = heading
        self.start_heading: float = heading
        self.replay: Replay = replay

        self.car_image = pyglet.image.load("../images/car.png")
        self.car_image.anchor_x = int(self.car_image.width / 2)
        self.car_image.anchor_y = int(self.car_image.height / 2)
        self.car_sprite = pyglet.sprite.Sprite(self.car_image, x=self.x, y=self.y)

        self.width: float = self.car_sprite.width
        self.height: float = self.car_sprite.height

        self.velocity: Vector2 = np.zeros(2, dtype=float)
        self.acceleration: Vector2 = np.zeros(2, dtype=float)
        self.steering_direction: float = 0.0
        self.going_reverse: float = 0.0
        self.alive: bool = True

        self.borders: List[utilities.Segment] = borders
        self.gates: List[utilities.Segment] = gates.copy()
        if self.gates:
            self.gates.append(self.gates[0])

        self.next_gate: int = 0
        self.completed: bool = False
        self.current_time: float = 0.0
        self.last_timer: float = 0.0

        self.driven: bool = driven
        self.i_frame: int = 0

        # Distances se segments
        pos: Vector2 = np.array([self.x, self.y], dtype=float)
        self.front_dist = utilities.Segment(pos.copy(), pos.copy())
        self.left_dist = utilities.Segment(pos.copy(), pos.copy())
        self.right_dist = utilities.Segment(pos.copy(), pos.copy())
        self.front_left_dist = utilities.Segment(pos.copy(), pos.copy())
        self.front_right_dist = utilities.Segment(pos.copy(), pos.copy())
        self.distances: np.ndarray = np.zeros(5, dtype=float)

    def physics_process(self, keys: Mapping[int, bool], dt: float) -> None:
        self.acceleration[:] = 0.0
        self.get_input(keys)
        self.apply_friction()
        self.velocity += self.acceleration * dt
        self.calculate_steering(dt)

    def get_input(self, keys: Mapping[int, bool]) -> None:
        """
        Change car status based on keys pressed
        :param keys: Dictionary of used keys
        :return: None
        """

        turn = 0
        if keys[key.A]:
            turn += 1
        if keys[key.D]:
            turn -= 1

        self.steering_direction = turn * car_stats.steering_angle
        self.acceleration[:] = 0.0

        if keys[key.W]:
            self.acceleration += utilities.vec_from_angle(self.car_heading) * car_stats.engine_power
        if keys[key.S]:
            self.acceleration += utilities.vec_from_angle(self.car_heading) * car_stats.braking

    def calculate_steering(self, dt: float) -> None:
        """
        Update the steering based on time passed
        :param dt: delta time
        :return: None

        """
        direction = utilities.vec_from_angle(self.car_heading)
        rear_wheel = np.array([self.x, self.y]) - car_stats.wheel_base / 2.0 * utilities.normalized(direction)
        front_wheel = np.array([self.x, self.y]) + car_stats.wheel_base / 2.0 * utilities.normalized(direction)
        rear_wheel += self.velocity * dt
        front_wheel += utilities.rotate(self.velocity, self.steering_direction) * dt

        self.x = float((rear_wheel[0] + front_wheel[0]) / 2)
        self.y = float((rear_wheel[1] + front_wheel[1]) / 2)

        new_heading = utilities.normalized(front_wheel - rear_wheel)
        current_traction = car_stats.traction_slow
        speed_norm = utilities.norm(self.velocity)

        if speed_norm > car_stats.slip_speed1:
            current_traction = car_stats.traction_mid
        if speed_norm > car_stats.slip_speed2:
            current_traction = car_stats.traction_fast

        self.going_reverse = float(np.dot(new_heading, utilities.normalized(self.velocity)))
        self.car_heading = float(utilities.angle(new_heading))

        if speed_norm > 0:
            if self.going_reverse > 0:
                vec = new_heading * speed_norm
                if not np.allclose(vec, self.velocity) and not np.isclose(vec[0], 0) and not np.isclose(vec[1], 0):
                    # Linear Interpolate
                    x_min = np.minimum(self.velocity[0], vec[0])
                    x_max = np.maximum(self.velocity[0], vec[0])
                    new_x = x_min + current_traction * (x_max - x_min)
                    new_y = self.velocity[1] + ((vec[1] - self.velocity[1]) / (vec[0] - self.velocity[0])) * (
                        new_x - self.velocity[0]
                    )
                    self.velocity = np.array([new_x, new_y], dtype=float)
                else:
                    self.velocity = vec
            elif self.going_reverse < 0:
                self.velocity = -new_heading * min(speed_norm, car_stats.max_speed_reverse)

        self.car_sprite.rotation = -self.car_heading

    def apply_friction(self) -> None:
        # stop velocity if too small
        speed_norm = utilities.norm(self.velocity)
        if speed_norm < 5:
            self.velocity[:] = 0.0
            return

        friction_force = -self.velocity * car_stats.friction
        drag_force = -self.velocity * speed_norm * car_stats.drag
        self.acceleration += friction_force + drag_force

    def show(self) -> None:
        if not self.alive:
            return
        self.car_sprite.update(x=float(self.x), y=float(self.y))
        self.car_sprite.draw()

    def update(self, keys: dict[int, bool], dt: float) -> list[float | None]:
        self.current_time += dt
        if self.driven:
            if not self.alive or self.completed:
                return [0.0, self.last_timer]

            self.physics_process(keys, dt)

            if self.cross_next_gate():
                self.next_gate += 1
                if self.next_gate == len(self.gates):
                    self.completed = True
                    return [0.0, round(self.current_time, 2)]

            if self.cross_border():
                self.alive = False
                return [0.0, round(self.current_time, 2)]

            self.last_timer = round(self.current_time, 2)
            speed = utilities.norm(self.velocity)
            if self.going_reverse < 0:
                speed *= -1
            self.calculate_distances()
            return [speed, round(self.current_time, 2)]
        else:
            if not self.alive or self.completed:
                return [None, round(self.replay.log[-1].dt, 2)]

            while self.i_frame < len(self.replay.log) - 1 and abs(
                self.current_time - self.replay.log[self.i_frame].dt
            ) >= abs(self.current_time - self.replay.log[self.i_frame + 1].dt):
                self.i_frame += 1

            frame = self.replay.log[self.i_frame]
            self.x, self.y = frame.x, frame.y
            self.car_heading = frame.heading
            self.alive = frame.alive
            self.completed = frame.completed
            self.car_sprite.rotation = -self.car_heading
            return [None, round(frame.dt, 2)]

    def car_vertices(self) -> list[Vector2]:
        """Return the 4 corner points of the car as Vector2 arrays."""
        front = utilities.vec_from_angle(self.car_heading) * (self.width / 2)
        back = utilities.vec_from_angle(self.car_heading) * (-self.width / 2)
        left = utilities.vec_from_angle(self.car_heading + 90) * (self.height / 2)
        right = utilities.vec_from_angle(self.car_heading - 90) * (self.height / 2)
        center = np.array([self.x, self.y], dtype=float)

        front_right = center + front + right
        front_left = center + front + left
        back_right = center + back + right
        back_left = center + back + left

        return [front_right, front_left, back_right, back_left]

    def get_edges(self) -> list[utilities.Segment]:
        """Return the 4 edges of the car as Segment objects."""
        v = self.car_vertices()
        right = utilities.Segment(v[0], v[2])
        left = utilities.Segment(v[1], v[3])
        front = utilities.Segment(v[0], v[1])
        back = utilities.Segment(v[2], v[3])
        return [right, left, front, back]

    def cross_border(self) -> bool:
        """Check if car intersects any border segment."""
        edges = self.get_edges()
        for edge in edges:
            for border in self.borders:
                intersects, _ = utilities.segment_intersection(edge, border)
                if intersects:
                    return True
        return False

    def cross_next_gate(self) -> bool:
        """Check if car intersects the next gate segment."""
        if self.next_gate >= len(self.gates):
            return False
        edges = self.get_edges()
        gate = self.gates[self.next_gate]
        for edge in edges:
            intersects, _ = utilities.segment_intersection(edge, gate)
            if intersects:
                return True
        return False

    def restart(self) -> None:
        """Restart car at initial position and heading without calling __init__."""
        self.x = self.start_x
        self.y = self.start_y
        self.car_heading = self.start_heading
        self.velocity[:] = 0.0
        self.acceleration[:] = 0.0
        self.steering_direction = 0.0
        self.going_reverse = 0.0
        self.alive = True
        self.next_gate = 0
        self.completed = False
        self.current_time = 0.0
        self.last_timer = 0.0
        self.i_frame = 0

        # Reset distances
        pos = np.array([self.x, self.y], dtype=float)
        for seg in [self.front_dist, self.left_dist, self.right_dist, self.front_left_dist, self.front_right_dist]:
            seg.p1 = pos.copy()
            seg.p2 = pos.copy()

        # Reset sprite position and rotation
        self.car_sprite.update(x=self.x, y=self.y)
        self.car_sprite.rotation = -self.car_heading

    def calculate_distances(self) -> None:
        """Calculate distances from car to borders in five directions."""
        directions = [0, 90, -90, 45, -45]
        segments_attr = ["front_dist", "left_dist", "right_dist", "front_left_dist", "front_right_dist"]

        for i, angle_offset in enumerate(directions):
            angle_deg = self.car_heading + angle_offset
            segment = utilities.Segment(
                np.array([self.x, self.y], dtype=float),
                np.array(
                    [self.x + 10000 * utilities.cos_deg(angle_deg), self.y + 10000 * utilities.sin_deg(angle_deg)],
                    dtype=float,
                ),
            )
            closest_point = np.array([10000.0, 10000.0], dtype=float)

            for border in self.borders:
                intersects, ipt = utilities.segment_intersection(border, segment)
                if intersects and ipt is not None:
                    if utilities.norm(ipt - np.array([self.x, self.y], dtype=float)) < utilities.norm(
                        closest_point - np.array([self.x, self.y], dtype=float)
                    ):
                        closest_point = ipt

            getattr(self, segments_attr[i]).p2 = closest_point
            self.distances[i] = utilities.norm(closest_point - np.array([self.x, self.y], dtype=float))
