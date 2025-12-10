import pyglet
import car_class
import make_replay
import utilities
from pyglet import shapes

iframe, prev = 0, 0
next_line = None


def main():
    bug = make_replay.replay()
    bug.read_from_file("13.82.txt")
    track = "../tracks/track1/"
    window_width, window_heigth, track_path = 1920, 1080, "../tracks/track1/"
    start_x, start_y, heading = (
        utilities.read_position(track)[0],
        utilities.read_position(track)[1],
        utilities.read_position(track)[2],
    )
    track_batch, gates_batch, finish_line_batch = (
        pyglet.graphics.Batch(),
        pyglet.graphics.Batch(),
        pyglet.graphics.Batch(),
    )
    track_segments, track_lines = utilities.load_track_segments(track), utilities.load_track_lines(track, track_batch)
    gates_segments, gates_lines = utilities.load_gates_segments(track), utilities.load_gates_lines(track, gates_batch)
    game_window = pyglet.window.Window(window_width, window_heigth)
    car = car_class.Car(start_x, start_y, heading, track_segments, gates_segments, True, None)
    car_batch = pyglet.graphics.Batch()
    edges = car.get_edges()
    car_lines = []
    for s in edges:
        car_lines.append(shapes.Line(s.x1, s.y1, s.x2, s.y2, color=(0, 0, 255), width=2, batch=car_batch))

    gate = car.gates[car.next_gate]
    global next_line
    next_line = shapes.Line(gate.x1, gate.y1, gate.x2, gate.y2, color=(255, 0, 0), width=2, batch=car_batch)

    @game_window.event
    def on_draw():
        game_window.clear()
        track_batch.draw()
        finish_line_batch.draw()
        car.show()
        car_batch.draw()

    def update(dt):
        global iframe
        global prev
        if iframe >= len(bug.log):
            return
        frame = bug.log[iframe]
        iframe += 1
        utilities.fill_keys(frame.keys)
        car.update(frame.keys, frame.dt - prev)
        prev = frame.dt
        edges = car.get_edges()
        for i in range(4):
            s = edges[i]
            car_lines[i] = shapes.Line(s.x1, s.y1, s.x2, s.y2, color=(0, 0, 255), width=2, batch=car_batch)
        gate = car.gates[car.next_gate]
        global next_line
        next_line = shapes.Line(gate.x1, gate.y1, gate.x2, gate.y2, color=(255, 0, 0), width=2, batch=car_batch)

    pyglet.clock.schedule_interval(update, 1 / 120)
    pyglet.app.run()


if __name__ == "__main__":
    main()
