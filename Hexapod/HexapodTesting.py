from Control import *
from Led import *
from Ultrasonic import *
import time


# --------------------------------------
# -------------- MOVEMENT --------------
# --------------------------------------

def relax(control, turn_on: bool) -> None:
    if turn_on:
        GPIO.output(control.GPIO_4, True)
        print("Hexapod relaxed")
    else:
        GPIO.output(control.GPIO_4, False)
        print("Hexapod no longer relaxed")


def parseMoveCMD(turn='none', move='none', gait_mode=1, speed=10, action_mode=2) -> list:
    # TURN
    turn_to_x = {'none': '0', 'right': '10', 'left': '-10'}
    x = turn_to_x.get(turn)

    # MOVE
    move_to_y = {'none': '0', 'forward': '30', 'backward': '-30'}
    y = move_to_y.get(move)

    # ANGLE
    angle = 0
    if action_mode == 2:
        if turn == 'none':
            angle = '0'
        else:
            angle = '-10' if turn == 'left' else '10'
        x = 0

    # example:
    # data=['CMD_MOVE', '1', '0', '25', '10', '0']
    # Gait Mode: "1"
    # Moving direction: x='0',y='25'
    # (x - Turn, y - Forward  | Both are capped between -35 and 35)
    # Speed:'10'
    # Angle: (Action Mode 1): '0'
    # (Action Mode 2): '10' (Anything beyond 10 makes it go wild)
    return ['CMD_MOVE', str(gait_mode), x, y, str(speed), angle]


def sendParsedMoveCMD(control, command, steps=3) -> None:
    print(f"Sending command: {command} times {steps}")
    for i in range(steps):
        control.run(command)


def sendMoveCMD(control, turn='none', move='none', steps=3, gait_mode=1, speed=10, action_mode=2) -> None:
    """
    :param control: Hexapod Control instance
    :param turn: either 'none', 'right' or 'left'
    :param move: either 'none', 'forward' or 'backward'
    :param steps: Amount of steps of the given action to take
    :param gait_mode: 0 (Each leg one after the other) or 1 (All legs at the same time)
    :param speed: 2 to 10
    :param action_mode: 1 (No turning) 2 (Turning)
    :return: None
    """

    print(f"Move instruction: "
          f"[turn={turn}, move={move}, steps={steps}, gait_move={gait_mode}, speed={speed}, action_mode={action_mode}")
    sendParsedMoveCMD(control, parseMoveCMD(turn, move, gait_mode, speed, action_mode), steps)


def walkUntilUltrasonicBelow(control, ultrasonic, below) -> None:
    distance = ultrasonic.getDistance()
    command = parseMoveCMD(move='forward')
    setHeadYaw(control, 90)
    setHeadPitch(control, 100)
    while distance > below:
        print(distance)
        sendParsedMoveCMD(control, command, steps=1)
        distance = ultrasonic.getDistance()


# --------------------------------------
# ---------------- HEAD ----------------
# --------------------------------------

def setHeadYaw(control, angle) -> None:
    """
    :param control: Hexapod Control instance
    :param angle: Turn angle (LEFT:180, STRAIGHT:90, RIGHT:0)
    :return: None
    """
    control.servo.setServoAngle(1, angle)
    print(f"Head yaw set to {angle}")


def setHeadPitch(control, angle) -> None:
    """
    :param control: Hexapod Control instance
    :param angle: Turn angle (DOWN: 50, STRAIGHT:100, UP: 180)
    :return: None
    """
    control.servo.setServoAngle(0, angle)
    print(f"Head pitch set to {angle}")


# --------------------------------------
# ---------------- LED -----------------
# --------------------------------------

def setAllLEDsTo(led, r, g, b) -> None:
    color = led.LED_TYPR('RGB', Color(r, g, b))
    for i in range(led.strip.numPixels()):
        led.strip.setPixelColor(i, color)
    led.strip.show()

    print(f"Set all LEDs to [{r}, {g}, {b}]")


# --------------------------------------
# ---------------- MAIN ----------------
# --------------------------------------

# This file needs to be placed in <Hexapod-Directory>/Code/Server to run
def main() -> None:
    # Erik: All the functions in the file do not even come close to all the things the
    # Hexapod can do yet. To add more, just look through the python files in the Code/Server directory
    # and see what functions have not been added here yet
    # This file mainly focuses on providing an easier interface for understanding the Hexapod Commands

    # CONTROL
    control = Control()
    sendMoveCMD(control, turn='right', move='none')

    # LED
    led = Led()
    setAllLEDsTo(led, 0, 20, 0)
    time.sleep(2)
    setAllLEDsTo(led, 20, 0, 0)
    time.sleep(2)
    setAllLEDsTo(led, 0, 0, 0)

    # ULTRASONIC
    ultrasonic = Ultrasonic()
    walkUntilUltrasonicBelow(control, ultrasonic, 30)

    setHeadYaw(control, 90)
    setHeadPitch(control, 170)

    relax(control, True)


main()
