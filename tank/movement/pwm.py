import pigpio


class PWM:
    """
    Slight modification of the original uncalibrated Motor class provided by Freenove.
    Handles setting the duty range of the separate wheel motors through pigpio.
    """

    def __init__(self):
        self.pwm1 = 24
        self.pwm2 = 23
        self.pwm3 = 5
        self.pwm4 = 6
        self.PwmServo = pigpio.pi()
        self.PwmServo.set_mode(self.pwm1, pigpio.OUTPUT)
        self.PwmServo.set_mode(self.pwm2, pigpio.OUTPUT)
        self.PwmServo.set_mode(self.pwm3, pigpio.OUTPUT)
        self.PwmServo.set_mode(self.pwm4, pigpio.OUTPUT)
        self.PwmServo.set_PWM_frequency(self.pwm1, 50)
        self.PwmServo.set_PWM_frequency(self.pwm2, 50)
        self.PwmServo.set_PWM_frequency(self.pwm3, 50)
        self.PwmServo.set_PWM_frequency(self.pwm4, 50)
        self.PwmServo.set_PWM_range(self.pwm1, 4095)
        self.PwmServo.set_PWM_range(self.pwm2, 4095)
        self.PwmServo.set_PWM_range(self.pwm3, 4095)
        self.PwmServo.set_PWM_range(self.pwm4, 4095)

    def set_left_wheel(self, duty: int):
        self.single_wheel_duty(duty, self.pwm1, self.pwm2)

    def set_right_wheel(self, duty: int):
        self.single_wheel_duty(duty, self.pwm3, self.pwm4)

    def single_wheel_duty(self, duty: int, pwm_a: int, pwm_b: int):
        if duty > 0:
            self.PwmServo.set_PWM_dutycycle(pwm_a, 0)
            self.PwmServo.set_PWM_dutycycle(pwm_b, duty)
        elif duty < 0:
            self.PwmServo.set_PWM_dutycycle(pwm_a, abs(duty))
            self.PwmServo.set_PWM_dutycycle(pwm_b, 0)
        else:
            self.PwmServo.set_PWM_dutycycle(pwm_a, 0)
            self.PwmServo.set_PWM_dutycycle(pwm_b, 0)

    def setMotors(self, duty_left: float, duty_right: float):
        duty_left, duty_right = limit_duty_range(int(duty_left), int(duty_right))
        self.set_left_wheel(duty_left)
        self.set_right_wheel(duty_right)

    def stop(self):
        self.setMotors(0, 0)


def limit_duty_range(duty1: int, duty2: int) -> tuple[int, int]:
    """
    :return: Tuple(duty1, duty2) limited to the hardware specific ranges.
    """

    if duty1 > 4095:
        duty1 = 4095
    elif duty1 < -4095:
        duty1 = -4095
    if duty2 > 4095:
        duty2 = 4095
    elif duty2 < -4095:
        duty2 = -4095
    return duty1, duty2
