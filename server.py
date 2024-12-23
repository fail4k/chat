import socket
import threading
from datetime import datetime

# Настройки сервера
HOST = '127.0.0.1'  # Локальный адрес
PORT = 1604         # Порт для всех соединений
text_clients = []   # Список клиентов текстового чата
voice_clients = []  # Список клиентов голосового чата
messages = []       # Список текстовых сообщений

def get_current_time():
    return datetime.now().strftime("%H:%M:%S")  # Формат времени HH:MM:SS

# Функция для трансляции аудио всем клиентам, кроме отправителя
def broadcast_audio(audio_data, sender_conn):
    disconnected_clients = []
    for client in voice_clients:
        if client != sender_conn:
            try:
                client.sendall(bytes([2]) + audio_data)
            except Exception as e:
                print(f"Ошибка при отправке аудио клиенту: {e}")
                disconnected_clients.append(client)
    
    # Удаляем отключенных клиентов после цикла
    for client in disconnected_clients:
        remove_client(client)

# Функция для трансляции текстовых сообщений
def broadcast_message(message, sender_conn):
    disconnected_clients = []
    for client in text_clients:
        if client != sender_conn:
            try:
                client.send(bytes([1]) + message.encode('utf-8'))
            except Exception as e:
                print(f"Ошибка при отправке сообщения клиенту: {e}")
                disconnected_clients.append(client)
    
    # Удаляем отключенных клиентов после цикла        
    for client in disconnected_clients:
        remove_client(client)

# Функция для обработки клиента
def handle_client(client_socket, addr):
    print(f"Подключен клиент: {addr}")
    
    # Отправляем все предыдущие сообщения новому клиенту
    if messages:
        chat_history = "\n".join(messages)
        try:
            client_socket.send(bytes([1]) + chat_history.encode('utf-8'))
        except Exception as e:
            print(f"Ошибка при отправке истории чата: {e}")
            remove_client(client_socket)
            return

    text_clients.append(client_socket)
    voice_clients.append(client_socket)

    while True:
        try:
            data = client_socket.recv(4096)
            if not data:
                break
                
            data_type = data[0]
            actual_data = data[1:]
            
            if data_type == 1:  # Текстовые сообщения
                message = actual_data.decode('utf-8')
                timestamped_message = f"[{get_current_time()}] {message}"
                messages.append(timestamped_message)
                broadcast_message(timestamped_message, client_socket)
            elif data_type == 2:  # Голосовые данные
                if len(actual_data) > 0:  # Проверяем, что есть аудиоданные
                    try:
                        broadcast_audio(actual_data, client_socket)
                    except Exception as e:
                        print(f"Ошибка при трансляции аудио: {e}")
                        break
                
        except ConnectionResetError:
            print(f"Клиент {addr} отключился.")
            break
        except Exception as e:
            print(f"Ошибка при обработке клиента {addr}: {e}")
            break

    remove_client(client_socket)

def remove_client(client_socket):
    if client_socket in text_clients:
        text_clients.remove(client_socket)
    if client_socket in voice_clients:
        voice_clients.remove(client_socket)
    try:
        client_socket.close()
    except Exception as e:
        print(f"Ошибка при закрытии сокета клиента: {e}")

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"Сервер запущен на {HOST}:{PORT}")

    while True:
        try:
            client_socket, addr = server.accept()
            client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            threading.Thread(target=handle_client, args=(client_socket, addr), daemon=True).start()
        except Exception as e:
            print(f"Ошибка при принятии подключения: {e}")

if __name__ == "__main__":
    start_server()
