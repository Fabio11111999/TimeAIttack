from typing import List, Optional, Tuple

import pyglet
from pyglet import shapes
from pyglet.window import key

import car_class
import graphics_constants
import make_replay
import utilities


class Game:
    def __init__(self, window_width: int, window_height: int, track: str):
        """
        Initialize a new Game session.

        :param window_width: Width of the game window
        :param window_height: Height of the game window
        :param track: Path to the track folder
        """
        self.window_width: int = window_width
        self.window_height: int = window_height
        self.track_path: str = track

        pos: Tuple[float, float, float] = utilities.read_position(track)
        self.start_x, self.start_y, self.heading = pos

        self.track_segments = utilities.load_track_segments(track)
        self.gates_segments = utilities.load_gates_segments(track)

        # Batches
        self.track_batch: Optional[pyglet.graphics.Batch] = None
        self.gates_batch: Optional[pyglet.graphics.Batch] = None
        self.finish_line_batch: Optional[pyglet.graphics.Batch] = None
        self.distances_batch: Optional[pyglet.graphics.Batch] = None

        # Border and gates lines

        self.track_lines: Optional[List[shapes.Line]] = None
        self.gates_lines: Optional[List[shapes.Line]] = None
        self.finish_line_line: Optional[shapes.Line] = None

        # Distance lines
        self.front_distance_line: Optional[shapes.Line] = None
        self.left_distance_line: Optional[shapes.Line] = None
        self.right_distance_line: Optional[shapes.Line] = None
        self.front_left_distance_line: Optional[shapes.Line] = None
        self.front_right_distance_line: Optional[shapes.Line] = None

        self.game_timer: float = 0.0
        self.started = False
        self.finished: bool = False

    def new_game(self) -> make_replay.Replay:
        """
        Start a new game session and return the replay object.

        :return: Replay containing all frames of this session
        """
        game_window = pyglet.window.Window(self.window_width, self.window_height, resizable=True)  # type: ignore

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
        replay = make_replay.Replay(self.track_path)
        car = car_class.Car(
            self.start_x,
            self.start_y,
            self.heading,
            self.track_segments,
            self.gates_segments,
            driven=True,
            replay=replay,
        )

        # Key handler
        keys = key.KeyStateHandler()
        game_window.push_handlers(keys)

        # Labels
        speed_label = pyglet.text.Label(
            "Speed: 0",
            color=graphics_constants.white_color,
            font_name=graphics_constants.game_speed_label_font_name,
            font_size=graphics_constants.game_speed_label_font_size,
            x=graphics_constants.game_speed_label_x,
            y=graphics_constants.game_speed_label_y,
        )

        timer_label = pyglet.text.Label(
            "Time: 0.0s",
            color=graphics_constants.white_color,
            font_name=graphics_constants.game_timer_label_font_name,
            font_size=graphics_constants.game_timer_label_font_size,
            x=graphics_constants.game_timer_label_x,
            y=graphics_constants.game_timer_label_y,
        )

        # Distance lines
        self.update_distance_lines(car)

        self.game_timer = 0.0
        self.finished = False
        self.started = False

        @game_window.event
        def on_draw() -> None:
            """
            Render all graphics on screen.

            :return: None
            """
            game_window.clear()
            if self.track_batch:
                self.track_batch.draw()
            if self.gates_batch:
                self.gates_batch.draw()
            if self.finish_line_batch:
                self.finish_line_batch.draw()
            if self.distances_batch:
                self.distances_batch.draw()
            car.show()
            speed_label.draw()
            timer_label.draw()

        def update(dt: float) -> None:
            """
            Update game logic for each frame.

            :return: None
            """
            if self.finished:
                return

            pressed_keys = utilities.get_dict_keys(keys)  # type: ignore[arg-type]

            if self.started is False and not any(pressed_keys.values()):
                return

            self.started = True

            speed, timer = car.update(keys, dt)  # type: ignore[arg-type]
            self.game_timer += dt

            speed_label.text = f"Speed: {int(speed) if speed is not None else 0}"
            timer_label.text = f"Time: {timer:.3f}s" if timer is not None else "0.0s"

            self.update_distance_lines(car)

            # Add frame to replay
            replay.add(
                make_replay.Replay.Frame(
                    frame_number=len(replay.log),
                    delta_time=self.game_timer,
                    x=car.x,
                    y=car.y,
                    heading=car.car_heading,
                    alive=car.alive,
                    completed=car.completed,
                    pressed_keys=pressed_keys,
                )
            )

            if not car.alive or car.completed:
                self.finished = True

        pyglet.clock.schedule_interval(update, 1 / 60)
        pyglet.app.run()
        return replay

    def update_distance_lines(self, car: car_class.Car) -> None:
        """
        Update or create distance lines for visualization.

        :param car: Car object to compute distances from
        """
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
