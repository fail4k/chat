import customtkinter as ctk
import pyaudio
import socket
import threading
import numpy as np
from PIL import Image

voice_chat_window = ctk.CTkToplevel()
voice_chat_window.title("Голосовой чат")
voice_chat_window.geometry('200x250')

# Загрузка изображений
image_on = Image.open("img/on.png")  # Укажите путь к вашему изображению
image_on = image_on.resize((60, 60), Image.LANCZOS)  # Изменение размера изображения
photo_on = ctk.CTkImage(light_image=image_on, dark_image=image_on)

image_off = Image.open("img/off.png")  # Укажите путь к вашему изображению
image_off = image_off.resize((60, 60), Image.LANCZOS)  # Изменение размера изображения
photo_off = ctk.CTkImage(light_image=image_off, dark_image=image_off)

# Настройки аудио
CHUNK = 2048  # Увеличенный размер буфера для уменьшения частоты отправки данных
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000  # Снижение частоты дискретизации для уменьшения нагрузки
THRESHOLD = 1000  # Порог для определения, есть ли звук

# Настройки клиента
SERVER_IP = '127.0.0.1'
SERVER_PORT = 5000

# Инициализация PyAudio
p = pyaudio.PyAudio()

global mic_muted  # Объявляем mic_muted глобальной переменной
mic_muted = True  # Начальное состояние микрофона (отключен)
send_thread = None

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
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    while not mic_muted:
        try:
            audio_data = stream.read(CHUNK, exception_on_overflow=False)
            client_socket.sendall(audio_data)  # Отправляем данные на сервер

            # Проверяем громкость
            volume_level = np.frombuffer(audio_data, dtype=np.int16).max()
            if volume_level > THRESHOLD:
                mute_button.configure(border_color='green')  # Обводка зеленая, когда есть звук
            else:
                mute_button.configure(border_color='black')  # Обводка черная, когда нет звука
        except Exception as e:
            print(f"Ошибка при отправке аудио: {e}")
            stream.stop_stream()
            stream.close()
            break

# Функция переключения состояния микрофона (вкл/выкл)
def toggle_mic():
    global mic_muted, send_thread  # Используем глобальные переменные

    mic_muted = not mic_muted
    if mic_muted:
        mute_button.configure(image=photo_off, border_color='black')  # Отображаем изображение "выключен"
    else:
        mute_button.configure(image=photo_on, border_color='black')  # Отображаем изображение "включен"
        # Перезапускаем поток отправки, если микрофон включен
        send_thread = threading.Thread(target=send_audio, args=(client_socket,))
        send_thread.daemon = True  # Позволяет потоку завершиться при выходе
        send_thread.start()

# Подключение к серверу
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((SERVER_IP, SERVER_PORT))

# Основные элементы интерфейса
frame = ctk.CTkFrame(voice_chat_window, width=190, height=240, fg_color='#1B1B1B')
frame.pack(pady=10, padx=10)

title = ctk.CTkLabel(voice_chat_window, text="Голосовой чат", font=ctk.CTkFont(size=20, weight="bold"), bg_color='#1B1B1B')
title.place(relx=0.5, rely=0.1, anchor=ctk.CENTER)

# Кнопка для включения/отключения микрофона
mute_button = ctk.CTkButton(voice_chat_window, image=photo_off, text='', border_width=3, 
                            border_color='black', fg_color='black', 
                            hover_color='#0f0f0f', width=50, height=40, 
                            command=toggle_mic)  # Устанавливаем изображение "выключен"
mute_button.place(relx=0.5, rely=0.8, anchor=ctk.CENTER)

# Запуск потоков для приема аудио
receive_thread = threading.Thread(target=receive_audio, args=(client_socket,))
receive_thread.daemon = True  # Позволяет потоку завершиться при выходе
receive_thread.start()

# Обработчик закрытия окна
def on_closing():
    global voice_chat_open  # Делаем переменную глобальной
    voice_chat_open = False  # Сбрасываем флаг, когда окно закрывается
    voice_chat_window.destroy()  # Закрываем окно

voice_chat_window.protocol("WM_DELETE_WINDOW", on_closing)  # Связываем событие закрытия окна с функцией