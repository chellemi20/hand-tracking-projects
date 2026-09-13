import cv2
import mediapipe as mp
import serial
import time


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

tip_ids = [4, 8, 12, 16, 20]

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame from camera")
        break

   
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    finger_states = [0, 0, 0, 0, 0]

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            lm_list = hand_landmarks.landmark

           
            if lm_list[tip_ids[0]].x < lm_list[tip_ids[0] - 1].x:
                finger_states[0] = 1
            else:
                finger_states[0] = 0

         
            for i in range(1, 5):
                if lm_list[tip_ids[i]].y < lm_list[tip_ids[i] - 2].y:
                    finger_states[i] = 1
                else:
                    finger_states[i] = 0

    
    data_string = "".join(map(str, finger_states))

    
    if arduino:
        arduino.write(f"{data_string}\n".encode())

   
    total_fingers = sum(finger_states)
    cv2.putText(frame, f"FINGERS: {total_fingers}", (20, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(frame, f"STATE: {data_string}", (20, 90),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    cv2.imshow("Hand Tracking LED Controller", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
if arduino:
    arduino.close()