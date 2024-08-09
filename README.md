# Planetnove
A planet exploration sim using Freenove robots.

## Board
The board representing the planets is made up of 1m x 1m white wooden pieces that can be rearranged into different layouts. 

## Mothership
Unlike the other actors, the mothership is not a physical agent on the board. It receives messages from and sends commands to its agents from afar.
The mothership is hosted on the main device running Planetnove, usually a PC or Laptop.

## Tank
The tank explores the planet and communicates with the mothership. It is hosted on a raspberry pi 4 on the [Freenove Tank Robot](https://github.com/Freenove/Freenove_Tank_Robot_Kit_for_Raspberry_Pi). It's components include infrared sensors for line following,
an ultrasound sensor, a camera, LEDs and a crane arm for picking up objects.

## Hexapod
The hexapod does not yet have an active role in Planetnove. It is hosted on raspberry pi 4 on the [Freenove Big Hexapod Robot](https://github.com/Freenove/Freenove_Big_Hexapod_Robot_Kit_for_Raspberry_Pi).
