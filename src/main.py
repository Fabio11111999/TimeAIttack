from typing import Literal

import game
import graphics_constants
import make_replay
import viewer


def main() -> None:
    mode: Literal["play", "view"] = "view"

    if mode == "play":
        game1 = game.Game(
            graphics_constants.resolution_width, graphics_constants.resolution_height, "../tracks/drawer/"
        )
        replay = game1.new_game()
        replay.save_to_file("test_json.json")
    else:
        replay = make_replay.Replay()
        replay.load_from_file("test_json.json")
        viewer1 = viewer.Viewer(graphics_constants.resolution_width, graphics_constants.resolution_height, replay)
        viewer1.view()


if __name__ == "__main__":
    main()
