from movement.line_following import LineFollower
from movement.calibrated_motor import CalibratedMotor
from sensors.infrared import InfraredSensor


motor = CalibratedMotor()
sensor = InfraredSensor()
line_follower = LineFollower(sensor, motor)
line_follower.run()
