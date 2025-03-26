import socket
import struct
from protocol import SizeProtocol

IP = "127.0.0.1"
PORT = 12345

def server_connection():
    """Установка соединения с сервером"""
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((IP, PORT))  # Подключение к серверу
        print("Соединение с сервером установлено")
        return client_socket
    except Exception as error:
        print(f"Ошибка при подключении к серверу: {error}")
        return None

def command_sending(client_socket, command):
    """Отправка команды серверу и получение ответа"""
    try:
        SizeProtocol.send(client_socket, command) # Протокол для отправки команды
        response = SizeProtocol.recv(client_socket)  # Протокол для получения ответа
        return response
    except Exception as error:
        print(f"Ошибка при отправке/получении данных: {error}")
        return None

def program_adding(client_socket):
    """Добавление новой программы"""
    prog_name = input("Введите имя программы для добавления: ")  # Ввод названия программы
    command = f"ADD {prog_name}"  # Формирование команды
    response = command_sending(client_socket, command)  # Отправка команды
    print(response)  # Вывод ответа сервера

def output_requesting(client_socket):
    """Запрос объединённого вывода программы"""
    prog_name = input("Введите имя программы для получения вывода: ")  # Ввод названия программы
    command = f"GET {prog_name}"  # Формирование команды
    response = command_sending(client_socket, command)  # Отправка команды
    if response:
        print(f"=== Вывод программы '{prog_name}' ===\n{response}\n===")  # Вывод результата

def main():
    """Основная функция клиента"""
    client_socket = server_connection()  # Установка соединения с сервером
    if not client_socket:
        return

    while True:
        print("\nДоступные команды:")
        print("1. Добавить программу (ADD)")
        print("2. Получить вывод программы (GET)")
        print("3. Выйти")
        choice = input("Выберите команду (1/2/3): ")  # Ввод команды пользователем

        if choice == "1":
            program_adding(client_socket)  # Добавление программы
        elif choice == "2":
            output_requesting(client_socket)  # Запрос вывода программы
        elif choice == "3":
            print("Завершение работы клиента")
            break
        else:
            print("Неверный выбор. Попробуйте снова")  # Обработка неверного выбора

    client_socket.close()  # Закрытие соединения с сервером

if __name__ == "__main__":
    main()
