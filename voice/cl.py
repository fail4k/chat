import customtkinter as ctk
import pyaudio
import socket
import threading
import numpy as np
from PIL import Image

# Настройки клиента
SERVER_IP = '127.0.0.1'  # Укажите IP-адрес сервера
SERVER_PORT = 5000     # Порт сервера

# Настройки аудио
CHUNK = 2048
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
THRESHOLD = 1000

# Глобальные переменные
mic_muted = True
send_thread = None

# Инициализация PyAudio
p = pyaudio.PyAudio()

# Подключение к серверу
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((SERVER_IP, SERVER_PORT))


# Функция для приема и воспроизведения аудиоданных
def receive_audio(client_socket):
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)
    while True:
        try:
            audio_data = client_socket.recv(CHUNK)
            if audio_data:
                stream.write(audio_data)
        except Exception as e:
            print(f"Ошибка при получении аудио: {e}")
            stream.stop_stream()
            stream.close()
            break


# Функция для захвата аудиоданных с микрофона и отправки их на сервер
def send_audio(client_socket):
    global mic_muted
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    while not mic_muted:
        try:
            audio_data = stream.read(CHUNK, exception_on_overflow=False)
            client_socket.sendall(audio_data)

            # Проверка уровня громкости
            volume_level = np.frombuffer(audio_data, dtype=np.int16).max()
            if volume_level > THRESHOLD:
                mute_button.configure(border_color='green')
            else:
                mute_button.configure(border_color='black')
        except Exception as e:
            print(f"Ошибка при отправке аудио: {e}")
            stream.stop_stream()
            stream.close()
            break


# Функция переключения состояния микрофона
def toggle_mic():
    global mic_muted, send_thread
    mic_muted = not mic_muted

    if mic_muted:
        mute_button.configure(image=photo_off, border_color='black')
    else:
        mute_button.configure(image=photo_on, border_color='black')
        send_thread = threading.Thread(target=send_audio, args=(client_socket,))
        send_thread.daemon = True
        send_thread.start()


# Графический интерфейс
voice_chat_window = ctk.CTk()
voice_chat_window.title("Голосовой чат")
voice_chat_window.geometry('200x250')

# Загрузка изображений
image_on = Image.open("img/on.png")
image_on = image_on.resize((60, 60), Image.LANCZOS)
photo_on = ctk.CTkImage(light_image=image_on, dark_image=image_on)

image_off = Image.open("img/off.png")
image_off = image_off.resize((60, 60), Image.LANCZOS)
photo_off = ctk.CTkImage(light_image=image_off, dark_image=image_off)

frame = ctk.CTkFrame(voice_chat_window, width=190, height=240, fg_color='#1B1B1B')
frame.pack(pady=10, padx=10)

title = ctk.CTkLabel(voice_chat_window, text="Голосовой чат", font=ctk.CTkFont(size=20, weight="bold"), bg_color='#1B1B1B')
title.place(relx=0.5, rely=0.1, anchor=ctk.CENTER)

mute_button = ctk.CTkButton(voice_chat_window, image=photo_off, text='', border_width=3, 
                            border_color='black', fg_color='black', 
                            hover_color='#0f0f0f', width=50, height=40, 
                            command=toggle_mic)
mute_button.place(relx=0.5, rely=0.8, anchor=ctk.CENTER)


# Поток для приема аудио
receive_thread = threading.Thread(target=receive_audio, args=(client_socket,))
receive_thread.daemon = True
receive_thread.start()


# Обработчик закрытия окна
def on_closing():
    global voice_chat_open
    voice_chat_open = False
    voice_chat_window.destroy()
    client_socket.close()


voice_chat_window.protocol("WM_DELETE_WINDOW", on_closing)
voice_chat_window.mainloop()
