from enum import Enum
from typing import List, Literal

import numpy as np
import pyglet
from pyglet import shapes
from pyglet.window import key, mouse

import graphics_constants
from car_class import Car

OUTPUT_PATH = "../tracks/drawer/"


class DrawingState(Enum):
    DRAW_OUTER = 1
    DRAW_INNER = 2
    FINISHED_DRAWING = 3
    CAR_PLACEMENT = 4
    GATES_PLACEMENT = 5


ModeType = Literal["inner", "outer", "gates"]

step_to_mode: dict[DrawingState, ModeType] = {
    DrawingState.DRAW_OUTER: "outer",
    DrawingState.DRAW_INNER: "inner",
    DrawingState.GATES_PLACEMENT: "gates",
}


def save_points(points: list[list[float]], filename: str) -> None:
    """
    Save a sequence of (x, y) points to a text file, one point per line.

    :param points: List of (x, y) float list representing the track points.
    :param filename: Path of the output file to write.
    :return: None
    """
    with open(filename, "w") as f:
        for x, y in points:
            f.write(f"{x} {y}\n")


def catmull_rom_spline(
    points: list[list[float]],
    resolution: int = 10,
    width: int | None = None,
    height: int | None = None,
) -> list[list[float]]:
    """
    Generate a Catmull-Rom spline that interpolates between the given points,
    optionally clamping points to the [0,width] x [0,height] rectangle.

    :param points: List of (x, y) float list representing control points.
    :param resolution: Number of interpolated points generated between each pair of input points.
    :param width: Optional max X value.
    :param height: Optional max Y value.
    :return: List of [x, y] points representing the smoothed spline.
    """
    if len(points) < 2 or resolution == 0:
        return points.copy()

    points = list(np.array(points))
    smooth_points = np.vstack([points[0], points, points[-1]])
    result = []

    for i in range(1, len(smooth_points) - 2):
        p0, p1, p2, p3 = (
            smooth_points[i - 1],
            smooth_points[i],
            smooth_points[i + 1],
            smooth_points[i + 2],
        )
        for t in np.linspace(0, 1, resolution + 1, endpoint=False):
            t2 = t * t
            t3 = t2 * t
            f = 0.5 * (
                (2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3
            )
            if width is not None:
                f[0] = max(0, min(width, int(f[0])))
            if height is not None:
                f[1] = max(0, min(height, int(f[1])))
            result.append(f.tolist())

    last_point = points[-1]
    if width is not None:
        last_point[0] = max(0, min(width, last_point[0]))
    if height is not None:
        last_point[1] = max(0, min(height, last_point[1]))
    result.append(last_point)

    return result


def draw_lines(
    batch: pyglet.graphics.Batch,
    lines_container: list,
    mode: ModeType,
    points: list[list[float]],
    color: tuple[int, int, int, int],
) -> None:
    """
    Draw connected line segments between consecutive (x, y) points.

    All previously drawn lines in `lines_container` are deleted and replaced
    with the new line objects.

    :param batch: The pyglet batch used to group drawing operations.
    :param lines_container: A list that stores the created Line objects, so they can be deleted later.
    :param mode: Type of line
    :param points: List of (x, y) float list through which the polyline is drawn.
    :param color: RGB or RGBA color tuple used to draw the lines.
    :return: None
    """
    for line in lines_container:
        line.delete()
    lines_container.clear()

    if mode == "gates":
        for i in range(0, len(points) - 1, 2):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            lines_container.append(shapes.Line(x1, y1, x2, y2, color=color, batch=batch))
    else:
        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            lines_container.append(shapes.Line(x1, y1, x2, y2, color=color, batch=batch))


def main() -> None:
    window = pyglet.window.Window(graphics_constants.resolution_width, graphics_constants.resolution_height)  # type: ignore

    drawing_step = DrawingState.DRAW_OUTER

    original_segments_batch = pyglet.graphics.Batch()
    smooth_segments_batch = pyglet.graphics.Batch()
    grid_batch = pyglet.graphics.Batch()
    gates_batch = pyglet.graphics.Batch()

    preview_line: shapes.Line | None = None
    preview_gate_line: shapes.Line | None = None

    smoothing_resolution = 10

    show_grid = False
    grid_rows = 8
    grid_columns = 10

    car_instance: Car | None = None
    car_rotation_step = 5

    points: dict[str, list[list[float]]] = {"outer": [], "inner": [], "gates": []}
    original_lines: dict[str, list[shapes.Line]] = {"outer": [], "inner": []}
    smooth_lines: dict[str, list[shapes.Line]] = {"outer": [], "inner": []}
    gates_lines: list[shapes.Line] = []

    string_spacing = " " * 7
    instruction_label_outer = pyglet.text.Label(
        "Draw outer border\nLeft click = add point"
        + string_spacing
        + "Right click = adjust last point"
        + string_spacing
        + "ENTER = close border"
        + string_spacing
        + "UP/DOWN = change smoothing resolution",
        font_name=graphics_constants.drawer_instruction_label_font_name,
        font_size=graphics_constants.drawer_instruction_label_font_size,
        x=graphics_constants.drawer_instruction_label_x,
        y=graphics_constants.drawer_instruction_label_y,
        color=graphics_constants.white_color,
        multiline=True,
        width=graphics_constants.resolution_width,
    )

    instruction_label_inner = pyglet.text.Label(
        "Draw inner border\nLeft click = add point"
        + string_spacing
        + "Right click = adjust last point"
        + string_spacing
        + "ENTER = close border"
        + string_spacing
        + "UP/DOWN = change smoothing resolution",
        font_name=graphics_constants.drawer_instruction_label_font_name,
        font_size=graphics_constants.drawer_instruction_label_font_size,
        x=graphics_constants.drawer_instruction_label_x,
        y=graphics_constants.drawer_instruction_label_y,
        color=graphics_constants.white_color,
        multiline=True,
        width=graphics_constants.resolution_width,
    )

    instruction_label_finished_drawing = pyglet.text.Label(
        "Adjust smoothing resolution\n" "ENTER = save track" + string_spacing + "UP/DOWN = change smoothing resolution",
        font_name=graphics_constants.drawer_instruction_label_font_name,
        font_size=graphics_constants.drawer_instruction_label_font_size,
        x=graphics_constants.drawer_instruction_label_x,
        y=graphics_constants.drawer_instruction_label_y,
        color=graphics_constants.white_color,
        multiline=True,
        width=graphics_constants.resolution_width,
    )

    instruction_label_placing_car = pyglet.text.Label(
        "Place car\n"
        "Move mouse to place car" + string_spacing + "A/D = rotate car " + string_spacing + "ENTER = save track",
        font_name=graphics_constants.drawer_instruction_label_font_name,
        font_size=graphics_constants.drawer_instruction_label_font_size,
        x=graphics_constants.drawer_instruction_label_x,
        y=graphics_constants.drawer_instruction_label_y,
        color=graphics_constants.white_color,
        multiline=True,
        width=graphics_constants.resolution_width,
    )

    smoothing_label = pyglet.text.Label(
        f"Smoothing resolution: {smoothing_resolution}",
        font_name=graphics_constants.drawer_instruction_label_font_name,
        font_size=graphics_constants.drawer_instruction_smoothing_label_font_size,
        x=graphics_constants.drawer_instruction_smoothing_label_x,
        y=graphics_constants.drawer_instruction_smoothing_label_y,
        color=graphics_constants.white_color,
    )

    grid_instruction_label = pyglet.text.Label(
        "G = enable/disable grid"
        + string_spacing
        + "T = increase columns"
        + string_spacing
        + "V = decrease columns"
        + string_spacing
        + "F = increase rows"
        + string_spacing
        + "H = decrease rows",
        font_name=graphics_constants.drawer_instruction_label_font_name,
        font_size=graphics_constants.drawer_instruction_grid_font_size,
        x=graphics_constants.drawer_instruction_grid_label_x,
        y=graphics_constants.drawer_instruction_grid_label_y,
        color=graphics_constants.white_color,
    )

    instruction_label_gates = pyglet.text.Label(
        "Place gates\nLeft click = place first point"
        + string_spacing
        + "Right click = replace last point"
        + string_spacing
        + "ENTER = save gates and quit",
        font_name=graphics_constants.drawer_instruction_label_font_name,
        font_size=graphics_constants.drawer_instruction_label_font_size,
        x=graphics_constants.drawer_instruction_label_x,
        y=graphics_constants.drawer_instruction_label_y,
        color=graphics_constants.white_color,
        multiline=True,
        width=graphics_constants.resolution_width,
    )

    def add_point(x: float, y: float, step: DrawingState) -> None:
        """
        Add a point (x, y) to the list for the given mode ("outer" or "inner" or "gates").
        Updates the drawn polyline and triggers smoothing.

        :param x: X coordinate of the point.
        :param y: Y coordinate of the point.
        :param step: Identifying which point list to modify.
        :return: None
        """
        mode = step_to_mode[step]
        pts = points[mode]
        pts.append([x, y])
        if step != DrawingState.GATES_PLACEMENT:
            if len(pts) > 1:
                draw_lines(
                    original_segments_batch,
                    original_lines[mode],
                    mode,
                    pts,
                    graphics_constants.white_color,
                )
            update_smooth()
        else:
            draw_lines(gates_batch, gates_lines, mode, pts, graphics_constants.yellow_color)

    def adjust_last_point(x: float, y: float, step: DrawingState) -> None:
        """
        Move the last added point for the given mode to a new (x, y) location.
        Updates the drawn polyline and triggers smoothing.

        :param x: New X coordinate.
        :param y: New Y coordinate.
        :param step: Identifying which point list to update.
        :return: None
        """
        mode = step_to_mode[step]
        pts = points[mode]
        if not pts:
            return
        pts[-1] = [x, y]
        if step != DrawingState.GATES_PLACEMENT:
            if len(pts) > 1:
                draw_lines(
                    original_segments_batch,
                    original_lines[mode],
                    mode,
                    pts,
                    graphics_constants.white_color,
                )
            update_smooth()
        else:
            draw_lines(gates_batch, gates_lines, mode, pts, graphics_constants.yellow_color)
            update_preview_gate(*pts[-1])

    def update_preview(x: float, y: float, mode: str) -> None:
        """
        Update the preview line shown between the last point and the mouse cursor.

        :param x: current mouse x coordinate.
        :param y: current mouse y coordinate.
        :param mode: Active drawing mode ("outer" or "inner").
        :return: None
        """
        nonlocal preview_line
        pts = points[mode]
        if len(pts) == 0:
            if preview_line:
                preview_line = None
            return

        if drawing_step != DrawingState.DRAW_OUTER and drawing_step != DrawingState.DRAW_INNER:
            return

        x1, y1 = pts[-1]
        preview_line = shapes.Line(
            x1,
            y1,
            x,
            y,
            color=graphics_constants.red_color,
            batch=original_segments_batch,
        )

    def update_preview_gate(x: float, y: float) -> None:
        """
        Update the preview line for gates while placing.
        Draws a line from the last placed point to the mouse cursor.
        :param x: current mouse x coordinate.
        :param y: current mouse y coordinate.
        :return: None
        """
        nonlocal preview_gate_line
        pts = points["gates"]
        if not pts or len(pts) % 2 == 0:
            if preview_gate_line:
                preview_gate_line.delete()
                preview_gate_line = None
            return

        x1, y1 = pts[-1]
        if preview_gate_line:
            preview_gate_line.delete()
        preview_gate_line = shapes.Line(x1, y1, x, y, color=graphics_constants.red_color, batch=gates_batch)

    def update_smooth() -> None:
        """
        Recompute and redraw the Catmull-Rom smoothed curves for inner and outer points.
        Also updates the UI label showing smoothing resolution and total point count.

        :return: None
        """
        smooth_outer_points = catmull_rom_spline(
            points["outer"],
            smoothing_resolution,
            graphics_constants.resolution_width,
            graphics_constants.resolution_height,
        )
        smooth_inner_points = catmull_rom_spline(
            points["inner"],
            smoothing_resolution,
            graphics_constants.resolution_width,
            graphics_constants.resolution_height,
        )

        draw_lines(
            smooth_segments_batch,
            smooth_lines["outer"],
            "outer",
            smooth_outer_points,
            graphics_constants.green_color,
        )
        draw_lines(
            smooth_segments_batch,
            smooth_lines["inner"],
            "inner",
            smooth_inner_points,
            graphics_constants.green_color,
        )

        smoothing_label.text = f"Smoothing resolution: {smoothing_resolution}. Points: {len(smooth_outer_points) +
                                                                                        + len(smooth_inner_points)}"

    def draw_grid(
        batch: pyglet.graphics.Batch,
        width: int,
        height: int,
        rows: int,
        cols: int,
        color: tuple[int, int, int, int],
    ) -> List[shapes.Line]:
        """
        Draw a rectangular grid on the window using pyglet shapes.

        :param batch: The pyglet Batch used for grouping drawing operations.
        :param width: Width of the window or drawing area.
        :param height: Height of the window or drawing area.
        :param rows: Number of horizontal rows in the grid.
        :param cols: Number of vertical columns in the grid.
        :param color: RGB color tuple for the grid lines.
        :return: List of Line objects created for the grid.
        """
        lines: List[shapes.Line] = []

        # horizontal lines
        for i in range(1, rows):
            y = i * height / rows
            lines.append(shapes.Line(0, y, width, y, color=color, batch=batch))

        # vertical lines
        for j in range(1, cols):
            x = j * width / cols
            lines.append(shapes.Line(x, 0, x, height, color=color, batch=batch))

        return lines

    def save_borders() -> None:
        """
        Save the smoothed points to disk.

        :return: None
        """
        for mode in ["inner", "outer"]:
            save_points(
                catmull_rom_spline(
                    points[mode],
                    smoothing_resolution,
                    graphics_constants.resolution_width,
                    graphics_constants.resolution_height,
                ),
                f"{OUTPUT_PATH}{mode}.txt",
            )

    def save_gates() -> None:
        """
        Save gates to disk
        """
        with open(f"{OUTPUT_PATH}gates.txt", "w") as f:
            for i in range(0, len(points["gates"]), 2):
                x1, y1 = points["gates"][i]
                x2, y2 = points["gates"][i + 1]
                f.write(f"{x1} {y1} {x2} {y2}\n")

    def close_border(mode: ModeType) -> None:
        """
        Close the shape by connecting the last point to the first.
        Update smoothing, redraw the original polyline.

        :param mode: string to understand if it's the inner or outer border
        :return: None
        """
        points[mode].append(points[mode][0])
        update_smooth()
        draw_lines(
            original_segments_batch,
            original_lines[mode],
            mode,
            points[mode],
            graphics_constants.white_color,
        )

    @window.event
    def on_draw() -> None:
        """
        Render the window content: instructions label, all batched drawings, and smoothing label.

        :return: None
        """
        window.clear()
        match drawing_step:
            case DrawingState.DRAW_OUTER:
                label = instruction_label_outer
            case DrawingState.DRAW_INNER:
                label = instruction_label_inner
            case DrawingState.FINISHED_DRAWING:
                label = instruction_label_finished_drawing
            case DrawingState.CAR_PLACEMENT:
                label = instruction_label_placing_car
            case DrawingState.GATES_PLACEMENT:
                label = instruction_label_gates
            case _:
                label = None
        label.draw()

        smoothing_label.draw()
        grid_instruction_label.draw()
        if show_grid:
            grid_lines = draw_grid(
                grid_batch,
                graphics_constants.resolution_width,
                graphics_constants.resolution_height,
                grid_rows,
                grid_columns,
                graphics_constants.grey_color,
            )
            for line in grid_lines:
                line.draw()
        smooth_segments_batch.draw()
        if smoothing_resolution > 0 and (
            drawing_step == DrawingState.DRAW_OUTER
            or drawing_step == DrawingState.DRAW_INNER
            or drawing_step == DrawingState.FINISHED_DRAWING
        ):
            original_segments_batch.draw()

        if (
            drawing_step == DrawingState.CAR_PLACEMENT or drawing_step == DrawingState.GATES_PLACEMENT
        ) and car_instance is not None:
            car_instance.show()

        if drawing_step == DrawingState.GATES_PLACEMENT:
            gates_batch.draw()

        gates_batch.draw()
        if preview_gate_line:
            preview_gate_line.draw()

    @window.event
    def on_mouse_motion(x: float, y: float, dx: float, dy: float) -> None:
        """
        Handle mouse movement and update the preview line or car position depending on the step.

        :param x: New mouse X.
        :param y: New mouse Y.
        :param dx: Mouse delta X.
        :param dy: Mouse delta Y.
        :return: None
        """
        if drawing_step == DrawingState.CAR_PLACEMENT and car_instance is not None:
            car_instance.x = x
            car_instance.y = y
            car_instance.car_sprite.update(x=x, y=y)
        elif drawing_step == DrawingState.GATES_PLACEMENT:
            update_preview_gate(x, y)
        else:
            mode = "outer" if drawing_step == DrawingState.DRAW_OUTER else "inner"
            update_preview(x, y, mode)

    @window.event
    def on_mouse_press(x: float, y: float, button: int, modifiers: int) -> None:
        """
        Handle mouse clicks: left adds a point, right adjusts the last point.

        :param x: Mouse X.
        :param y: Mouse Y.
        :param button: Mouse button constant.
        :param modifiers: Modifier keys.
        :return: None
        """
        if drawing_step == DrawingState.FINISHED_DRAWING or drawing_step == DrawingState.CAR_PLACEMENT:
            return

        if button == mouse.LEFT:
            add_point(x, y, drawing_step)
        elif button == mouse.RIGHT:
            adjust_last_point(x, y, drawing_step)

    @window.event
    def on_key_press(symbol: int, modifiers: int) -> None:
        """
        Handle keyboard input for drawing, smoothing, grid, and car placement.

        :param symbol: Key symbol.
        :param modifiers: Key modifiers.
        :return: None
        """
        nonlocal drawing_step, preview_line, smoothing_resolution
        nonlocal show_grid, grid_rows, grid_columns, car_instance
        if symbol == key.ENTER:
            if drawing_step == DrawingState.DRAW_OUTER:
                if len(points["outer"]) < 3:
                    return
                close_border("outer")
                drawing_step = DrawingState.DRAW_INNER
            elif drawing_step == DrawingState.DRAW_INNER:
                if len(points["inner"]) < 3:
                    return
                close_border("inner")
                preview_line = None
                drawing_step = DrawingState.FINISHED_DRAWING
            elif drawing_step == DrawingState.FINISHED_DRAWING:
                save_borders()
                drawing_step = DrawingState.CAR_PLACEMENT
                car_instance = Car(
                    x=graphics_constants.resolution_width / 2,
                    y=graphics_constants.resolution_height / 2,
                    heading=0,
                    borders=[],
                    gates=[],
                    driven=False,
                    replay=None,
                )
            elif drawing_step == DrawingState.CAR_PLACEMENT:
                if car_instance is not None:
                    with open(f"{OUTPUT_PATH}starting_position.txt", "w") as f:
                        f.write(f"{int(car_instance.x)} {int(car_instance.y)} {int(car_instance.car_heading)}\n")
                    drawing_step = DrawingState.GATES_PLACEMENT
            elif drawing_step == DrawingState.GATES_PLACEMENT:
                if len(points["gates"]) % 2 == 1:
                    return
                save_gates()
                pyglet.app.exit()
        elif symbol == key.A:
            if drawing_step == DrawingState.CAR_PLACEMENT and car_instance is not None:
                car_instance.car_heading = (car_instance.car_heading - car_rotation_step) % 360
                car_instance.car_sprite.rotation = -car_instance.car_heading
        elif symbol == key.D:
            if drawing_step == DrawingState.CAR_PLACEMENT and car_instance is not None:
                car_instance.car_heading = (car_instance.car_heading + car_rotation_step) % 360
                car_instance.car_sprite.rotation = -car_instance.car_heading
        elif symbol == key.UP:
            if (
                drawing_step == DrawingState.DRAW_OUTER
                or drawing_step == DrawingState.DRAW_INNER
                or drawing_step == DrawingState.FINISHED_DRAWING
            ):
                smoothing_resolution = min(smoothing_resolution + 1, 20)
                update_smooth()
        elif symbol == key.DOWN:
            if (
                drawing_step == DrawingState.DRAW_OUTER
                or drawing_step == DrawingState.DRAW_INNER
                or drawing_step == DrawingState.FINISHED_DRAWING
            ):
                smoothing_resolution = max(smoothing_resolution - 1, 0)
                update_smooth()
        elif symbol == key.G:
            show_grid = not show_grid
        elif symbol == key.F:
            grid_rows += 1
        elif symbol == key.H:
            grid_rows = max(1, grid_rows - 1)
        elif symbol == key.T:
            grid_columns += 1
        elif symbol == key.V:
            grid_columns = max(1, grid_columns - 1)

        grid_lines = draw_grid(
            grid_batch,
            graphics_constants.resolution_width,
            graphics_constants.resolution_height,
            grid_rows,
            grid_columns,
            graphics_constants.grey_color,
        )
        if show_grid:
            for line in grid_lines:
                line.delete()
            grid_lines[:] = draw_grid(
                grid_batch,
                graphics_constants.resolution_width,
                graphics_constants.resolution_height,
                grid_rows,
                grid_columns,
                graphics_constants.grey_color,
            )
        else:
            for line in grid_lines:
                line.delete()
            grid_lines.clear()

    pyglet.app.run()


if __name__ == "__main__":
    main()
