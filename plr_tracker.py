import cv2
import mediapipe as mp
import os
import time
from pygame import mixer
import tkinter as tk


def init_player():
    mixer.init()
    song_folder = # Song Directory on your machine
    playlist = [os.path.join(song_folder, song) for song in os.listdir(song_folder) if song.endswith(".mp3")]
    return playlist, 0


def play_song(playlist, index):
    mixer.music.load(playlist[index])
    mixer.music.play()
    song_name = os.path.basename(playlist[index])
    window.after(0, lambda: song_label.config(text=f"Playing: {song_name}"))


def pause_song():
    mixer.music.pause()
    print("Paused")
    window.after(0, lambda: song_label.config(text="Paused"))


def resume_song():
    mixer.music.unpause()
    song_name = os.path.basename(playlist[current_song_index])
    print("Resumed")
    window.after(0, lambda: song_label.config(text=f"Playing: {song_name}"))


def change_song(playlist, index, direction):
    index = (index + direction) % len(playlist)
    play_song(playlist, index)
    return index


def count_fingers(hand_landmarks):
    tips_ids = [4, 8, 12, 16, 20]
    fingers = []

    if hand_landmarks.landmark[tips_ids[0]].x < hand_landmarks.landmark[tips_ids[0] - 1].x:
        fingers.append(1)
    else:
        fingers.append(0)

    for id in range(1, 5):
        if hand_landmarks.landmark[tips_ids[id]].y < hand_landmarks.landmark[tips_ids[id] - 2].y:
            fingers.append(1)
        else:
            fingers.append(0)
    return fingers


def check_volume_gesture(fingers, landmarks):
    if fingers == [1, 0, 0, 0, 0]:
        thumb_tip_y = landmarks.landmark[4].y
        thumb_mcp_y = landmarks.landmark[2].y
        return "up" if thumb_tip_y < thumb_mcp_y else "down"
    return None


def setup_gui(on_exit):
    global song_label, window
    window = tk.Tk()
    window.title("Gesture Controlled Media Player")

    song_label = tk.Label(window, text="No song is playing", font=("Helvetica", 16))
    song_label.pack(pady=20)

    exit_button = tk.Button(window, text="Exit", font=("Helvetica", 14), command=on_exit)
    exit_button.pack(pady=10)

    return window


def gesture_controlled_player():
    global playlist, current_song_index, volume, last_volume, song_label, window

    playlist, current_song_index = init_player()

    def on_exit():
        print("Exiting Program...")
        mixer.music.stop()
        cap.release()
        cv2.destroyAllWindows()
        window.destroy()

    window = setup_gui(on_exit)

    cap = cv2.VideoCapture(0)
    while not cap.isOpened():
        time.sleep(0.1)

    window.update()
    play_song(playlist, current_song_index)

    is_playing = True
    is_muted = False
    volume = 0.5
    last_volume = volume
    last_action_time = 0

    mixer.music.set_volume(volume)

    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(max_num_hands=1)
    mp_draw = mp.solutions.drawing_utils

    while True:
        ret, img = cap.read()
        if not ret:
            break
        img = cv2.flip(img, 1)
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_img)

        if results.multi_hand_landmarks:
            for hand_landmark in results.multi_hand_landmarks:
                mp_draw.draw_landmarks(img, hand_landmark, mp_hands.HAND_CONNECTIONS)
                fingers = count_fingers(hand_landmark)
                finger_count = sum(fingers)
                current_time = time.time()

                vol_gesture = check_volume_gesture(fingers, hand_landmark)
                if vol_gesture and current_time - last_action_time > 1:
                    if vol_gesture == "up" and volume < 1.0:
                        volume = min(1.0, volume + 0.1)
                        mixer.music.set_volume(volume)
                        print(f"Volume Increased: {int(volume * 100)}%")
                    elif vol_gesture == "down" and volume > 0.0:
                        volume = max(0.0, volume - 0.1)
                        mixer.music.set_volume(volume)
                        print(f"Volume Decreased: {int(volume * 100)}%")
                    last_action_time = current_time

                if current_time - last_action_time > 1.5:
                    if finger_count == 0 and not is_muted:
                        last_volume = volume
                        mixer.music.set_volume(0.0)
                        is_muted = True
                        print("Muted")
                        window.after(0, lambda: song_label.config(text="Muted"))
                        last_action_time = current_time

                    elif is_muted and finger_count > 0:
                        mixer.music.set_volume(last_volume)
                        volume = last_volume
                        is_muted = False
                        print(f"Unmuted - Volume: {int(volume * 100)}%")
                        window.after(0, lambda: song_label.config(text="Unmuted"))
                        last_action_time = current_time

                    elif finger_count == 1:
                        if is_playing:
                            pause_song()
                        else:
                            resume_song()
                        is_playing = not is_playing
                        last_action_time = current_time

                    elif finger_count == 2:
                        current_song_index = change_song(playlist, current_song_index, 1)
                        is_playing = True
                        last_action_time = current_time

                    elif finger_count == 3:
                        current_song_index = change_song(playlist, current_song_index, -1)
                        is_playing = True
                        last_action_time = current_time

        cv2.imshow("Gesture Controlled Media Player", img)
        window.update()
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    window.destroy()


if __name__ == "__main__":
    gesture_controlled_player()
