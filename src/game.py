import pyglet
import copy
from pyglet import shapes
from pyglet.window import key
import car_class
import utilities
import make_replay


class Game:
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
        self.distances_batch = None

        self.finish_line_line = None
        self.gates_lines = None
        self.track_lines = None

        self.front_distance_line = None
        self.left_distance_line = None
        self.right_distance_line = None
        self.front_left_distance_line = None
        self.front_right_distance_line = None

        self.game_timer = 0.0
        self.finished = False

    def new_game(self):
        game_window = pyglet.window.Window(self.window_width, self.window_height, resizable=True)

        self.track_batch = pyglet.graphics.Batch()
        self.gates_batch = pyglet.graphics.Batch()
        self.finish_line_batch = pyglet.graphics.Batch()
        self.distances_batch = pyglet.graphics.Batch()

        self.track_lines = utilities.load_track_lines(self.track_path, self.track_batch)
        self.gates_lines = utilities.load_gates_lines(self.track_path, self.gates_batch)
        self.finish_line_line = utilities.load_finish_line_line(self.track_path, self.finish_line_batch)

        car = car_class.Car(
            self.start_x, self.start_y, self.heading, self.track_segments, self.gates_segments, True, None
        )
        keys = key.KeyStateHandler()
        game_window.push_handlers(keys)

        speed_label = pyglet.text.Label(
            "Speed : 0", font_name="Times New Roman", color=(255, 255, 255, 255), font_size=24, x=1700, y=1040
        )
        timer_label = pyglet.text.Label(
            "0.0s", font_name="Times New Roman", color=(255, 255, 255, 255), font_size=24, x=1600, y=1040
        )

        self.front_distance_line = shapes.Line(
            car.x, car.y, car.front_dist.x2, car.front_dist.y2, batch=self.distances_batch
        )
        self.left_distance_line = shapes.Line(
            car.x, car.y, car.left_dist.x2, car.left_dist.y2, batch=self.distances_batch
        )
        self.right_distance_line = shapes.Line(
            car.x, car.y, car.right_dist.x2, car.right_dist.y2, batch=self.distances_batch
        )
        self.front_left_distance_line = shapes.Line(
            car.x, car.y, car.front_left_dist.x2, car.front_left_dist.y2, batch=self.distances_batch
        )
        self.front_right_distance_line = shapes.Line(
            car.x, car.y, car.front_right_dist.x2, car.front_right_dist.y2, batch=self.distances_batch
        )

        replay = make_replay.replay()
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

        def update(dt):
            if self.finished:
                return

            upd = car.update(keys, dt)
            if upd[1] == -1:
                replay.reset()
                self.game_timer = 0
                self.finished = False
                return

            speed, timer = upd[0], upd[1]
            speed_label.text = f"Speed: {int(speed) if speed is not None else 0}"
            timer_label.text = f"{timer:.3f}s" if timer is not None else "0.0s"

            self.game_timer += dt

            self.front_distance_line = shapes.Line(
                car.x, car.y, car.front_dist.x2, car.front_dist.y2, batch=self.distances_batch
            )
            self.right_distance_line = shapes.Line(
                car.x, car.y, car.right_dist.x2, car.right_dist.y2, batch=self.distances_batch
            )
            self.left_distance_line = shapes.Line(
                car.x, car.y, car.left_dist.x2, car.left_dist.y2, batch=self.distances_batch
            )
            self.right_distance_line = shapes.Line(
                car.x, car.y, car.right_dist.x2, car.right_dist.y2, batch=self.distances_batch
            )
            self.front_left_distance_line = shapes.Line(
                car.x, car.y, car.front_left_dist.x2, car.front_left_dist.y2, batch=self.distances_batch
            )
            self.front_right_distance_line = shapes.Line(
                car.x, car.y, car.front_right_dist.x2, car.front_right_dist.y2, batch=self.distances_batch
            )

            replay.add(
                make_replay.replay.frame(
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
