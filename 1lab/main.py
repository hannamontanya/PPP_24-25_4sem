import os
import time
import subprocess
import signal
import sys

def main():
    """Главная функция программы"""
    script_directory = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_directory)  # Переход в директорию скрипта

    # Пути к файлам сервера и клиента
    server_file_path = os.path.join(script_directory, "server.py")
    client_file_path = os.path.join(script_directory, "client.py")

    # Проверка наличия файлов сервера и клиента
    if not os.path.exists(server_file_path):
        print(f"Файл сервера {server_file_path} отсутствует")
        sys.exit(1)
    if not os.path.exists(client_file_path):
        print(f"Файл клиента {client_file_path} отсутствует")
        sys.exit(1)

    # Получение списка программ из аргументов командной строки
    program_list = sys.argv[1:]

    # Если программы не переданы, запрашиваем их у пользователя
    if not program_list:
        user_input = input("Введите имена программ через пробел: ")
        program_list = user_input.split()

    if not program_list:
        print("Ошибка: не указаны программы для запуска.")
        sys.exit(1)

    try:
        # Запуск сервера с переданными программами
        server_process = subprocess.Popen([sys.executable, server_file_path] + program_list)
        print(f"Сервер запущен с программами: {', '.join(program_list)}")
    except Exception as err:
        print(f"Не удалось запустить сервер: {err}")
        sys.exit(1)

    # Пауза для завершения инициализации сервера
    time.sleep(1)

    try:
        # Запуск клиента
        client_process = subprocess.Popen([sys.executable, client_file_path])
        print("Клиент успешно запущен.")
    except Exception as err:
        print(f"Не удалось запустить клиента: {err}")
        server_process.terminate()  # Остановка сервера
        sys.exit(1)

    def handle_exit(signal_number, frame_reference):
        """Функция для обработки завершения программы"""
        print("\nПолучен сигнал завершения. Остановка всех процессов...")
        try:
            client_process.terminate()  # Остановка клиента
        except Exception:
            pass  # Игнорируем ошибки
        try:
            server_process.terminate()  # Остановка сервера
        except Exception:
            pass  # Игнорируем ошибки
        try:
            # Ожидание завершения процессов
            client_process.wait(timeout=5)
            server_process.wait(timeout=5)
        except Exception:
            pass  # Игнорируем ошибки
        print("Все процессы остановлены.")
        sys.exit(0)  # Завершение программы

    # Настройка обработчиков сигналов
    signal.signal(signal.SIGINT, handle_exit)  # Ctrl+C
    signal.signal(signal.SIGTERM, handle_exit)  # SIGTERM

    try:
        while True:
            # Проверка состояния клиента
            if client_process.poll() is not None:
                print("Клиент завершил работу. Остановка сервера...")
                try:
                    server_process.terminate()  # Остановка сервера
                    server_process.wait(timeout=5)  # Ожидание завершения
                except Exception:
                    pass  # Игнорируем ошибки
                break  # Выход из цикла
            time.sleep(1)  # Пауза перед следующей проверкой
    except KeyboardInterrupt:  # Обработка Ctrl+C
        handle_exit(None, None)  # Вызов функции завершения

    print("Работа программы завершена. Возврат управления командной строке.")

if __name__ == "__main__":
    main()
