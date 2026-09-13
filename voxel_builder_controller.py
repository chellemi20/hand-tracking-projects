import cv2
import mediapipe as mp
import serial
import time
import math
import numpy as np

# --- SERIAL SETUP ---
try:
    arduino = serial.Serial('COM10', 9600, timeout=0.1)
    time.sleep(2)
    print("Arduino connected successfully on COM10!")
except Exception as e:
    print(f"Error connecting to Arduino: {e}")
    arduino = None

# --- MEDIAPIPE SETUP ---
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

cap = cv2.VideoCapture(0)

def draw_3d_cube(img, center, size, color):
    """Gumuhit ng Wireframe 3D Voxel Cube sa 2D Frame"""
    cx, cy = center
    s = size // 2

    # Isometric/3D Projection Vertices (Front & Back faces)
    offset = int(s * 0.5)
    
    # Front Face Vertices
    f_tl = (cx - s, cy - s)
    f_tr = (cx + s, cy - s)
    f_br = (cx + s, cy + s)
    f_bl = (cx - s, cy + s)

    # Back Face Vertices (Shifted up and right for 3D depth)
    b_tl = (cx - s + offset, cy - s - offset)
    b_tr = (cx + s + offset, cy - s - offset)
    b_br = (cx + s + offset, cy + s - offset)
    b_bl = (cx - s + offset, cy + s - offset)

    # Draw Front Face
    pts_front = np.array([f_tl, f_tr, f_br, f_bl], np.int32)
    cv2.polylines(img, [pts_front], True, color, 2)

    # Draw Back Face
    pts_back = np.array([b_tl, b_tr, b_br, b_bl], np.int32)
    cv2.polylines(img, [pts_back], True, (150, 150, 150), 1)

    # Connecting Edges (Front to Back)
    cv2.line(img, f_tl, b_tl, color, 1)
    cv2.line(img, f_tr, b_tr, color, 1)
    cv2.line(img, f_br, b_br, color, 1)
    cv2.line(img, f_bl, b_bl, color, 1)

def calculate_distance(p1, p2):
    return math.hypot(p1.x - p2.x, p1.y - p2.y)

# Store persistent Voxels on screen
placed_voxels = []

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    brightness_pct = 0
    pwm_val = 0

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            lm = hand_landmarks.landmark

            # Landmark Points: Thumb Tip (4) and Index Tip (8)
            thumb_tip = lm[4]
            index_tip = lm[8]

            x1, y1 = int(thumb_tip.x * w), int(thumb_tip.y * h)
            x2, y2 = int(index_tip.x * w), int(index_tip.y * h)
            mid_x, mid_y = (x1 + x2) // 2, (y1 + y2) // 2

            dist = calculate_distance(thumb_tip, index_tip)

            # Map distance to percentage (0% to 100%)
            brightness_pct = int(((dist - 0.02) / (0.20 - 0.02)) * 100)
            brightness_pct = max(0, min(100, brightness_pct))
            pwm_val = int((brightness_pct / 100.0) * 255)

            # Dynamic Voxel Size based on Pinch Width
            voxel_size = int(20 + (brightness_pct / 100.0) * 80)

            # Active Glowing Voxel at Pinch Cursor Position
            draw_3d_cube(frame, (mid_x, mid_y), voxel_size, (255, 255, 255))
            cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)

            # Automatic Voxel Placement Trail
            if brightness_pct > 10 and len(placed_voxels) < 30:
                placed_voxels.append(((mid_x, mid_y), voxel_size, (255, 200, 0)))

    # Render Placed Voxel Cubes (Visual Stack Buffer)
    for pos, size, color in placed_voxels:
        draw_3d_cube(frame, pos, size, color)

    # Keep maximum 25 voxels on screen to avoid clutter
    if len(placed_voxels) > 25:
        placed_voxels.pop(0)

    # Send PWM intensity to Arduino COM10
    if arduino:
        arduino.write(f"{pwm_val}\n".encode())

    # Futuristic Voxel Builder HUD Display
    cv2.rectangle(frame, (20, 20), (360, 90), (15, 15, 15), -1)
    cv2.rectangle(frame, (20, 20), (360, 90), (0, 255, 255), 1)
    cv2.putText(frame, "3D VOXEL ENGINE", (30, 48),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    cv2.putText(frame, f"BUILD SCALE / PWM: {brightness_pct}%", (30, 78),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    cv2.imshow("3D Voxel Builder & Hardware Control", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
if arduino:
    arduino.close()