import cv2
import mediapipe as mp
import math
import requests
import time

ESP_IP = "http://10.223.235.1"  # replace with your ESP IP

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(model_complexity=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

mode = "LED"
last_action_time = 0
toggle_mode_triggered = False
servo_angle = 0

def find_distance(p1, p2):
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])

# LED states (to prevent repeat requests)
led_states = [0, 0, 0, 0, 0]

while True:
    success, img = cap.read()
    if not success:
        continue

    img = cv2.flip(img, 1)
    imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(imgRGB)

    current_time = time.time()

    if results.multi_hand_landmarks:
        for handLms in results.multi_hand_landmarks:
            lmList = []
            h, w, c = img.shape

            for id, lm in enumerate(handLms.landmark):
                cx, cy = int(lm.x * w), int(lm.y * h)
                lmList.append((cx, cy))

            if lmList:
                # Finger detection
                thumb = 1 if lmList[4][1] < lmList[2][1] else 0
                index = 1 if lmList[8][1] < lmList[6][1] else 0
                middle = 1 if lmList[12][1] < lmList[10][1] else 0
                ring = 1 if lmList[16][1] < lmList[14][1] else 0
                pinky = 1 if lmList[20][1] < lmList[18][1] else 0

                # 👉 RESET (Thumb + Pinky)
                if thumb == 1 and pinky == 1 and index == 0 and middle == 0 and ring == 0:
                    if current_time - last_action_time > 1:
                        try:
                            requests.get(f"{ESP_IP}/alloff")
                        except:
                            pass
                        led_states = [0, 0, 0, 0, 0]
                        last_action_time = current_time
                    continue

                # 👉 TOGGLE (Index + Pinky)
                if index == 1 and pinky == 1 and middle == 0 and ring == 0:
                    if not toggle_mode_triggered and current_time - last_action_time > 1:
                        mode = "SERVO" if mode == "LED" else "LED"
                        toggle_mode_triggered = True
                        last_action_time = current_time
                        print("Mode:", mode)
                    continue
                else:
                    toggle_mode_triggered = False

                # 👉 LED MODE (FINAL CORRECT)
                if mode == "LED":
                    try:
                        if current_time - last_action_time > 0.5:

                            # LED1 → index
                            if index == 1 and middle == 0 and ring == 0 and pinky == 0:
                                if led_states[0] == 0:
                                    led_states[0] = 1
                                    requests.get(f"{ESP_IP}/led1?state=1")

                            # LED2 → index + middle
                            elif index == 1 and middle == 1 and ring == 0 and pinky == 0:
                                if led_states[1] == 0:
                                    led_states[1] = 1
                                    requests.get(f"{ESP_IP}/led2?state=1")

                            # LED3 → index + middle + ring
                            elif index == 1 and middle == 1 and ring == 1 and pinky == 0:
                                if led_states[2] == 0:
                                    led_states[2] = 1
                                    requests.get(f"{ESP_IP}/led3?state=1")

                            # LED4 → index + middle + ring + pinky
                            elif index == 1 and middle == 1 and ring == 1 and pinky == 1 and thumb == 0:
                                if led_states[3] == 0:
                                    led_states[3] = 1
                                    requests.get(f"{ESP_IP}/led4?state=1")

                            # LED5 → all fingers
                            elif index == 1 and middle == 1 and ring == 1 and pinky == 1 and thumb == 1:
                                if led_states[4] == 0:
                                    led_states[4] = 1
                                    requests.get(f"{ESP_IP}/led5?state=1")

                            last_action_time = current_time

                    except:
                        pass

                # 👉 SERVO MODE (UNCHANGED)
                elif mode == "SERVO":
                    x1, y1 = lmList[4]
                    x2, y2 = lmList[8]

                    distance = find_distance((x1, y1), (x2, y2))
                    angle = int((distance / 200) * 180)
                    angle = max(0, min(angle, 180))

                    servo_angle = angle

                    try:
                        requests.get(f"{ESP_IP}/servo?angle={angle}")
                    except:
                        pass

            mp_draw.draw_landmarks(img, handLms, mp_hands.HAND_CONNECTIONS)

    # 👉 Display
    cv2.putText(img, f"Mode: {mode}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    if mode == "SERVO":
        cv2.putText(img, f"Servo Angle: {servo_angle}", (10, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    cv2.imshow("Gesture Control", img)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()