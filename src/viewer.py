from typing import List, Optional

import pyglet

import car_class
import graphics_constants
import utilities
from make_replay import Replay


class Viewer:
    def __init__(self, window_width: int, window_height: int, replay: Replay):
        """
        Creating a new replay viewer

        :param window_width: width of the viewer window
        :param window_height: height of the viewer window
        :param replay: replay to visualize
        """
        self.window_width: int = window_width
        self.window_height: int = window_height
        self.replay: Replay = replay
        if replay.track_path is None:
            raise Exception("Replay does not have a track path")
        self.track_path: str = replay.track_path

        pos = utilities.read_position(self.track_path)
        self.start_x: float
        self.start_y: float
        self.heading: float
        self.start_x, self.start_y, self.heading = pos[0], pos[1], pos[2]

        self.track_segments = utilities.load_track_segments(self.track_path)
        self.gates_segments = utilities.load_gates_segments(self.track_path)

        self.track_batch: Optional[pyglet.graphics.Batch] = None
        self.gates_batch: Optional[pyglet.graphics.Batch] = None
        self.finish_line_batch: Optional[pyglet.graphics.Batch] = None
        self.track_lines: List[pyglet.shapes.Line] | None = None
        self.gates_lines: List[pyglet.shapes.Line] | None = None
        self.finish_line_line: pyglet.shapes.Line | None = None

        self.timer_label: Optional[pyglet.text.Label] = None

    def view(self) -> None:
        """
        Show the replay in a pyglet window.

        :return: None
        """
        replay_window = pyglet.window.Window(self.window_width, self.window_height)  # type: ignore

        self.track_batch = pyglet.graphics.Batch()
        self.gates_batch = pyglet.graphics.Batch()
        self.finish_line_batch = pyglet.graphics.Batch()

        self.track_lines = utilities.load_track_lines(self.track_path, self.track_batch)
        self.gates_lines = utilities.load_gates_lines(self.track_path, self.gates_batch)
        self.finish_line_line = utilities.load_finish_line_line(self.track_path, self.finish_line_batch)

        self.timer_label = pyglet.text.Label(
            "Time: 0.0s",
            font_name=graphics_constants.replay_viewer_font_name,
            color=graphics_constants.white_color,
            font_size=graphics_constants.replay_viewer_font_size,
            x=graphics_constants.replay_viewer_label_x,
            y=graphics_constants.replay_viewer_label_y,
        )

        car = car_class.Car(
            self.start_x,
            self.start_y,
            self.heading,
            self.track_segments,
            self.gates_segments,
            driven=False,
            replay=self.replay,
        )

        @replay_window.event
        def on_draw() -> None:
            """
            Renders the viewer
            :return: None
            """
            replay_window.clear()
            if self.track_batch:
                self.track_batch.draw()
            if self.gates_batch:
                self.gates_batch.draw()
            if self.finish_line_batch:
                self.finish_line_batch.draw()
            car.show()
            if self.timer_label:
                self.timer_label.draw()

        def update(dt: float) -> None:
            """
            Updates the car position and the labels
            :param dt: delta time
            :return: None
            """
            upd = car.update(None, dt)
            if self.timer_label and upd[1] is not None:
                self.timer_label.text = f"Time: {upd[1]:.3f}s"

        pyglet.clock.schedule_interval(update, 1 / 120)
        pyglet.app.run()
