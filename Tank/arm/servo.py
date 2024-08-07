import pigpio


class Servo:
    """
    Slight modification of the original crane arm servo class provided by Freenove.
    """

    def __init__(self):
        self.channel1 = 7
        self.channel2 = 8
        self.channel3 = 25
        self.PwmServo = pigpio.pi()
        self.PwmServo.set_mode(self.channel1, pigpio.OUTPUT)
        self.PwmServo.set_mode(self.channel2, pigpio.OUTPUT)
        self.PwmServo.set_mode(self.channel3, pigpio.OUTPUT)
        self.PwmServo.set_PWM_frequency(self.channel1, 50)
        self.PwmServo.set_PWM_frequency(self.channel2, 50)
        self.PwmServo.set_PWM_frequency(self.channel3, 50)
        self.PwmServo.set_PWM_range(self.channel1, 4000)
        self.PwmServo.set_PWM_range(self.channel2, 4000)
        self.PwmServo.set_PWM_range(self.channel3, 4000)

    def setServoPwm(self, channel: int, angle: float):
        angle = limit_angle_range(0, angle)
        pwm_angle = 80 + (400 / 180) * angle

        if channel == 0:
            self.PwmServo.set_PWM_dutycycle(self.channel1, pwm_angle)
        elif channel == 1:
            self.PwmServo.set_PWM_dutycycle(self.channel2, pwm_angle)
        elif channel == 2:
            self.PwmServo.set_PWM_dutycycle(self.channel3, pwm_angle)


def limit_angle_range(channel: int, init_angle: float) -> int:
    """
    :return: Initial angle limited to the channel specific range.
    """
    if channel == 0 or channel == 1:
        if init_angle < 90:
            init_angle = 90
        elif init_angle > 150:
            init_angle = 150
    elif channel == 2:
        if init_angle < 0:
            init_angle = 0
        elif init_angle > 180:
            init_angle = 180

    return int(init_angle)
