# Planetnove
A planet exploration sim using Freenove robots.

The tank robot explores the planet board using simple line following. Whenever it reaches a node, it starts communicating with the mothership. When it has decided what direction to depart in, it sends that information to the mothership and waits for confirmation. The mothership can then use its superior triangulation processing power to determine the next node the tank will arive at. Upon arrival the tank notifies the mothership and then receives a message with it's new position as well as the available paths from this
position. To keep the cost of communications low, the tank has to remember the map layout and make its own pathing decisions based on only these short messages.
Once the tank has explored the entire planet, i.e. has explored all paths of all nodes that it encountered, it informs the mothership.

There are a few additional cases that can happen:
- The mothership rejects the tank's request for departue in a direction. In that case the tank will need to choose another direction and send another request. (Note: The motherships rejection of a direction at a node is temporary. If the tank returns to the same node
later it can ask about taking that direction again.)
- The tank encounters an obstacle on the path. It will then have to turn around and notify the mothership of the blocked path. *After* the mothership has confirmed receiving the blocked path message, the tank can send a new arrival message
for the node it just returned to from the blocked path. (Note: The blocked path is permanent. Once the path is considered blocked it will not be unblocked for the remainder of the run/until the tank is disconnected. More information about blocking in the section 'Path blocking')
- The tank is stuck and unable to finish exploring the planet. This can happen if all routes to unexplored nodes lead through paths that have been blocked or if the mothership rejects all departure directions that the tank could take to get to the unexplored nodes.
In that case, the tank informs the mothership that it is stuck and finishes.

## Board
The board representing the planets is made up of 1m x 1m white wooden pieces that can be rearranged into different layouts. Each board has 3 connecting points at each of its 4 edges. These are the only points
on which a path can connect to another piece. This way, new maps can modularly and dynamically be constructed by simply shifting these puzzle pieces.
Please note that most of the rendering functions are calibrated to work with node names of length 6. The node rendering function of the tank internal map gui will cut off the node name if it is too many pixels wide.

## Mothership
Unlike the other actors, the mothership is not a physical agent on the board. It receives messages from and sends commands to its agents from afar.
The mothership is hosted on the main device running Planetnove, usually a PC or Laptop.
Though the game is based on the mothership 'triangulating' the robots new position after reaching a node, behind the scenes it actually knows the entire layout of the map from the start. The mothership simply
sends back information about the node connected to the path the tank robot last departed from.

#### Coms config
You need to create a file called 'coms_config.json' at put it at the root level of the repository. The file should contain the following:
```
{
  "mothership_ip": "<your-ip>",
  "mothership_port": 65432
}
```

## Tank
The tank explores the planet and communicates with the mothership. It is hosted on a raspberry pi 4 on the [Freenove Tank Robot](https://github.com/Freenove/Freenove_Tank_Robot_Kit_for_Raspberry_Pi). It's components include infrared sensors for line following,
an ultrasound sensor, a camera, LEDs and a crane arm for picking up objects.

Known issues:
- The ultrasound sensor is very low to the ground. I recommend ignoring all readings beyond 10cm and using a very flat surface as the spread of the ultrasound sensor's 'cone' of view will cause small uneven parts of the floor to be read as obstacles at further distances.

## Hexapod
The hexapod does not yet have an active role in Planetnove. It is hosted on raspberry pi 4 on the [Freenove Big Hexapod Robot](https://github.com/Freenove/Freenove_Big_Hexapod_Robot_Kit_for_Raspberry_Pi).

## Path blocking
Throughout the run, you can block paths using obstacles detectable by the tank's ultrasound sensors. If the tank encounters an obstacle, it will then have to turn around and notify the mothership of the blocked path. Once the path is considered blocked it will not be unblocked for the remainder of the run.

There are a few rules for blocking:
- An obstacle can only be places at positions where there is at least 20cm of (at least slightly) straight path between it and the nodes on either side.
- An obstacle can ignore this rule if it is placed directly on a node.

# Requirements

## Cairo
#### Linux
```
sudo apt-get install libcairo2-dev
```

#### Mac OS X 
```
sudo port install cairo
```

#### Windows
1. Install [MSYS2](https://github.com/msys2/msys2-installer?tab=readme-ov-file)
2. Inside the MSYS2 console, run the following commands:
- ``` 
  pacman -Syu
- ```
   pacman -S mingw-w64-x86_64-cairo
3. Add MSYS2 to PATH in environment variables (usually C:\msys64\mingw64\bin)
