import pyglet
from pyglet.window import key
import car_class
from pyglet import shapes
import utilities
import make_replay
import pathlib
import time


class viewer():
    def __init__(self, window_width, window_heigth, track):
        self.window_width, self.window_heigth, self.track_path = window_width, window_heigth, track
        self.start_x, self.start_y, self.heading = utilities.read_position(track)[0], utilities.read_position(track)[1], utilities.read_position(track)[2]
        self.track_batch, self.gates_batch, self.finish_line_batch = pyglet.graphics.Batch(), pyglet.graphics.Batch(), pyglet.graphics.Batch()
        self.track_segments, self.track_lines = utilities.load_track_segments(track), utilities.load_track_lines(track, self.track_batch)
        self.gates_segments, self.gates_lines = utilities.load_gates_segments(track), utilities.load_gates_lines(track, self.gates_batch)
        self.finish_line_line = utilities.load_finish_line_line(track, self.finish_line_batch)
        self.timer_label = pyglet.text.Label('0.0s', font_name='Times New Roman', color=(255, 255, 255, 255), bold=True, font_size=24, x=1600, y=1040)

    def view(self, replay):
        replay_window = pyglet.window.Window(self.window_width, self.window_heigth)
        car = car_class.car(self.start_x, self.start_y, self.heading, self.track_segments, self.gates_segments, False, replay)

        @replay_window.event
        def on_draw():
            replay_window.clear()
            self.track_batch.draw()
            # self.gates_batch.draw()
            self.finish_line_batch.draw()
            car.show()
            self.timer_label.draw()

        def update(dt):
            upd = car.update(None, dt)
            self.timer_label.text = str(upd[1]) + 's'

        pyglet.clock.schedule_interval(update, 1 / 120)
        pyglet.app.run()
