import math

COUNTS_PER_SQUARE = 10500
PASSWORD = bytearray([ord('W'), ord('I'), ord('Z')])

class Robot():

    def __init__(self, id, position, angle, server, device_id):
        self.id = id
        self.position = position
        self.server = server
        self.device_id = device_id

        # Angle is measured counterclockwise from horizontal
        self.angle = angle
        self.initial_angle = angle

        self.buffer = bytearray()

    def __repr__(self):
        return self.id
    
    # ALL COMMANDS ONLY ADD MOVEMENT TO BUFFER, BUT STILL AFFECT ROBOT POSITION VALUES BEFORE BUFFER IS SENT / MOVEMENT IS MADE. 
    # send_buffer() MUST BE USED FOR COMMAND TO BE SENT TO ROBOT
    # THIS MEANS Robot.position DOES NOT REFLECT ACTUAL POSITION OF ROBOT, THIS NEEDS TO BE DERIVED FROM COMPUTER VISION.

    def send_buffer(self):
        if self.server:
            self.server.send_command(self.device_id, PASSWORD + self.buffer + bytearray([3]))
        self.buffer = bytearray()
        
    def move(self, distance):
        encoder_counts = distance * COUNTS_PER_SQUARE / 100
        command = bytearray([1, 0]) + bytearray(int(encoder_counts).to_bytes(2, byteorder="big"))
        print(command)
        self.buffer += command
    
    def turn(self, angle):
        if angle == 0:
            return
        
        command_angle = int(angle if angle > 0 else -angle)
        command = bytearray([2, 0 if angle > 0 else 1]) + bytearray(command_angle.to_bytes(1, byteorder="big")) + bytearray([0])
        print(command)
        self.buffer += command
        self.angle += angle
        self.angle = self.angle % 360

    def turn_to(self, angle):
        angle = angle % 360
        turn_angle = angle - self.angle
        if turn_angle > 180:
            turn_angle = -360 + turn_angle
        elif turn_angle < -180:
            turn_angle = 360 + turn_angle
        
        self.turn(turn_angle)

    # NEW: Send Holonomic movement vector to Pico
    def move_holonomic(self, angle, distance):
        # Calculate encoder counts
        encoder_counts = distance * COUNTS_PER_SQUARE / 100
        
        # Ensure angle is positive 0-360
        command_angle = int(angle % 360)
        
        # Command format: [5, angle_high_byte, angle_low_byte, distance_scaled_byte]
        angle_bytes = command_angle.to_bytes(2, byteorder="big")
        dist_byte = bytearray([min(255, int(encoder_counts / 100))])
        
        command = bytearray([5]) + bytearray(angle_bytes) + dist_byte
        print(f"Holonomic Command: {command}")
        self.buffer += command

    # UPDATED: Directs the robot without physical rotation
    def move_to(self, position):
        dx = position[0] - self.position[0]
        dy = position[1] - self.position[1]
        
        distance = math.dist(self.position, position)
        
        # Determine angle based on X/Y difference 
        move_angle = math.degrees(math.atan2(dy, dx))
        
        # No longer turning! Just gliding omnidirectionally
        self.move_holonomic(move_angle, distance)
        
        self.position = position

    def face_forward(self):
        # Still useful if the robot gets bumped or you want to add a spin attack later
        self.turn_to(self.initial_angle)

    def execute_path(self, path_points):
        print(f'Moving: {self.id} from {self.position} to {path_points[-1]}')
        for point in path_points:
            self.move_to(point)
            print(self.position)
            print(f"Moved to {point}")
        
        print(self.position)
        print("Finished Path")
