import pyglet 
from pyglet import shapes
from pyglet.window import key
import utilities

path = '../tracks/drawer/'
start_point = [-1, -1]


def print_gates(gates, file_path):
    f = open(file_path, 'w')
    for g in gates:
        f.write(str(g[0]) + ' ' + str(g[1]) + ' ' + str(g[2]) + ' ' + str(g[3]) + '\n')
    f.close()

def main():
    drawing_window = pyglet.window.Window(1920, 1080)
    track_batch = pyglet.graphics.Batch()
    borders = utilities.load_track(path)[2]
    lines = []
    border_segments = []
    for border in borders:
        lines.append(shapes.Line(border[0], border[1], border[2], border[3], color = (255, 255, 255), width = 4, batch = track_batch))
    instruction_label = pyglet.text.Label('"left-click" to place the next point (for each gate place 2 points), "right-click" to correct the last point. Press "Enter" to save and exit.',
                                           font_name = 'Times New Roman', color = (255, 255, 255, 255), font_size = 14, x = 10, y = 1060)
    gates = []
    new_lines = []

    @drawing_window.event
    def on_draw():
        drawing_window.clear()
        instruction_label.draw()
        track_batch.draw()

    @drawing_window.event
    def on_mouse_press(x, y, button, modifiers):
        global start_point
        if button == pyglet.window.mouse.LEFT:
            if start_point == [-1, -1]:
                start_point = [x, y]
            else:
                gates.append(start_point + [x, y])
                start_point = [-1, -1]
                new_lines.append(shapes.Line(gates[-1][0], gates[-1][1], gates[-1][2], gates[-1][3], width = 4, color = (255, 255, 255), batch = track_batch))
        elif button == pyglet.window.mouse.RIGHT:
            if start_point == [-1, -1]:
                if len(gates) == 0:
                    return
                gates[-1][2], gates[-1][3] = x, y
                new_lines.pop()
                new_lines.append(shapes.Line(gates[-1][0], gates[-1][1], gates[-1][2], gates[-1][3], width = 4, color = (255, 255, 255), batch = track_batch))
            else:
                start_point = [x, y]
    
    @drawing_window.event
    def on_key_press(symbol, modifier):
        if symbol == key.ENTER:
            print_gates(gates, path + 'gates.txt')
            exit()
    
    pyglet.app.run()

if __name__ == '__main__':
    main()
