import socket # Работа с сетью
import os # Операционная система
import time
import sys # Системные функции
import json
import threading # Работа с потоками
import subprocess # Внешние процессы
import signal # Сигнал завершения

# Файл с данными про программы
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
data_about_progs = os.path.join(BASE_DIR, "data_about_progs.json")

IP = "127.0.0.1"
PORT = 12345

# Интервал, через который запускаются программы
interval = 10

# Словарь с данными про программы
all_progs = {}

# Список активных потоков
all_threads = []

# Флаг для завершения работы сервера
stop_server_flag = threading.Event()

def loading():
    """Загрузка данных о программах из JSON-файла"""
    global all_progs
    if os.path.exists(data_about_progs):  # Проверка существования файла
        try:
            with open(data_about_progs, "r", encoding="utf-8") as file:
                all_progs = json.load(file)  # Загрузка данных из файла
        except Exception as error:
            print(f"Ошибка при загрузке данных: {error}")
            all_progs = {}  # Инициализация пустого словаря в случае ошибки
    else:
        all_progs = {}  # Инициализация пустого словаря, если файл не существует

def cleaning(name):
    """Очистка названия папки от недопустимых символов"""
    return "".join(char if char.isalnum() or char in ('-', '_') else '-' for char in name)

def new_folder(prog_name):
    """Создание папки для программы, если она ещё не существует"""
    folder = os.path.join(BASE_DIR, cleaning(prog_name))  # Очистка названия папки
    if not os.path.exists(folder):  # Проверка существования папки
        os.makedirs(folder)  # Создание папки
    return folder

def saving():
    """Сохранение данных о программах в JSON-файл"""
    try:
        with open(data_about_progs, "w", encoding="utf-8") as file:
            json.dump(all_progs, file, indent=4, ensure_ascii=False)  # Запись данных в файл
    except Exception as error:
        print(f"Ошибка при сохранении данных: {error}")

def execution(prog_name):
    """Циклический запуск программы с интервалом и сохранение её вывода"""
    folder = all_progs[prog_name]["folder"]  # Получение папки для программы
    while not stop_server_flag.is_set():  # Проверка флага завершения
        start_time = time.strftime("%H%M%S_%d%m%y")  # Формат времени
        result_file = os.path.join(folder, f"result-{start_time}.txt")  # Название файла для вывода
        try:
            # Запуск программы и получение её вывода
            command = f"{sys.executable} {os.path.abspath(prog_name)}"
            process_result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=30)
            output = process_result.stdout
        except Exception as error:
            output = f"Ошибка во время запуска программы: {error}"

        # Сохранение вывода в файл
        try:
            with open(result_file, "w", encoding="utf-8") as file:
                file.write(output)  # Запись вывода в файл
        except Exception as error:
            print(f"Ошибка при записи в файл {result_file}: {error}")

        # Добавление информации о запуске в словарь
        all_progs[prog_name]["runs"].append({"time": start_time, "file": result_file})
        saving()  # Сохранение данных в JSON
        time.sleep(interval)  # Ожидание интервала перед следующим запуском

def signal_handler(sig, frame):
    """Обработка сигнала завершения (Ctrl+C)"""
    print("\nПолучен сигнал завершения. Останавливаю сервер...")
    stop_server_flag.set()  # Установка флага завершения

    # Остановка всех потоков
    for thread in all_threads:
        thread.join(timeout=1)  # Ожидание завершения потоков

    saving()  # Сохранение данных перед выходом
    print("Сервер завершён.")
    os._exit(0)  # Принудительное завершение процесса

def client_handling(conn, addr):
    """Обработка запросов от клиента."""
    print(f"Подключен клиент: {addr}")
    while not stop_server_flag.is_set():  # Проверка флага завершения
        try:
            data = conn.recv(1024).decode("utf-8")  # Получение данных от клиента
            if not data:
                break

            if data.startswith("ADD"):
                # Обработка команды ADD
                _, prog_name = data.split(maxsplit=1)
                if not os.path.exists(prog_name):  # Проверка существования программы
                    conn.send(f"Ошибка: программа '{prog_name}' не найдена.".encode("utf-8"))
                    continue

                if prog_name not in all_progs:  # Проверка, добавлена ли программа
                    folder = new_folder(prog_name)  # Создание папки для программы
                    all_progs[prog_name] = {"folder": folder, "runs": []}  # Добавление программы в словарь
                    thread = threading.Thread(target=execution, args=(prog_name,), daemon=True)
                    thread.start()
                    all_threads.append(thread)
                    saving()  # Сохранение данных
                    conn.send(f"Программа '{prog_name}' добавлена и запущена.".encode("utf-8"))
                else:
                    conn.send(f"Программа '{prog_name}' уже запущена.".encode("utf-8"))

            elif data.startswith("GET"):
                # Обработка команды GET
                _, prog_name = data.split(maxsplit=1)
                if prog_name in all_progs:  # Проверка существования программы
                    combined_output = ""
                    for run in all_progs[prog_name]["runs"]:  # Обход всех запусков программы
                        try:
                            with open(run["file"], "r", encoding="utf-8") as file:
                                combined_output += f"=== {run['time']} ===\n{file.read()}\n"
                        except Exception as error:
                            combined_output += f"Ошибка при чтении файла {run['file']}: {error}\n"
                    conn.send(combined_output.encode("utf-8"))  # Отправка объединённого вывода
                else:
                    conn.send(f"Программа '{prog_name}' не найдена.".encode("utf-8"))

            else:
                conn.send("Неизвестная команда.".encode("utf-8"))  # Ответ на неизвестную команду

        except Exception as error:
            print(f"Ошибка при обработке запроса от клиента {addr}: {error}")
            break

    print(f"Клиент {addr} отключен.")
    conn.close()  # Закрытие соединения с клиентом

def server_starting():
    """Запуск сервера и ожидание подключения клиентов"""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind((IP, PORT))  # Привязка сервера к IP и порту
        server_socket.listen(5)  # Ожидание подключений
        print(f"Сервер слушает порт {PORT}...")

        while not stop_server_flag.is_set():  # Проверка флага завершения
            try:
                conn, addr = server_socket.accept()  # Принятие подключения клиента
                client_thread = threading.Thread(target=client_handling, args=(conn, addr), daemon=True)
                client_thread.start()
            except Exception as error:
                if not stop_server_flag.is_set():
                    print(f"Ошибка при подключении клиента: {error}")
    finally:
        server_socket.close()  # Закрытие сокета сервера
        print("Сокет сервера закрыт.")

def main():
    """Основная функция сервера."""
    print("Сервер запущен. Для остановки нажмите Ctrl + C...")
    loading()  # Загрузка данных о программах
    for prog in sys.argv[1:]:  # Обработка аргументов командной строки
        if os.path.exists(prog):  # Проверка существования программы
            folder = new_folder(prog)  # Создание папки для программы
            if prog not in all_progs:  # Проверка, добавлена ли программа
                all_progs[prog] = {"folder": folder, "runs": []}
            thread = threading.Thread(target=execution, args=(prog,), daemon=True)
            thread.start()
            all_threads.append(thread)
        else:
            print(f"Ошибка: программа '{prog}' не найдена.")
    saving()  # Сохранение данных

    # Запуск сервера для обработки клиентов
    server_thread = threading.Thread(target=server_starting)
    server_thread.start()

    # Обработка сигнала завершения
    signal.signal(signal.SIGINT, signal_handler)
    while not stop_server_flag.is_set():  # Проверка флага завершения
        time.sleep(1)

if __name__ == "__main__":
    main()
