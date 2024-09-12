# Planetnove
A planet exploration sim using Freenove robots.

The tank robot explores the planet board using simple line following. Whenever it reaches a node, it starts communicating with the mothership. When it has decided what direction to depart in, it sends that information to the mothership and waits for confirmation. The mothership can then use its superior triangulation processing power to determine the next node the tank will arive at. Upon arrival the tank notifies the mothership and then receives a message with it's new position as well as the available paths from this
position. To keep the cost of communications low, the tank has to remember the map layout and make its own pathing decisions based on only these short messages.
Once the tank has explored the entire planet, i.e. has explored all paths of all nodes that it encountered, it informs the mothership.

There are a few additional cases that can happen:
- The mothership rejects the tank's request for departue in a direction. In that case the tank will need to choose another direction and send another request. (Note: The motherships rejection of a direction at a node is temporary. If the tank returns to the same node
later it can ask about taking that direction again.)
- The tank encounters an obstacle on the path. More information in the section on [Path blocking](#path-blocking).
- The tank is stuck and unable to finish exploring the planet. This can happen if all routes to unexplored nodes lead through paths that have been blocked or if the mothership rejects all departure directions that the tank could take to get to the unexplored nodes.
In that case, the tank informs the mothership that it is stuck and finishes.

## Board
The board representing the planets is made up of 1m x 1m white wooden pieces that can be rearranged into different layouts. Each board has 3 connecting joints at each of its 4 edges. These are the only points
on which a path can connect to another piece. This way, new maps can modularly and dynamically be constructed by simply shifting these puzzle pieces.

<div align="center"><img src="/docs/img/base_tile_joints.png" alt="Base tile with joint positions" width="250"></div>

As you can see, the joints have a specific local direction and number assigned to them. Each tile and its joints are first described in local directions. Later, when it has been rotated and connected to other tiles, these directions are converted to the global directions
of the planet (e.g. joint_N1 rotated becomes joint_E3 if the tile has been rotated 90 degrees clockwise).

All other tiles use this base tile to construct their paths and nodes. A node has to align with one of the joints both horizontally and vertically. If we treat the bottom corner of the tile as coordinate (0,0) and and give the joints coordinates corresponding to their number (e.g. joint_S1 = (0,1), joint_S3 = (0,3), joint_E3 = (3, 3), joint_N2 = (2, 3)) then a node can only have coordinates in the range ([1,3], [1,3]). Nodes are indicated to the line follower by a vertically and horizontally aligned cross of 2cm thick black tape. The cross should be
at least 6cm wide and tall so that the three infrared sensors of the tank robot all read it at the same time.
A path is 2cm thick and can only ever connect two end points, i.e. it needs one specific start and one specific end. No branching paths. These end points can either be nodes or joints. A path can also connect to the same node at a different direction or the same direction.

Provided with the repository are the following four example tiles:
<div align="center"><img src="/docs/img/example_tiles.png" alt="Example tiles" width="500"></div>

To create new tiles, the files tile_\<id>.json, tile_\<id>.svd and tile_\<id>_blank.svg need to be created and placed into /planets/data and /planets/svg respectively. 
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
  "mothership_ip": "your-ip>",
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
Throughout the run, you can block paths using obstacles detectable by the tank's ultrasound sensors. If the tank encounters an obstacle, it will then have to turn around and notify the mothership of the blocked path. 
*After* the mothership has confirmed receiving the blocked path message, the tank can send a new arrival message for the node it just returned to from the blocked path. 
Once a path is considered blocked it can not be unblocked for the remainder of the run.

There are a few rules for blocking:
- An obstacle can only be places at positions where there is at least 20cm of (at least slightly) straight path between it and the nodes on either side.
- An obstacle can ignore the distance rule if it is placed directly on a node.


<img src="/docs/img/blocking_examples.png" alt="Blocking examples" width="1700">

# Requirements
The tank and mothership have different requirements. You can run init_<entity>.py without having the requirements for the other entities. 
The requirements are specified in 'requirements.txt' within the entity's source folder.
The following subsections concern requirements with extra steps beyond pip install.

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
