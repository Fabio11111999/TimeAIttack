import pyglet
from pyglet.window import key
import numpy as np
import utilities
import car_stats


class Car:
    def __init__(self, x, y, heading, borders, gates, driven, replay):
        self.x = x
        self.y = y
        self.start_x = x
        self.start_y = y
        self.car_image = pyglet.image.load("../images/car.png")
        self.car_image.anchor_x = int(self.car_image.width / 2)
        self.car_image.anchor_y = int(self.car_image.height / 2)
        self.car_sprite = pyglet.sprite.Sprite(self.car_image, x=self.x, y=self.y)

        self.width = self.car_sprite.width
        self.height = self.car_sprite.height
        self.car_heading = heading
        self.start_heading = heading
        self.velocity = np.array([0.0, 0.0])
        self.steering_direction = 0  # Either equals to -15, 0, 15
        self.acceleration = np.array([0.0, 0.0])
        self.going_reverse = 0
        self.alive = True
        self.borders = borders
        self.gates = gates
        if len(self.gates):
            self.gates.append(gates[0])
        self.next_gate = 0
        self.completed = False
        self.current_time = 0.0
        self.last_timer = 0

        # Replay
        self.driven = driven
        self.replay = replay
        self.i_frame = 0

        # Distances
        self.front_dist = utilities.segment(self.x, self.y, self.x, self.y)
        self.left_dist = utilities.segment(self.x, self.y, self.x, self.y)
        self.right_dist = utilities.segment(self.x, self.y, self.x, self.y)
        self.front_left_dist = utilities.segment(self.x, self.y, self.x, self.y)
        self.front_right_dist = utilities.segment(self.x, self.y, self.x, self.y)
        self.distances = [0, 0, 0, 0, 0]

    def physics_process(self, keys, dt):
        self.acceleration = np.array([0.0, 0.0])
        self.get_input(keys)
        self.apply_friction()
        self.velocity += self.acceleration * dt
        self.calculate_steering(dt)

    def get_input(self, keys):
        turn = 0
        if keys[key.A]:
            turn += 1
        if keys[key.D]:
            turn -= 1
        self.steering_direction = turn * car_stats.steering_angle
        if keys[key.W]:
            self.acceleration = utilities.vec_from_angle(self.car_heading) * car_stats.engine_power
        if keys[key.S]:
            self.acceleration = utilities.vec_from_angle(self.car_heading) * car_stats.braking

    def calculate_steering(self, dt):
        direction = utilities.vec_from_angle(self.car_heading)
        rear_wheel = np.array([self.x, self.y]) - car_stats.wheel_base / 2.0 * utilities.normalized(direction)
        front_wheel = np.array([self.x, self.y]) + car_stats.wheel_base / 2.0 * utilities.normalized(direction)
        rear_wheel += self.velocity * dt
        front_wheel += utilities.rotate(self.velocity, self.steering_direction) * dt
        self.x = (rear_wheel[0] + front_wheel[0]) / 2
        self.y = (rear_wheel[1] + front_wheel[1]) / 2
        new_heading = utilities.normalized(front_wheel - rear_wheel)
        current_traction = car_stats.traction_slow
        if utilities.norm(self.velocity) > car_stats.slip_speed1:
            current_traction = car_stats.traction_mid
        if utilities.norm(self.velocity) > car_stats.slip_speed2:
            current_traction = car_stats.traction_fast
        self.going_reverse = np.dot(new_heading, utilities.normalized(self.velocity))
        self.car_heading = utilities.angle(new_heading)
        if self.going_reverse > 0:
            vec = new_heading * utilities.norm(self.velocity)
            if vec[0] * vec[1] != 0 and self.velocity[0] * self.velocity[1] != 0 and vec[0] != self.velocity[0]:
                # Linear Interpolate
                x = min(self.velocity[0], vec[0])
                y = max(self.velocity[0], vec[0])
                new_x = x + current_traction * (y - x)
                new_y = self.velocity[1] + ((vec[1] - self.velocity[1]) / (vec[0] - self.velocity[0])) * (
                    new_x - self.velocity[0]
                )
                self.velocity = np.array([new_x, new_y])
            else:
                self.velocity = new_heading * utilities.norm(self.velocity)
        elif self.going_reverse < 0:
            self.velocity = -new_heading * min(utilities.norm(self.velocity), car_stats.max_speed_reverse)
        self.car_sprite.rotation = -self.car_heading

    def apply_friction(self):
        # avoiding an infinite lasting slow down
        if utilities.norm(self.velocity) < 5:
            self.velocity = np.array([0.0, 0.0])
        friction_force = self.velocity * car_stats.friction
        drag_force = self.velocity * utilities.norm(self.velocity) * car_stats.drag
        self.acceleration += friction_force + drag_force

    def show(self):
        if not self.alive:
            return
        self.car_sprite.update(x=self.x, y=self.y)
        self.car_sprite.draw()

    def update(self, keys, dt):
        self.current_time += dt
        if self.driven:
            if not self.alive or self.completed:
                return [0, self.last_timer]
            self.physics_process(keys, dt)
            if self.cross_next_gate():
                self.next_gate += 1
                if self.next_gate == len(self.gates):
                    self.completed = True
                    return [0, round(self.current_time, 2)]
            if self.cross_border():
                # self.restart()
                # return [0, -1]
                self.alive = False
                return [0, round(self.current_time, 2)]
            self.last_timer = round(self.current_time, 2)
            speed = utilities.norm(self.velocity)
            if self.going_reverse < 0:
                speed *= -1
            self.calculate_distances()
            return [speed, round(self.current_time, 2)]
        else:
            if self.alive is False or self.completed:
                return [None, round(self.replay.log[-1].dt, 2)]
            while self.i_frame < len(self.replay.log) - 1 and abs(
                self.current_time - self.replay.log[self.i_frame].dt
            ) >= abs(self.current_time - self.replay.log[self.i_frame + 1].dt):
                self.i_frame += 1
            self.x = self.replay.log[self.i_frame].x
            self.y = self.replay.log[self.i_frame].y
            self.car_heading = self.replay.log[self.i_frame].heading
            self.alive = self.replay.log[self.i_frame].alive
            self.completed = self.replay.log[self.i_frame].completed
            self.car_sprite.rotation = -self.car_heading
            return [None, round(self.replay.log[self.i_frame].dt, 2)]

    def car_vertices(self):
        front = utilities.vec_from_angle(self.car_heading) * self.width / 2
        back = utilities.vec_from_angle(self.car_heading) * -self.width / 2
        left = utilities.vec_from_angle(self.car_heading + 90) * self.height / 2
        right = utilities.vec_from_angle(self.car_heading - 90) * self.height / 2
        center = np.array([self.x, self.y])
        front_right = center + front + right
        front_left = center + front + left
        back_right = center + back + right
        back_left = center + back + left
        return [front_right, front_left, back_right, back_left]

    def get_edges(self):
        v = self.car_vertices()
        right = utilities.segment(v[0][0], v[0][1], v[2][0], v[2][1])
        left = utilities.segment(v[1][0], v[1][1], v[3][0], v[3][1])
        front = utilities.segment(v[0][0], v[0][1], v[1][0], v[1][1])
        back = utilities.segment(v[2][0], v[2][1], v[3][0], v[3][1])
        return [right, left, front, back]

    def cross_border(self):
        edges = self.get_edges()
        for edge in edges:
            for border in self.borders:
                if utilities.segment_intersect(edge, border):
                    return True
        return False

    def cross_next_gate(self):
        edges = self.get_edges()
        for edge in edges:
            if utilities.segment_intersect(edge, self.gates[self.next_gate]):
                return True
        return False

    def restart(self):
        self.__init__(
            self.start_x, self.start_y, self.start_heading, self.borders, self.gates, self.driven, self.replay
        )
        self.next_gate = 0

    # Calculates the points of intersection for each direction
    def calculate_distances(self):
        front_segment = utilities.segment(
            self.x,
            self.y,
            self.x + 10000 * utilities.cos(self.car_heading),
            self.y + 10000 * utilities.sin(self.car_heading),
        )
        front_point = [10000, 10000]
        for border in self.borders:
            front_intersection = utilities.segment_intersection(border, front_segment)
            if front_intersection is not False and utilities.dist(
                self.x, self.y, front_intersection[0], front_intersection[1]
            ) < utilities.dist(self.x, self.y, front_point[0], front_point[1]):
                front_point = front_intersection
        self.front_dist.x2 = front_point[0]
        self.front_dist.y2 = front_point[1]
        self.distances[0] = utilities.dist(self.x, self.y, front_point[0], front_point[1])

        left_segment = utilities.segment(
            self.x,
            self.y,
            self.x + 10000 * utilities.cos(self.car_heading + 90),
            self.y + 10000 * utilities.sin(self.car_heading + 90),
        )
        left_point = [10000, 10000]
        for border in self.borders:
            left_intersection = utilities.segment_intersection(border, left_segment)
            if left_intersection is not False and utilities.dist(
                self.x, self.y, left_intersection[0], left_intersection[1]
            ) < utilities.dist(self.x, self.y, left_point[0], left_point[1]):
                left_point = left_intersection
        self.left_dist.x2 = left_point[0]
        self.left_dist.y2 = left_point[1]
        self.distances[1] = utilities.dist(self.x, self.y, left_point[0], left_point[1])

        right_segment = utilities.segment(
            self.x,
            self.y,
            self.x + 10000 * utilities.cos(self.car_heading - 90),
            self.y + 10000 * utilities.sin(self.car_heading - 90),
        )
        right_point = [10000, 10000]
        for border in self.borders:
            right_intersection = utilities.segment_intersection(border, right_segment)
            if right_intersection is not False and utilities.dist(
                self.x, self.y, right_intersection[0], right_intersection[1]
            ) < utilities.dist(self.x, self.y, right_point[0], right_point[1]):
                right_point = right_intersection
        self.right_dist.x2 = right_point[0]
        self.right_dist.y2 = right_point[1]
        self.distances[2] = utilities.dist(self.x, self.y, right_point[0], right_point[1])

        front_left_segment = utilities.segment(
            self.x,
            self.y,
            self.x + 10000 * utilities.cos(self.car_heading + 45),
            self.y + 10000 * utilities.sin(self.car_heading + 45),
        )
        front_left_point = [10000, 10000]
        for border in self.borders:
            front_left_intersection = utilities.segment_intersection(border, front_left_segment)
            if front_left_intersection is not False and utilities.dist(
                self.x, self.y, front_left_intersection[0], front_left_intersection[1]
            ) < utilities.dist(self.x, self.y, front_left_point[0], front_left_point[1]):
                front_left_point = front_left_intersection
        self.front_left_dist.x2 = front_left_point[0]
        self.front_left_dist.y2 = front_left_point[1]
        self.distances[3] = utilities.dist(self.x, self.y, front_left_point[0], front_left_point[1])

        front_right_segment = utilities.segment(
            self.x,
            self.y,
            self.x + 10000 * utilities.cos(self.car_heading - 45),
            self.y + 10000 * utilities.sin(self.car_heading - 45),
        )
        front_right_point = [10000, 10000]
        for border in self.borders:
            front_right_intersection = utilities.segment_intersection(border, front_right_segment)
            if front_right_intersection is not False and utilities.dist(
                self.x, self.y, front_right_intersection[0], front_right_intersection[1]
            ) < utilities.dist(self.x, self.y, front_right_point[0], front_right_point[1]):
                front_right_point = front_right_intersection
        self.front_right_dist.x2 = front_right_point[0]
        self.front_right_dist.y2 = front_right_point[1]
        self.distances[4] = utilities.dist(self.x, self.y, front_right_point[0], front_right_point[1])
