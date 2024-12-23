import customtkinter as ctk
import socket
import threading
import time
from PIL import Image
import pyaudio
import numpy as np
from customtkinter import CTkImage
import os

class MessengerApp:
    def __init__(self, master, client_socket, nickname):
        self.master = master
        self.client_socket = client_socket
        self.nickname = nickname
        self.connected = True
        self.unsent_messages = []
        master.title(f"Messenger - {nickname}")
        master.geometry('700x350')
        master.resizable(False, False)

        try:
            self.image_send = Image.open("img/send.png")
            self.image_send = self.image_send.resize((50, 50), Image.LANCZOS)
            self.photo_send = CTkImage(light_image=self.image_send, dark_image=self.image_send)
            
            self.image_file = Image.open("img/file.png")
            self.image_file = self.image_file.resize((50, 50), Image.LANCZOS)
            self.photo_file = CTkImage(light_image=self.image_file, dark_image=self.image_file)
        except Exception as e:
            print(f"Ошибка при загрузке изображения: {e}")
            self.photo_send = None
            self.photo_file = None
        
        self.message_display = ctk.CTkTextbox(master, width=500, height=300, corner_radius=10, state='disabled')
        self.message_display.place(relx=0.01, rely=0.01)
        self.message_display.configure(font=("Arial", 14))
        
        self.frame_voice = ctk.CTkFrame(master, width=175, height=125, corner_radius=10, fg_color='#1B1B1B')
        self.frame_voice.place(relx=0.74, rely=0.01)
        
        self.label_frame_voice = ctk.CTkLabel(master, text='Голосовой чат', text_color='#00c525', bg_color='#1B1B1B', font=('Arial', 15))
        self.label_frame_voice.place(relx=0.75, rely=0.01)
        
        self.label_acc_value = ctk.CTkLabel(master, text='Количество участников: ', font=('Arial', 12), fg_color='#1B1B1B')
        self.label_acc_value.place(relx=0.75, rely=0.125)

        def join_voice():
            voice_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            voice_socket.connect((ip, port))
            
            CHUNK = 1024
            FORMAT = pyaudio.paInt16
            CHANNELS = 1
            RATE = 44100
            THRESHOLD = 500
            
            p = pyaudio.PyAudio()
            mic_muted = True
            
            voice_window = ctk.CTkToplevel()
            voice_window.title("Голосовой чат")
            voice_window.geometry('200x250')
            
            image_on = Image.open("img/on.png")
            image_on = image_on.resize((60, 60), Image.LANCZOS)
            photo_on = CTkImage(light_image=image_on, dark_image=image_on)

            image_off = Image.open("img/off.png")
            image_off = image_off.resize((60, 60), Image.LANCZOS)
            photo_off = CTkImage(light_image=image_off, dark_image=image_off)

            def toggle_mic():
                nonlocal mic_muted
                mic_muted = not mic_muted
                if mic_muted:
                    mute_button.configure(image=photo_off, border_color='black')
                else:
                    mute_button.configure(image=photo_on, border_color='black')
                    threading.Thread(target=send_audio).start()

            def send_audio():
                stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, 
                              input=True, frames_per_buffer=CHUNK)
                while not mic_muted:
                    try:
                        audio_data = stream.read(CHUNK, exception_on_overflow=False)
                        voice_socket.sendall(bytes([2]) + audio_data)
                        
                        volume_level = np.frombuffer(audio_data, dtype=np.int16).max()
                        if volume_level > THRESHOLD:
                            mute_button.configure(border_color='green')
                        else:
                            mute_button.configure(border_color='black')
                    except:
                        break
                stream.stop_stream()
                stream.close()

            def receive_audio():
                stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                              output=True, frames_per_buffer=CHUNK)
                while True:
                    try:
                        data = voice_socket.recv(CHUNK + 1)
                        if data and data[0] == 2:
                            stream.write(data[1:])
                    except:
                        break
                stream.stop_stream()
                stream.close()

            frame = ctk.CTkFrame(voice_window, width=190, height=240, fg_color='#1B1B1B')
            frame.pack(pady=10, padx=10)

            title = ctk.CTkLabel(voice_window, text="Голосовой чат",
                               font=ctk.CTkFont(size=20, weight="bold"),
                               bg_color='#1B1B1B')
            title.place(relx=0.5, rely=0.1, anchor=ctk.CENTER)

            mute_button = ctk.CTkButton(voice_window, image=photo_off, text='',
                                      border_width=3, border_color='black',
                                      fg_color='black', hover_color='#0f0f0f',
                                      width=50, height=40, command=toggle_mic)
            mute_button.place(relx=0.5, rely=0.8, anchor=ctk.CENTER)

            threading.Thread(target=receive_audio, daemon=True).start()

            def on_closing():
                nonlocal mic_muted
                mic_muted = True
                try:
                    voice_socket.shutdown(socket.SHUT_RDWR)
                    voice_socket.close()
                except:
                    pass
                voice_window.destroy()

            voice_window.protocol("WM_DELETE_WINDOW", on_closing)

        self.button_join_voice = ctk.CTkButton(master, text='войти',
                                              command=lambda: threading.Thread(target=join_voice).start(),
                                              width=165, fg_color='#2c2c2c',
                                              hover_color='#373737', corner_radius=7)
        self.button_join_voice.place(relx=0.745, rely=0.25)

        self.frame_acc = ctk.CTkFrame(master, width=175, height=200,
                                    corner_radius=10, fg_color='#1B1B1B')
        self.frame_acc.place(relx=0.74, rely=0.4)

        self.button_file = ctk.CTkButton(master, image=self.photo_file,
                                       width=30, height=25, text="",
                                       fg_color='#1a1a1a', hover_color='#303030')
        self.button_file.place(relx=0.01, rely=0.885)
        
        self.message_entry = ctk.CTkEntry(master, width=415)
        self.message_entry.place(relx=0.065, rely=0.885)
        self.message_entry.bind("<Return>", lambda event: self.send_message())

        self.send_button = ctk.CTkButton(master, image=self.photo_send,
                                       width=30, height=25, text="",
                                       fg_color='#1a1a1a', hover_color='#303030',
                                       command=self.send_message)
        self.send_button.place(relx=0.66, rely=0.885)

        threading.Thread(target=self.receive_messages, daemon=True).start()
        threading.Thread(target=self.keep_alive, daemon=True).start()

    def send_message(self):
        message = self.message_entry.get()
        if message:
            self.message_entry.delete(0, "end")
            if self.connected:
                threading.Thread(target=self._send_message_thread, args=(message,)).start()
            else:
                self.unsent_messages.append(message)
                threading.Thread(target=self.reconnect).start()

    def _send_message_thread(self, message):
        try:
            data = bytes([1]) + f"{self.nickname}: {message}".encode('utf-8')
            self.client_socket.send(data)
            self.display_message(f"[{time.strftime('%H:%M:%S')}] [{self.nickname}] {message}")
        except:
            self.unsent_messages.append(message)
            threading.Thread(target=self.reconnect).start()

    def receive_messages(self):
        while True:
            try:
                data = self.client_socket.recv(4096)
                if data:
                    if data[0] == 1:
                        message = data[1:].decode('utf-8')
                        self.display_message(message.strip())
            except:
                self.connected = False
                break

    def keep_alive(self):
        while True:
            time.sleep(30)
            if self.connected:
                try:
                    self.client_socket.send(bytes([1]))
                except:
                    self.connected = False
                    threading.Thread(target=self.reconnect).start()

    def display_message(self, message):
        self.message_display.configure(state='normal')
        self.message_display.insert("end", message + "\n")
        self.message_display.configure(state='disabled')
        self.message_display.see("end")

    def reconnect(self):
        self.connected = False
        while not self.connected:
            try:
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.connect((ip, port))
                self.connected = True
                threading.Thread(target=self.receive_messages, daemon=True).start()
                while self.unsent_messages:
                    self._send_message_thread(self.unsent_messages.pop(0))
            except:
                time.sleep(5)

