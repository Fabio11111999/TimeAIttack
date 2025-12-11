import pyglet
from pyglet import shapes
from pyglet.window import key
from typing import Optional

import car_class
import utilities
import make_replay
import graphics_constants


class Game:
    def __init__(self, window_width: int, window_height: int, track: str):
        self.window_width = window_width
        self.window_height = window_height
        self.track_path = track

        pos = utilities.read_position(track)
        self.start_x, self.start_y, self.heading = pos[0], pos[1], pos[2]

        self.track_segments = utilities.load_track_segments(track)
        self.gates_segments = utilities.load_gates_segments(track)

        # Batches
        self.track_batch: Optional[pyglet.graphics.Batch] = None
        self.gates_batch: Optional[pyglet.graphics.Batch] = None
        self.finish_line_batch: Optional[pyglet.graphics.Batch] = None
        self.distances_batch: Optional[pyglet.graphics.Batch] = None

        # Distance lines
        self.front_distance_line: Optional[shapes.Line] = None
        self.left_distance_line: Optional[shapes.Line] = None
        self.right_distance_line: Optional[shapes.Line] = None
        self.front_left_distance_line: Optional[shapes.Line] = None
        self.front_right_distance_line: Optional[shapes.Line] = None

        self.game_timer: float = 0.0
        self.finished: bool = False

    def new_game(self) -> make_replay.Replay:
        game_window = pyglet.window.Window(self.window_width, self.window_height, resizable=True)

        # Create batches
        self.track_batch = pyglet.graphics.Batch()
        self.gates_batch = pyglet.graphics.Batch()
        self.finish_line_batch = pyglet.graphics.Batch()
        self.distances_batch = pyglet.graphics.Batch()

        # Load track graphics
        self.track_lines = utilities.load_track_lines(self.track_path, self.track_batch)
        self.gates_lines = utilities.load_gates_lines(self.track_path, self.gates_batch)
        self.finish_line_line = utilities.load_finish_line_line(self.track_path, self.finish_line_batch)

        # Create replay and car
        replay = make_replay.Replay()
        car = car_class.Car(
            self.start_x, self.start_y, self.heading, self.track_segments, self.gates_segments, True, replay
        )

        # Key handler
        keys = key.KeyStateHandler()
        game_window.push_handlers(keys)

        # Labels
        speed_label = pyglet.text.Label("Speed: 0", color=graphics_constants.white_color, font_size=24, x=1700, y=1040)
        timer_label = pyglet.text.Label(
            "Time: 0.0s", color=graphics_constants.white_color, font_size=24, x=1400, y=1040
        )

        # Distance lines
        self.update_distance_lines(car)

        self.game_timer = 0.0
        self.finished = False

        @game_window.event
        def on_draw():
            game_window.clear()
            self.track_batch.draw()
            self.gates_batch.draw()
            self.finish_line_batch.draw()
            self.distances_batch.draw()
            car.show()
            speed_label.draw()
            timer_label.draw()

        def update(dt: float):
            if self.finished:
                return

            speed, timer = car.update(keys, dt)
            self.game_timer += dt

            speed_label.text = f"Speed: {int(speed) if speed is not None else 0}"
            timer_label.text = f"Time: {timer:.3f}s" if timer is not None else "0.0s"

            # Update sensor lines
            self.update_distance_lines(car)

            # Add frame to replay
            replay.add(
                make_replay.Replay.Frame(
                    len(replay.log),
                    self.game_timer,
                    car.x,
                    car.y,
                    car.car_heading,
                    car.alive,
                    car.completed,
                    utilities.get_dict_keys(keys),
                )
            )

            if not car.alive or car.completed:
                self.finished = True

        pyglet.clock.schedule_interval(update, 1 / 120)
        pyglet.app.run()
        return replay

    def update_distance_lines(self, car: car_class.Car) -> None:
        """Update or create distance lines for visualization."""
        batch = self.distances_batch

        self.front_distance_line = shapes.Line(car.x, car.y, car.front_dist.x2, car.front_dist.y2, batch=batch)
        self.left_distance_line = shapes.Line(car.x, car.y, car.left_dist.x2, car.left_dist.y2, batch=batch)
        self.right_distance_line = shapes.Line(car.x, car.y, car.right_dist.x2, car.right_dist.y2, batch=batch)
        self.front_left_distance_line = shapes.Line(
            car.x, car.y, car.front_left_dist.x2, car.front_left_dist.y2, batch=batch
        )
        self.front_right_distance_line = shapes.Line(
            car.x, car.y, car.front_right_dist.x2, car.front_right_dist.y2, batch=batch
        )
