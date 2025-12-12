from __future__ import annotations

import json
from typing import Dict, List, Mapping


class Replay:
    class Frame:
        """
        A single recorder fram of the simulation
        """

        def __init__(
            self,
            frame_number: int,
            delta_time: float,
            x: float,
            y: float,
            heading: float,
            alive: bool,
            completed: bool,
            pressed_keys: Mapping[int, bool],
        ):
            """
            Create new frame

            :param frame_number: how many frame are there before this one
            :param delta_time: difference in time from the previous frame
            :param x: car x position at this frame
            :param y: car y position at this frame
            :param heading: angle of the car at this frame
            :param alive: boolean stating if the car is still running
            :param completed: boolean stating if the lap is completed
            :param pressed_keys: dictionary stating the key pressed at this frame
            """
            self.frame: int = frame_number
            self.dt: float = delta_time
            self.x: float = x
            self.y: float = y
            self.heading: float = heading
            self.alive: bool = alive
            self.completed: bool = completed
            self.keys: Dict[int, bool] = dict(pressed_keys)

        def to_dict(self) -> dict:
            """
            Convert frame to dict for JSON serialization
            :return: Dictionary with the fram info
            """
            return {
                "frame": self.frame,
                "dt": self.dt,
                "x": self.x,
                "y": self.y,
                "heading": self.heading,
                "alive": self.alive,
                "completed": self.completed,
                "keys": self.keys,
            }

        @staticmethod
        def from_dict(d: dict) -> Replay.Frame:
            """
            Create Frame from dictionary.

            :return: Frame with values taken from dictionary
            """
            return Replay.Frame(
                frame_number=d["frame"],
                delta_time=d["dt"],
                x=d["x"],
                y=d["y"],
                heading=d["heading"],
                alive=d["alive"],
                completed=d["completed"],
                pressed_keys=d["keys"],
            )

    def __init__(self, track_path: str | None = None) -> None:
        """
        Create new list of frames

        :return: None
        """
        self.track_path: str | None = track_path
        self.log: List[Replay.Frame] = []

    def add(self, frame: Replay.Frame) -> None:
        """
        Add frame to replay file

        :param frame: frame to add
        :return: None
        """
        self.log.append(frame)

    def reset(self) -> None:
        """
        Clear all frames from replay

        :return: None
        """
        self.log = []

    def save_to_file(self, filename: str) -> None:
        """
        Save replay as JSON file

        :param filename: name of the replay file
        :return: None
        """
        data = {"track_path": self.track_path, "frames": [frame.to_dict() for frame in self.log]}
        with open(f"../replays/{filename}", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load_from_file(self, filename: str) -> None:
        """
        Load replay from JSON file

        :param filename: name of the replay file
        :return: None
        """
        self.reset()
        with open(f"../replays/{filename}", "r", encoding="utf-8") as f:
            data = json.load(f)
            self.track_path = data.get("track_path")
            for frame_dict in data["frames"]:
                self.add(Replay.Frame.from_dict(frame_dict))
