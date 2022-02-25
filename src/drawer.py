import pyglet 
from pyglet import shapes
from pyglet.window import key

outer = True

output_path = '../tracks/drawer/'

def print_points(points, file_path):
    f = open(file_path, 'w')
    for p in points:
        f.write(str(p[0]) + ' ' + str(p[1]) + '\n')
    f.close()

def main():
    drawing_window = pyglet.window.Window(1920, 1030)
    points_outer = []
    lines_outer = []
    points_inner = []
    lines_inner = []
    main_batch = pyglet.graphics.Batch()
    instruction_label = pyglet.text.Label('Start drawing the outer section: "left-click" to place the next point, "right-click" to correct the last point,' + 
                                           'Press "Enter" to start drawing the inner border (the last line will be placed automatically) or to save and exit if you already did.',
                                           font_name = 'Times New Roman', color = (255, 255, 255, 255), font_size = 14, x = 10, y = 1000)

    @drawing_window.event
    def on_draw():
        drawing_window.clear()
        instruction_label.draw()
        main_batch.draw()

    @drawing_window.event
    def on_mouse_press(x, y, button, modifiers):
        if button == pyglet.window.mouse.LEFT:
            if outer == True:
                points_outer.append([x, y])
                if len(points_outer) > 1:
                    lines_outer.append(shapes.Line(points_outer[-2][0], points_outer[-2][1], points_outer[-1][0], points_outer[-1][1], width = 4, color = (255, 255, 255), batch = main_batch))
            else:
                points_inner.append([x, y])
                if len(points_inner) > 1:
                    lines_inner.append(shapes.Line(points_inner[-2][0], points_inner[-2][1], points_inner[-1][0], points_inner[-1][1], width = 4, color = (255, 255, 255), batch = main_batch))
        elif button == pyglet.window.mouse.RIGHT:
            if outer == True and len(points_outer) > 0:
                points_outer[-1] = [x, y]
                if len(points_outer) > 1:
                    lines_outer.pop()
                    lines_outer.append(shapes.Line(points_outer[-2][0], points_outer[-2][1], points_outer[-1][0], points_outer[-1][1], width = 4, color = (255, 255, 255), batch = main_batch))
            elif outer == False and len(points_inner) > 0:
                points_inner[-1] = [x, y]
                if len(points_inner) > 1:
                    lines_inner.pop()
                    lines_inner.append(shapes.Line(points_inner[-2][0], points_inner[-2][1], points_inner[-1][0], points_inner[-1][1], width = 4, color = (255, 255, 255), batch = main_batch))
    
    @drawing_window.event
    def on_key_press(symbol, modifier):
        if symbol == key.ENTER:
            global outer
            if outer == True:   # Go to inner
                outer = False
                if points_outer[0] != points_outer[-1]:
                    points_outer.append(points_outer[0])     # Close the figure
                    lines_outer.append(shapes.Line(points_outer[-2][0], points_outer[-2][1], points_outer[-1][0], points_outer[-1][1], width = 4, color = (255, 255, 255), batch = main_batch))
                    points_outer.pop()
                    print_points(points_outer, output_path + 'outer.txt')
            else:   # Done 
                if points_inner[0] != points_inner[-1]:
                    points_inner.append(points_inner[0])
                    lines_inner.append(shapes.Line(points_inner[-2][0], points_inner[-2][1], points_inner[-1][0], points_inner[-1][1], width = 4, color = (255, 255, 255), batch = main_batch))
                    points_inner.pop()
                    print_points(points_inner, output_path + 'inner.txt')
                    exit()

    pyglet.app.run()

if __name__ == '__main__':
    main()
