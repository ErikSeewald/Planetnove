import RPi.GPIO as GPIO
import time


class Ultrasonic:
    """
    Slight modification of the original ultrasonic provided by Freenove.
    """

    def __init__(self):
        GPIO.setwarnings(False)
        self.trigger_pin = 27
        self.echo_pin = 22
        self.MAX_DISTANCE_CM = 300
        self.timeout = (self.MAX_DISTANCE_CM * 60) * 0.000001
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.trigger_pin, GPIO.OUT)
        GPIO.setup(self.echo_pin, GPIO.IN)

    def pulse(self, gpio_level) -> float:
        """
        :return: Pulse time for the echo pin, or 0 if the pulse timed out
        """

        t0 = time.time()
        while GPIO.input(self.echo_pin) != gpio_level:
            if (time.time() - t0) > self.timeout:
                return 0

        t0 = time.time()
        while GPIO.input(self.echo_pin) == gpio_level:
            if (time.time() - t0) > self.timeout:
                return 0

        return time.time() - t0

    def get_distance_cm(self) -> float:
        """
        :return: Measured distance in centimeters
        """

        distances_cm = [0.0, 0.0, 0.0, 0.0, 0.0]
        for i in range(5):
            GPIO.output(self.trigger_pin, GPIO.HIGH)
            time.sleep(0.00001)
            GPIO.output(self.trigger_pin, GPIO.LOW)

            pulse_time = self.pulse(GPIO.HIGH)
            distances_cm[i] = pulse_time * 340.0 / 2.0 * 100  # distance with speed of sound 340m/s

        distances_cm = sorted(distances_cm)
        median = distances_cm[2]
        return median if median > 0 else float("inf")
