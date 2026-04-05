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
        if len(filtered_detections) == 3:
            
            # Dictionary to map the detected tags to their coordinates
            detected_points = {}
            for d in filtered_detections:
                detected_points[d.tag_id] = d.center 
            
            # TODO: Assign pt1, pt2, pt3 based on your specific target_tag_ids array
            # and calculate the missing corner so you have all 4 points. 
            # Example (if pt2 is the shared corner):
            # missing_pt = self.calculate_missing_corner(pt1, pt2, pt3)
            
            # Now that you mathematically have 4 corners, you can run the standard
            # cv2.perspectiveTransform and grid logic from 2d_revamp.py!
            pass
            
        else:
            cv2.putText(frame, f"Q{self.quadrant_num} Anchor Tags Missing!", (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        return self.local_board_state

    def release_camera(self):
        self.cap.release()
