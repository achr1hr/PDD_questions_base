import sys
import subprocess
import threading

def run_parser():
    # Запускает парсер для обновления данных
    subprocess.run([sys.executable, 'parser.py'])

def run_server():
    # Запускает сервер для обслуживания веб-страниц
    subprocess.run([sys.executable, 'server.py'])

def start_services():
    # Запускает парсер и сервер в отдельных потоках
    parser_thread = threading.Thread(target=run_parser)
    server_thread = threading.Thread(target=run_server)

    # Запускаем оба потока
    parser_thread.start()
    server_thread.start()

    # Ожидаем завершения потоков
    parser_thread.join()
    server_thread.join()

if __name__ == '__main__':
    start_services()
