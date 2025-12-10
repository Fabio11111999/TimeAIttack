import pyglet
import car_class
import utilities


class Viewer:
    def __init__(self, window_width, window_height, track):
        self.window_width = window_width
        self.window_height = window_height
        self.track_path = track

        pos = utilities.read_position(track)
        self.start_x, self.start_y, self.heading = pos[0], pos[1], pos[2]

        self.track_segments = utilities.load_track_segments(track)
        self.gates_segments = utilities.load_gates_segments(track)

        self.track_batch = None
        self.gates_batch = None
        self.finish_line_batch = None
        self.track_lines = None
        self.gates_lines = None
        self.finish_line_line = None

        self.timer_label = None

    def view(self, replay):
        replay_window = pyglet.window.Window(self.window_width, self.window_height)

        self.track_batch = pyglet.graphics.Batch()
        self.gates_batch = pyglet.graphics.Batch()
        self.finish_line_batch = pyglet.graphics.Batch()

        self.track_lines = utilities.load_track_lines(self.track_path, self.track_batch)
        self.gates_lines = utilities.load_gates_lines(self.track_path, self.gates_batch)
        self.finish_line_line = utilities.load_finish_line_line(self.track_path, self.finish_line_batch)

        self.timer_label = pyglet.text.Label(
            "0.0s", font_name="Times New Roman", color=(255, 255, 255, 255), font_size=24, x=1600, y=1040
        )

        car = car_class.Car(
            self.start_x, self.start_y, self.heading, self.track_segments, self.gates_segments, False, replay
        )

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
            self.timer_label.text = f"{upd[1]:.3f}s"

        pyglet.clock.schedule_interval(update, 1 / 120)
        pyglet.app.run()