def center_window(window, width, height):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    window.geometry(f'{width}x{height}+{x}+{y}')

def enter_server_info(nickname):
    server_info_window = ctk.CTk()
    server_info_window.title("Enter Server Info")
    server_info_window.geometry('400x275')
    center_window(server_info_window, 400, 275)

    ip_label = ctk.CTkLabel(server_info_window, text="Введите айпи:")
    ip_label.pack(pady=10)

    ip_entry = ctk.CTkEntry(server_info_window)
    ip_entry.pack(pady=10)

    port_label = ctk.CTkLabel(server_info_window, text="Введите порт:")
    port_label.pack(pady=10)

    port_entry = ctk.CTkEntry(server_info_window)
    port_entry.pack(pady=10)

    def on_server_info_enter():
        global ip, port
        ip = ip_entry.get()
        port = port_entry.get()
        try:
            port = int(port)
            server_info_window.destroy()
            start_messenger(ip, port, nickname)
        except ValueError:
            ctk.CTkMessageBox.showerror("Error", "Invalid port number")

    enter_button = ctk.CTkButton(server_info_window, text="Enter",
                                command=on_server_info_enter)
    enter_button.pack(pady=10)

    server_info_window.mainloop()

def start_messenger(ip, port, nickname):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((ip, port))
    
    root = ctk.CTk()
    app = MessengerApp(root, client_socket, nickname)
    root.mainloop()

if __name__ == "__main__":
    nickname_window = ctk.CTk()
    nickname_window.title("Enter Nickname")
    nickname_window.geometry('400x275')
    center_window(nickname_window, 400, 275)

    label = ctk.CTkLabel(nickname_window, text="Введите ваше имя:")
    label.pack(pady=20)

    nickname_entry = ctk.CTkEntry(nickname_window)
    nickname_entry.pack(pady=10)

    def on_nickname_enter():
        nickname = nickname_entry.get()
        if nickname:
            nickname_window.destroy()
            enter_server_info(nickname)

    enter_button = ctk.CTkButton(nickname_window, text="Enter",
                                command=on_nickname_enter)
    enter_button.pack(pady=10)

    nickname_window.mainloop()
