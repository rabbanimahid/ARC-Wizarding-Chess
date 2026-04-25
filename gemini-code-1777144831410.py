import pygame
import socket
import struct
import math

# --- CONFIGURATION ---
ESP_IP = "192.168.1.XXX" # CHANGE THIS to your ESP-01S's IP address!
UDP_PORT = 12345

# Set up UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Initialize Pygame and Joystick
pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    print("No Xbox controller detected! Please plug one in.")
    exit()

controller = pygame.joystick.Joystick(0)
controller.init()
print(f"Connected to: {controller.get_name()}")

def send_motor_command(m1_speed, m2_speed, m3_speed):
    # Determine directions (1 for forward, 0 for reverse)
    d1 = 1 if m1_speed >= 0 else 0
    d2 = 1 if m2_speed >= 0 else 0
    d3 = 1 if m3_speed >= 0 else 0

    # Convert speeds to absolute bytes (0-255)
    s1 = min(255, int(abs(m1_speed) * 255))
    s2 = min(255, int(abs(m2_speed) * 255))
    s3 = min(255, int(abs(m3_speed) * 255))

    # Packet Format: 'W', 'I', 'Z', Dir1, Spd1, Dir2, Spd2, Dir3, Spd3
    packet = struct.pack('3sBBBBBB', b'WIZ', d1, s1, d2, s2, d3, s3)
    sock.sendto(packet, (ESP_IP, UDP_PORT))

print("Ready to drive! Press CTRL+C to quit.")

try:
    while True:
        pygame.event.pump() # Update controller state

        # Read Left Stick (X/Y Translation) and Right Stick X (Rotation)
        # Note: Pygame joysticks return values from -1.0 to 1.0
        joy_x = controller.get_axis(0) 
        joy_y = controller.get_axis(1) * -1 # Invert Y so up is positive
        joy_z = controller.get_axis(3) # Right stick horizontal for spin

        # Add a small deadzone to stop stick drift
        if abs(joy_x) < 0.1: joy_x = 0
        if abs(joy_y) < 0.1: joy_y = 0
        if abs(joy_z) < 0.1: joy_z = 0

        # --- KIWI DRIVE KINEMATICS MATRIX ---
        # Assuming wheels are placed at 150 deg, 30 deg, and 270 deg
        m1 = -0.5 * joy_x - (math.sqrt(3)/2) * joy_y + joy_z
        m2 = -0.5 * joy_x + (math.sqrt(3)/2) * joy_y + joy_z
        m3 = joy_x + joy_z

        # Normalize the speeds so we don't exceed 1.0 (100% PWM)
        max_val = max(abs(m1), abs(m2), abs(m3), 1.0)
        m1 /= max_val
        m2 /= max_val
        m3 /= max_val

        send_motor_command(m1, m2, m3)
        pygame.time.wait(50) # Send commands at 20Hz

except KeyboardInterrupt:
    print("Stopping...")
    send_motor_command(0, 0, 0) # Send a final stop command
    pygame.quit()