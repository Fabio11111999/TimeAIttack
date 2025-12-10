import json
import ast


class replay:
    class frame:
        def __init__(self, frame_number, delta_time, xp, yp, car_heading, alive, completed, pressed_keys):
            self.frame = frame_number
            self.dt = delta_time
            self.x = xp
            self.y = yp
            self.heading = car_heading
            self.alive = alive
            self.completed = completed
            self.keys = pressed_keys

        def __str__(self):
            return (
                str(self.frame)
                + "\t"
                + str(self.dt)
                + "\t"
                + str(self.x)
                + "\t"
                + str(self.y)
                + "\t"
                + str(self.heading)
                + "\t"
                + str(self.alive)
                + "\t"
                + str(self.completed)
                + "\t"
                + str(self.keys)
            )

    def __init__(self):
        self.log = []

    def add(self, frame):
        self.log.append(frame)

    def reset(self):
        self.log = []

    def print_to_file(self, name):
        ofile = open("../replays/" + name, "w")
        for f in self.log:
            ofile.write(f.__str__() + "\n")

    def read_from_file(self, name):
        ifile = open("../replays/" + name, "r")
        self.reset()
        for row in ifile:
            row = row[0:-1].split("\t")
            self.add(
                self.frame(
                    int(row[0]),
                    float(row[1]),
                    float(row[2]),
                    float(row[3]),
                    float(row[4]),
                    row[5] == "True",
                    row[6] == "True",
                    ast.literal_eval(row[7]),
                )
            )
