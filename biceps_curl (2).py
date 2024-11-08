import cv2
import mediapipe as mp
import pyttsx3
import pygame
import math
import queue
import threading
import tkinter as tk
from playsound import playsound

pygame.mixer.init()

# Video capture setup
cap = cv2.VideoCapture(0)
cap.set(3, 1280)
cap.set(4, 720)

# MediaPipe setup
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

# Initialize counts and states
left_count = 0
right_count = 0
left_arm_flexed = False
right_arm_flexed = False
left_moving_up = False
right_moving_up = False

# Audio setup
buzzer = r"C:\Users\nupur bhatkhande\Desktop\buzzer.mp3"
welcome = r"C:\Users\nupur bhatkhande\Desktop\welcome.mp3"
motivational_music = r"C:\Users\nupur bhatkhande\Desktop\guide.mp3"
engine = pyttsx3.init()
update_queue = queue.Queue()

# Music flags
music_playing = False
buzzer_played_flag = False

def calculate_angle(point1, point2, point3):
    """Calculates the angle between three points."""
    angle_radians = math.atan2(point3[1] - point2[1], point3[0] - point2[0]) - math.atan2(point1[1] - point2[1], point1[0] - point2[0])
    angle_degrees = math.degrees(angle_radians)
    return abs(angle_degrees)

def play_buzzer_once():
    global buzzer_played_flag
    if not buzzer_played_flag:
        playsound(buzzer)
        buzzer_played_flag = True

def voice_coaching_bicep_curl_count():
    global left_count, right_count
    while True:
        try:
            new_counts = update_queue.get()
            if new_counts is not None:
                side, count = new_counts
                if side == "left":
                    engine.say(f"Bicep Left {count}")
                elif side == "right":
                    engine.say(f"Bicep Right {count}")
                engine.runAndWait()
        except queue.Empty:
            pass

def play_welcome_sound():
    playsound(welcome)

def play_motivational_music():
    global music_playing
    if not music_playing:
        pygame.mixer.music.load(motivational_music)
        pygame.mixer.music.play(0)
        music_playing = True

def stop_motivational_music():
    global music_playing
    if music_playing:
        pygame.mixer.music.stop()
        music_playing = False

def update_target_count():
    global target_count
    new_target = target_entry.get()
    try:
        new_target = int(new_target)
        if new_target >= 0:
            target_count.set(new_target)
            if not music_playing:
                play_motivational_music()
    except ValueError:
        print("Please enter a valid number.")

def run_gui():
    global target_entry, target_count
    root = tk.Tk()
    root.title("Bicep Curl Counter")
    root.geometry("400x200")
    root.configure(bg="#f0f0f0")

    frame = tk.Frame(root, bg="#ffffff", padx=20, pady=20)
    frame.pack(expand=True, fill="both")

    label = tk.Label(frame, text="Set Your Bicep Curl Target", font=("Helvetica", 14), bg="#ffffff")
    label.pack()

    target_entry = tk.Entry(frame, font=("Helvetica", 12))
    target_entry.insert(0, "10")  # Default target count
    target_entry.pack()

    set_button = tk.Button(frame, text="Set Target", command=update_target_count, bg="#007acc", fg="#ffffff", font=("Helvetica", 12))
    set_button.pack()

    target_count = tk.StringVar(value="")
    target_label = tk.Label(frame, textvariable=target_count, font=("Helvetica", 12), bg="#ffffff")
    target_label.pack()

    root.mainloop()

# Start GUI and voice coaching threads
gui_thread = threading.Thread(target=run_gui)
gui_thread.start()

voice_coaching_thread = threading.Thread(target=voice_coaching_bicep_curl_count)
voice_coaching_thread.daemon = True
voice_coaching_thread.start()

play_welcome_sound()

def draw_progress_bar(image, progress, width=400, height=30, x=50, y=50):
    """Draw a progress bar on the screen."""
    cv2.rectangle(image, (x, y), (x + width, y + height), (0, 0, 0), -1)  # Background
    cv2.rectangle(image, (x, y), (x + int(progress * width), y + height), (0, 255, 0), -1)  # Progress

with mp_pose.Pose(min_detection_confidence=0.7, min_tracking_confidence=0.7) as pose:
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            print("Empty camera")
            break

        result = pose.process(image)

        if result.pose_landmarks:
            mp_drawing.draw_landmarks(image, result.pose_landmarks, mp_pose.POSE_CONNECTIONS)

            # Get landmark positions
            left_wrist = result.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_WRIST]
            left_elbow = result.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_ELBOW]
            left_shoulder = result.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER]

            right_wrist = result.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_WRIST]
            right_elbow = result.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_ELBOW]
            right_shoulder = result.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER]

            # Calculate angles for left and right arms
            left_elbow_angle = calculate_angle(
                [left_shoulder.x, left_shoulder.y],
                [left_elbow.x, left_elbow.y],
                [left_wrist.x, left_wrist.y]
            )
            right_elbow_angle = calculate_angle(
                [right_shoulder.x, right_shoulder.y],
                [right_elbow.x, right_elbow.y],
                [right_wrist.x, right_wrist.y]
            )

            # Left arm curl detection
            if left_elbow_angle < 90 and not left_arm_flexed:
                left_moving_up = True
                left_arm_flexed = True
            elif left_elbow_angle > 160 and left_arm_flexed and left_moving_up:
                left_count += 1
                print(f"Bicep Curl Count (Left Arm): {left_count}")
                update_queue.put(("left", left_count))
                left_arm_flexed = False
                left_moving_up = False

            # Right arm curl detection
            if right_elbow_angle < 90 and not right_arm_flexed:
                right_moving_up = True
                right_arm_flexed = True
            elif right_elbow_angle > 160 and right_arm_flexed and right_moving_up:
                right_count += 1
                print(f"Bicep Curl Count (Right Arm): {right_count}")
                update_queue.put(("right", right_count))
                right_arm_flexed = False
                right_moving_up = False

            # Visual feedback for correct posture
            if left_elbow_angle < 90 or right_elbow_angle < 90:
                cv2.putText(image, "Correct Curl", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            else:
                cv2.putText(image, "Extend Arms", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # Display curl counts for both arms
        cv2.putText(image, f"Left Count: {left_count}", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
        cv2.putText(image, f"Right Count: {right_count}", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)

        # Display progress bar for target count
        try:
            new_target = target_count.get()
            if new_target != "":
                progress = min(max(left_count / int(new_target), right_count / int(new_target)), 1.0)  # Progress as a fraction (0 to 1)
                draw_progress_bar(image, progress)
                if left_count >= int(new_target) or right_count >= int(new_target):
                    play_buzzer_once()
        except ValueError:
            pass

        # Display the updated frame
        cv2.imshow("Bicep Curl Counter", image)

        key = cv2.waitKey(1)
        if key == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
