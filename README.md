# Planetnove
A planet exploration sim making use of Freenove robots.

The tank robot explores the planet board using line following. Whenever it reaches a node, it starts communicating with the mothership. When it has decided what direction to depart in, it sends that information to the mothership and waits for confirmation. The mothership can then use its superior triangulation processing power to determine the next node that the tank will arrive at. Upon arrival, the tank notifies the mothership and then receives a message with its new position as well as the available paths from that node. To keep the cost of communications low, the tank has to remember the map layout and make its own pathing decisions based on only these short messages.
Once the tank has explored the entire planet, i.e., has explored all available paths of all nodes that it encountered, it informs the mothership.

There are a few additional cases that can occur:
- The mothership rejects the tank's request for departure in a direction. In that case, the tank will need to choose another direction and send another request. (Note: The mothership's rejection of a direction at a node is temporary. If the tank returns to the same node later, it can ask about taking that direction again.)
- The tank encounters an obstacle on the path. More information in the section on [path blocking](#path-blocking).
- The tank is stuck and unable to finish exploring the planet. This can happen if all routes to unexplored nodes lead through paths that have been blocked or if the mothership rejects all departure directions that the tank could take to get to the unexplored nodes.
In that case, the tank informs the mothership that it is stuck and finishes.

## Board
The board representing the planet is made up of white pieces (tiles) sized 1m x 1m that can be rearranged into different layouts. Each tile has three connecting joints at each of its four edges. These are the only points
at which a path can connect to another tile. This way, new maps can be constructed modularly and dynamically by simply shifting and rotating the pieces. The corresponding [GUI](#gui) allows for easy synchronization of the digital and physical tile layouts. 

<div align="center"><img src="/docs/img/base_tile_joints.png" alt="Base tile with joint positions" width="250"></div>

The joints have a specific local direction and number assigned to them. Internally, each tile and its joints are initially described in local directions only. Later, after rotation and connection to other tiles, the GUI converts these directions to the global directions
of the now arranged planet (e.g., joint_N1 becomes joint_E3 if the tile has been rotated 90 degrees clockwise).

All other tiles use this base tile to construct their paths and nodes. A node has to align with one of the joints both horizontally and vertically. Let the bottom corner of the tile be the coordinate (0,0) and assign the joints coordinates corresponding to their number (e.g., joint_S1 = (0,1), joint_S3 = (0,3), joint_E3 = (3, 3), joint_N2 = (2, 3)), then a node can only have coordinates in the range ([1,3], [1,3]). 

A path is 2cm wide and can only ever connect two end points, i.e., it needs one specific start and one specific end. No branching paths. On individual tiles, these endpoints can either be nodes or joints. On the finished planet board, a path can only connect two nodes (multiple tile joints in between are allowed as long as the final end points are nodes). Any paths that do not match this criteria are discarded.
A path can also connect to the same node in a different direction or the same direction (loopback paths).

Nodes are marked by a vertically and horizontally aligned cross of tape. The cross should be
at least 8cm wide both horizontally and vertically (3cm beyond the 2cm tape on each side) so that the three infrared sensors of the tank robot all read it at the same time.

Provided with the repository are the following example tiles:
<div align="center"><img src="/docs/img/example_tiles.png" alt="Example tiles" width="500"></div>

To create new tiles, the files tile_\<id>.json, tile_\<id>.svg and tile_\<id>_blank.svg need to be created and placed into ```/planets/data``` and ```/planets/svg``` respectively. Only the former has an actual impact on sim logic, with the latter only providing a visual representation.
Besides the given [examples](/planets/data/), which are relatively simple and should be easy to understand without additional documentation, the corresponding [loader](/mothership/io/tile_loader.py) and [storage class](/planets/code/tiles/tile_data.py) also output detailed errors to make to process of creating new tiles easier for beginners.
Please note that most of the rendering functions are calibrated to work with node names of length 6. Node names may be cut off if they extend too far beyond this length.

## Mothership
Unlike the tank robot, the mothership is not a physical agent on the board. It receives messages from and sends commands to its agents from afar.
The mothership is hosted on the main device running Planetnove, usually a PC or Laptop.
Though the game is based on the mothership 'triangulating' the robot's new position after reaching a node, behind the scenes it actually knows the entire layout of the map from the start. The mothership simply
sends information about the node connected to the path that the tank robot last departed from.

#### GUI
The mothership GUI can be used to handle communications with other actors and to edit the planet. In the planet view window, planet tiles can be dragged and dropped, rotated by pressing 'r' while holding the tile, and attached to each other by dropping them near other tiles.
A selected tile can be deactivated/reactivated by pressing 'd'. Deactivated tiles are no longer 'in play', which means the planet can be finished without attaching them.
Once all tiles are snapped into place, the main GUI will enable the 'Finish planet' button. Once the planet is finished, all tiles are locked and cannot be moved until the 'Edit' button is pressed. While the planet is finished, the name of the starting node and the direction of the path from which the tank will arrive need to be set. The tank's facing direction and location are tracked based on these parameters.

Afterward, the IP address of the tank can be entered at the 'Communications' window. Pressing the 'Add tank' button initiates the connection. If it succeeds, everything is ready. A button will appear in the same window that allows sending a start message, which begins the sim.

This will begin the loop of the tank traveling to the next node, stopping to communicate, receiving information from the mothership, and heading off to the next node.

The GUI also displays the current state of the tank's internal map. That is, what nodes, paths, and path blockages the tank is currently aware of and which routes it intends to follow. The current node is red while the target node and the route towards it (if they exist) are blue. All other nodes and paths are green and white respectively.
Every time the tank updates its internal map it sends the updated state to the mothership. Yes, this goes against the idea of 'keeping the cost of communications low' that was stated in the sim's description, but I consider this to be a 'behind the scenes' communication that only exists for a better viewing experience for the operator of the mothership.

#### Coms config
To configure communications for entities that do not have a GUI (i.e., the tank) you need to create a file called 'coms_config.json' and put it at the root level of the repository. The file should contain the following:
```
{
  "mothership_ip": "<host-ip>",
  "mothership_port": 65432
}
```

## Tank
The tank explores the planet and communicates with the mothership. It is hosted on a raspberry pi 4 on the [Freenove Tank Robot](https://github.com/Freenove/Freenove_Tank_Robot_Kit_for_Raspberry_Pi). Planetnove does not make use of its crane arm. Instead, it is recommended to use that space to mount the ultrasound sensor higher above the floor to avoid picking up small but passable bumps as obstacles.

<img src="/docs/img/tank.jpeg" alt="Tank example" width="250">

#### Physical components
- Ultrasound sensor for detecting obstacles ahead
- Three on-off infrared sensors at the bottom to allow for bit-mapped line following
- Tank motors for movement
- A set of four LEDs in square arrangement for signaling information outside of the console:
    - **Client connected**: Turns all LEDs green at once when the tank client has connected to the mothership.
    - **Exploration finished**: A smooth rainbow animation.
    - **Direction indicator**: Before departure, the tank indicates the global directions relative to its own orientation by turning on its LEDs with the following color correspondence: *{north: red, east: green, south: blue, west: yellow}*
    - **Turn animation**: Flashes 3 LEDs in series from the front toward the direction the tank is going to turn.
    - **Node departure**: Flashes the 2 LEDs in the back and then the 2 LEDs in the front to indicate forward movement. The color is either white for normal exploration, blue for backtracking, or orange for the final backtrack step.
    - **Obstacle animation**: Flashes the two front LEDs red twice and then plays the 180-degree turn animation in red.

## Hexapod
The hexapod does not yet have an active role in Planetnove. It is hosted on raspberry pi 4 on the [Freenove Big Hexapod Robot](https://github.com/Freenove/Freenove_Big_Hexapod_Robot_Kit_for_Raspberry_Pi).

## Path blocking
Throughout the run, you can block paths using obstacles detectable by the tank's ultrasound sensors. If the tank encounters an obstacle, it will then have to turn around and notify the mothership of the blocked path. 
*After* the mothership has confirmed receiving the blocked path message, the tank can send a new arrival message for the node it just returned to from the blocked path. 
Once a path is considered blocked it cannot be unblocked for the remainder of the run.

There are a few rules for blocking:
- An obstacle can only be places at positions where there is at least 30cm of mostly straight path between it and the nodes on either side. This is to give the tank enough room to turn around.
- An obstacle can ignore the distance rule if it is placed directly on a node.
- An obstacle cannot occur before the tank encounters its first node.


<img src="/docs/img/blocking_examples.png" alt="Blocking examples" width="1700">

# Software

## Architecture
The following diagram displays a fundamental overview of the software architecture of Planetnove, divided into the 'util', 'mothership', 'tank', and 'planets' packages.
It is important to note that a lot of smaller classes and relations were left out for clarity. What can be seen here is only
a selection of the most relevant information needed to gain an understanding of how the system works.
![Software architecture diagram](/docs/img/architecture_diagram.svg)



## Requirements
The tank and mothership have different requirements. You can run ```init_<entity>.py``` without having the requirements for the other entities. 
The requirements are specified in 'requirements.txt' within the entity's source folder.
The following subsections concern requirements with extra steps beyond pip install.

#### Cairo Windows
On Windows, cairo needs to be installed separately.
1. Install [MSYS2](https://github.com/msys2/msys2-installer?tab=readme-ov-file)
2. Inside the MSYS2 console, run the following commands:
- ``` 
  pacman -Syu
- ```
  pacman -S mingw-w64-x86_64-cairo
3. Add MSYS2 to PATH in environment variables (usually C:\msys64\mingw64\bin)
4. (If you already have another python-pip installation and do not want it to be overwritten, remove the python executable from msys64\mingw64\bin)
