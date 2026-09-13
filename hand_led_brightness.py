import cv2
import mediapipe as mp
import serial
import time
import math


try:
    arduino = serial.Serial('COM10', 9600, timeout=0.1)
    time.sleep(2)
    print("Arduino connected successfully on COM10!")
except Exception as e:
    print(f"Error connecting to Arduino: {e}")
    arduino = None


mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

cap = cv2.VideoCapture(0)

def calculate_distance(p1, p2):
    return math.hypot(p1.x - p2.x, p1.y - p2.y)

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
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            lm = hand_landmarks.landmark

            
            thumb_tip = lm[4]
            index_tip = lm[8]

            
            x1, y1 = int(thumb_tip.x * w), int(thumb_tip.y * h)
            x2, y2 = int(index_tip.x * w), int(index_tip.y * h)
            
           
            cv2.circle(frame, (x1, y1), 8, (255, 0, 0), cv2.FILLED)
            cv2.circle(frame, (x2, y2), 8, (255, 0, 0), cv2.FILLED)
            cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)

            
            dist = calculate_distance(thumb_tip, index_tip)

            
            brightness_pct = int(((dist - 0.02) / (0.20 - 0.02)) * 100)
            brightness_pct = max(0, min(100, brightness_pct))

           
            pwm_val = int((brightness_pct / 100.0) * 255)

   
    if arduino:
        arduino.write(f"{pwm_val}\n".encode())

    
    cv2.putText(frame, f"Brightness: {brightness_pct} %", (30, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 255), 3)

    cv2.imshow("Hand Distance Brightness Control", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
if arduino:
    arduino.close()