import cv2
import numpy as np
from pyapriltags import Detector
import linear_equations as le

class Quadrant:
    def __init__(self, camera_index, quadrant_num, corner_tag_ids, files, ranks, missing_corner, distance_const=70):
        self.camera_index = camera_index
        self.quadrant_num = quadrant_num
        self.target_tag_ids = corner_tag_ids # Now expects 3 tags
        self.files = files
        self.ranks = ranks
        self.missing_corner = missing_corner
        self.distance_const = distance_const
        
        self.detector = Detector(families='tag36h11')
        self.cap = cv2.VideoCapture(self.camera_index)
        
        self.local_board_state = {}
        for f in self.files:
            for r in self.ranks:
                self.local_board_state[f"{f}{r}"] = None

    def calculate_missing_corner(self, pt1, pt2, pt3):
        """
        Given 3 corners of a rectangle, calculates the 4th (missing) corner.
        Assumes pt2 is the corner shared by the two edges.
        """
        # Vector math: 4th point = pt1 + pt3 - pt2
        x = pt1[0] + pt3[0] - pt2[0]
        y = pt1[1] + pt3[1] - pt2[1]
        return (int(x), int(y))

    def scan_sector(self):
        ret, frame = self.cap.read()
        if not ret:
            return self.local_board_state

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        adaptive_thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                                cv2.THRESH_BINARY, 11, 2)

        detections = self.detector.detect(adaptive_thresh)
        filtered_detections = [d for d in detections if d.tag_id in self.target_tag_ids]

        # Expecting exactly 3 tags to anchor the sector
        # Expecting exactly 3 tags to anchor the sector
        if len(filtered_detections) == 3:
            
            # Dictionary to map the detected tag IDs to their (x, y) center coordinates
            detected_points = {}
            for d in filtered_detections:
                detected_points[d.tag_id] = d.center 
            
            # Initialize the 4 main corners
            top_left = bottom_left = bottom_right = top_right = None

            # ---------------------------------------------------------
            # Quadrant 1: a1 to d4 (Missing: Top Right)
            # Array Order: [bottom_right, bottom_left, top_left]
            # ---------------------------------------------------------
            if self.quadrant_num == 1:
                bottom_right = detected_points[self.target_tag_ids[0]]
                bottom_left = detected_points[self.target_tag_ids[1]]
                top_left = detected_points[self.target_tag_ids[2]]
                
                # To find Top Right, Bottom Left is the diagonally opposite (shared) corner
                top_right = self.calculate_missing_corner(top_left, bottom_left, bottom_right)

            # ---------------------------------------------------------
            # Quadrant 2: e1 to h4 (Missing: Top Left)
            # Array Order: [bottom_left, bottom_right, top_right]
            # ---------------------------------------------------------
            elif self.quadrant_num == 2:
                bottom_left = detected_points[self.target_tag_ids[0]]
                bottom_right = detected_points[self.target_tag_ids[1]]
                top_right = detected_points[self.target_tag_ids[2]]
                
                # To find Top Left, Bottom Right is the diagonally opposite (shared) corner
                top_left = self.calculate_missing_corner(bottom_left, bottom_right, top_right)

            # ---------------------------------------------------------
            # Quadrant 3: a5 to d8 (Missing: Bottom Right)
            # Assumed Array Order: [bottom_left, top_left, top_right]
            # ---------------------------------------------------------
            elif self.quadrant_num == 3:
                bottom_left = detected_points[self.target_tag_ids[0]]
                top_left = detected_points[self.target_tag_ids[1]]
                top_right = detected_points[self.target_tag_ids[2]]
                
                # To find Bottom Right, Top Left is the diagonally opposite (shared) corner
                bottom_right = self.calculate_missing_corner(bottom_left, top_left, top_right)

            # ---------------------------------------------------------
            # Quadrant 4: e5 to h8 (Missing: Bottom Left)
            # Assumed Array Order: [bottom_right, top_right, top_left]
            # ---------------------------------------------------------
            elif self.quadrant_num == 4:
                bottom_right = detected_points[self.target_tag_ids[0]]
                top_right = detected_points[self.target_tag_ids[1]]
                top_left = detected_points[self.target_tag_ids[2]]
                
                # To find Bottom Left, Top Right is the diagonally opposite (shared) corner
                bottom_left = self.calculate_missing_corner(bottom_right, top_right, top_left)

            # --- Now that we have all 4 corners mathematically, generate the grid ---
            
            # Calculate midpoints (matching your logic from 2d_revamp.py)
            mid1_x = int((top_left[0] + top_right[0]) / 2)
            mid1_y = int((top_left[1] + top_right[1]) / 2)
            mid2_x = int((bottom_left[0] + bottom_right[0]) / 2)
            mid2_y = int((bottom_left[1] + bottom_right[1]) / 2)

            # Calculate left_bound and right_bound using your linear_equations logic
            left_bound, right_bound = draw_vertical_lines(
                frame, top_left, bottom_left, bottom_right, top_right, mid1_x, mid1_y, mid2_x, mid2_y
            )

            # Calculate the transformation matrix using the 4 points
            src_points = np.array([top_left, top_right, bottom_right, bottom_left], dtype=np.float32)
            
            # Create a perfect square destination matrix based on the distance_const 
            # (since a 4x4 grid is 4 squares wide and 4 squares tall)
            grid_size = self.distance_const * 4
            dst_points = np.array([
                [0, 0], 
                [grid_size, 0], 
                [grid_size, grid_size], 
                [0, grid_size]
            ], dtype=np.float32)

            matrix = cv2.getPerspectiveTransform(src_points, dst_points)

            # Identify the pieces using your existing function
            self.local_board_state = identify_apriltag_area(
                detections, self.target_tag_ids, frame, top_left, bottom_left, 
                bottom_right, top_right, left_bound, right_bound, matrix
            )

        return self.local_board_state

    def release_camera(self):
        self.cap.release()
