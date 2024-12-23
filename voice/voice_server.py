import socket
import threading

# Настройки сервера
HOST = '0.0.0.0'
PORT = 5000

# Список подключенных клиентов
clients = []

def broadcast(sender_conn, data):
    """Отправить данные всем клиентам, кроме отправителя"""
    for client in clients:
        if client != sender_conn:
            try:
                client.sendall(data)
            except:
                clients.remove(client)

def handle_client(conn, addr):
    """Обработка каждого клиента"""
    print(f"Подключился: {addr}")
    while True:
        try:
            data = conn.recv(1024)
            if not data:
                break
            broadcast(conn, data)
        except ConnectionResetError:
            break
    print(f"Отключился: {addr}")
    clients.remove(conn)
    conn.close()

def main():
    """Главная функция запуска сервера"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"Сервер запущен на {HOST}:{PORT}")
    while True:
        conn, addr = server.accept()
        clients.append(conn)
        threading.Thread(target=handle_client, args=(conn, addr)).start()

if __name__ == "__main__":
    main()
