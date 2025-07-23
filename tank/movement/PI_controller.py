import time
from tank.sensors.infrared import SensorBitmap


class PIController:
    """
    Line following PI controller used to map sensor input to a wheel speed correction.
    """

    bitmap_to_error: dict[SensorBitmap, float] = {
        SensorBitmap.NONE: float("inf"),
        SensorBitmap.RIGHT: -1.0,
        SensorBitmap.MIDDLE: 0.0,
        SensorBitmap.MIDDLE_RIGHT: -0.5,
        SensorBitmap.LEFT: 1.0,
        SensorBitmap.LEFT_RIGHT: -float("inf"),
        SensorBitmap.LEFT_MIDDLE: 0.5,
        SensorBitmap.ALL: 0.0
    }

    def __init__(self, kp: float, ki: float):
        self.kp = kp
        self.ki = ki
        self.last_error = 0.0
        self.integral = 0.0
        self.last_time = time.time()

    def compute_correction(self, bitmap: SensorBitmap) -> float:
        """
        Returns the correction to be applied to wheel speed based on the SensorBitmap input.
        """

        current_time = time.time()
        delta_time = current_time - self.last_time
        if delta_time <= 0:
            delta_time = 1e-3

        error = self.bitmap_to_error[bitmap]
        if abs(error) > 1:
            error = self.last_error

        self.integral += error * delta_time
        correction = self.kp * error + self.ki * self.integral
        self.last_error = error
        self.last_time = current_time
        return correction
