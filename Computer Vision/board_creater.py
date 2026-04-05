import quadrant as qt

def main():
    # Define the 3 corner tags for EACH camera. (12 tags total)
    # The arrays map to the specific corners mentioned in quadrants.txt
    
    # Quadrant 1: a1 to d4 -> [bottom_right, bottom_left, top_left]
    q1_anchors = [10, 11, 12] 
    
    # Quadrant 2: e1 to h4 -> [bottom_left, bottom_right, top_right]
    q2_anchors = [20, 21, 22]
    
    # Quadrant 3: a5 to d8 -> (Inferring the missing text) [bottom_right, top_right, top_left]
    q3_anchors = [30, 31, 32]
    
    # Quadrant 4: e5 to h8 -> (Inferring the missing text) [bottom_left, top_left, top_right]
    q4_anchors = [40, 41, 42]

    print("Initializing Quadrant Cameras Handler...")
    
    # Quadrant 1 (Camera 0)
    quadrant_one = qt.Quadrant(camera_index=0, quadrant_num=1, corner_tag_ids=q1_anchors,
                               files=['a', 'b', 'c', 'd'], ranks=[1, 2, 3, 4], 
                               missing_corner="top_right")
    
    # Quadrant 2 (Camera 1)
    quadrant_two = qt.Quadrant(camera_index=1, quadrant_num=2, corner_tag_ids=q2_anchors,
                               files=['e', 'f', 'g', 'h'], ranks=[1, 2, 3, 4],
                               missing_corner="top_left")
    
    # Quadrant 3 (Camera 2)
    quadrant_three = qt.Quadrant(camera_index=2, quadrant_num=3, corner_tag_ids=q3_anchors,
                                 files=['a', 'b', 'c', 'd'], ranks=[5, 6, 7, 8],
                                 missing_corner="bottom_left")
    
    # Quadrant 4 (Camera 3)
    quadrant_four = qt.Quadrant(camera_index=3, quadrant_num=4, corner_tag_ids=q4_anchors,
                                files=['e', 'f', 'g', 'h'], ranks=[5, 6, 7, 8],
                                missing_corner="bottom_right")

    all_quadrants = [quadrant_one, quadrant_two, quadrant_three, quadrant_four]

    try:
        while True:
            master_board_state = {}
            
            # Query each camera for its 4x4 sector data
            for quad in all_quadrants:
                sector_data = quad.scan_sector()
                master_board_state.update(sector_data)
            
            # master_board_state now accurately holds a1 through h8
            
    except KeyboardInterrupt:
        print("Shutting down vision system...")
    finally:
        for quad in all_quadrants:
            quad.release_camera()

if __name__ == "__main__":
    main()
