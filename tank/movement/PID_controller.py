import time
from tank.sensors.infrared import SensorBitmap


class PIDController:
    bitmap_to_error: dict[SensorBitmap, float] = {
        SensorBitmap.NONE: float("inf"),
        SensorBitmap.RIGHT: 1.0,
        SensorBitmap.MIDDLE: 0,
        SensorBitmap.MIDDLE_RIGHT: 0.5,
        SensorBitmap.LEFT: -1.0,
        SensorBitmap.LEFT_RIGHT: -float("inf"),
        SensorBitmap.LEFT_MIDDLE: -0.5,
        SensorBitmap.ALL: 0
    }

    def __init__(self, kp: float, ki: float, kd: float):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.last_error = 0.0
        self.integral = 0.0
        self.last_time = time.time()

    def compute_correction(self, bitmap: SensorBitmap) -> float:
        current_time = time.time()
        delta_time = current_time - self.last_time
        if delta_time <= 0:
            delta_time = 1e-3

        error = self.bitmap_to_error[bitmap]
        self.integral += error * delta_time
        derivative = (error - self.last_error) / delta_time
        output = self.kp * error + self.ki * self.integral + self.kd * derivative
        self.last_error = error
        self.last_time = current_time
        return output