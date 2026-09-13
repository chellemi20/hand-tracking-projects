import cv2
import mediapipe as mp
import serial
import time
import math
import numpy as np
import random

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

# TouchDesigner Style Particle Class
class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-4, -1)  # Float upward like sand dust
        self.size = random.randint(1, 3)  # Fine micro particles
        self.life = random.randint(20, 50)
        self.alpha = random.randint(180, 255) # Silver / White sparkle

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1

# Particle Array Container
particles = []

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
            lm = hand_landmarks.landmark

            # 1. Spawn particles directly across ALL hand landmarks (TouchDesigner Simulation)
            for point in lm:
                px, py = int(point.x * w), int(point.y * h)
                # Spawn multiple fine dust particles per landmark
                if random.random() > 0.4:
                    particles.append(Particle(px + random.randint(-10, 10), py + random.randint(-10, 10)))

            # 2. Pinch Control Logic (Thumb tip: 4, Index tip: 8)
            thumb_tip = lm[4]
            index_tip = lm[8]

            x1, y1 = int(thumb_tip.x * w), int(thumb_tip.y * h)
            x2, y2 = int(index_tip.x * w), int(index_tip.y * h)
            mid_x, mid_y = (x1 + x2) // 2, (y1 + y2) // 2

            dist = calculate_distance(thumb_tip, index_tip)

            # Map distance (0.02 to 0.20) -> 0% to 100%
            brightness_pct = int(((dist - 0.02) / (0.20 - 0.02)) * 100)
            brightness_pct = max(0, min(100, brightness_pct))
            pwm_val = int((brightness_pct / 100.0) * 255)

            # Extra particle explosion intensity at the pinch center point
            extra_sparks = int((brightness_pct / 100.0) * 25)
            for _ in range(extra_sparks):
                particles.append(Particle(mid_x + random.randint(-15, 15), mid_y + random.randint(-15, 15)))

            # Pinch Connection Spark Line
            cv2.line(frame, (x1, y1), (x2, y2), (255, 255, 255), 2)
            cv2.circle(frame, (x1, y1), 5, (200, 200, 200), -1)
            cv2.circle(frame, (x2, y2), 5, (200, 200, 200), -1)

    # 3. Fast Particle Rendering Engine
    for p in particles[:]:
        p.update()
        if p.life <= 0:
            particles.remove(p)
        else:
            # Draw sparkling white/silver micro particles
            color = (p.alpha, p.alpha, p.alpha)
            cv2.circle(frame, (int(p.x), int(p.y)), p.size, color, -1)

    # Limit max particle count to preserve frame rate
    if len(particles) > 600:
        particles = particles[-600:]

    # Send PWM Signal to Arduino COM10
    if arduino:
        arduino.write(f"{pwm_val}\n".encode())

    # Minimalist Tech HUD Text Overlay
    cv2.putText(frame, f"PARTICLE INTENSITY: {brightness_pct}%", (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    cv2.imshow("TouchDesigner Particle Sim - Hardware Controller", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
if arduino:
    arduino.close()