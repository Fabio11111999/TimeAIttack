"""

Constant value for car movements

"""

wheel_base = 64  # Distance between wheels
steering_angle = 35  # Turning angle for front wheel
engine_power = 800  # Power used during acceleration
friction = 1.0  # Ground resistance (most effective on low speeds)
drag = 0.001  # Air resistance (most effective on high speeds)
braking = -450  # Power used during braking
max_speed_reverse = 250  # Max speed going backwards
slip_speed1 = 150  # Above this speed you start drifting more
slip_speed2 = 350  # Above this speed tou start drifting much more
traction_fast = 0.1  # Traction when going fast
traction_mid = 0.2  # Traction when going medium speed
traction_slow = 0.4  # Traction when going slow
