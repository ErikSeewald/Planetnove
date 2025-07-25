from tank.sensors.infrared import SensorBitmap

class PController:
    """
    Line following P controller used to map sensor input to a wheel speed correction.
    Note: Used to be a PID controller, but with the discrete bitmap values I and D do not work well.
    Instead, this modified P controller makes use of an accumulated error with a maximum to mimic some PID behavior
    when the line following line is completely out of sight.
    """

    bitmap_to_error: dict[SensorBitmap, float] = {
        SensorBitmap.NONE: float("inf"),
        SensorBitmap.RIGHT: -1.0,
        SensorBitmap.MIDDLE: 0.0,
        SensorBitmap.MIDDLE_RIGHT: -0.5,
        SensorBitmap.LEFT: 1.0,
        SensorBitmap.LEFT_RIGHT: float("inf"),
        SensorBitmap.LEFT_MIDDLE: 0.5,
        SensorBitmap.ALL: 0.0
    }

    def __init__(self, kp: float):
        self.kp = kp
        self.MAX_ABS_ERROR = kp * 3 # Maximum absolute cumulative error
        self.last_error = 0.0
        self.last_bitmap = SensorBitmap.NONE

    def reset(self):
        """
        Resets the controller. Avoids having old accumulated errors affect new departures.
        """
        self.last_error = 0.0
        self.last_bitmap = SensorBitmap.ALL

    def compute_correction(self, bitmap: SensorBitmap) -> float:
        """
        Returns the correction to be applied to wheel speed based on the SensorBitmap input.
        """

        error = self.bitmap_to_error[bitmap]

        # Accumulate error if the line is out of sight
        if error == float("inf"):
            error = self.last_error
            if abs(error) < self.MAX_ABS_ERROR:
                error = min(error * 1.5, self.MAX_ABS_ERROR)

        correction = self.kp * error
        self.last_error = error
        return correction
