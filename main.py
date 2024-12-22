import subprocess
import sys

def run_subprocess(command):
    return subprocess.Popen(command, stdout=sys.stdout, stderr=sys.stderr)

def start_services():
    # Запускаем parser.py и server.py как независимые процессы
    parser_process = run_subprocess([sys.executable, 'parser.py'])
    server_process = run_subprocess([sys.executable, 'server.py'])

    try:
        # Ожидаем завершения любого из процессов
        while True:
            # Если parser.py завершился
            if parser_process.poll() is not None:
                print("parser.py завершился. Завершаем main.py.")
                server_process.terminate()  # Завершаем server.py
                server_process.wait()
                sys.exit(parser_process.returncode)

            # Если server.py завершился
            if server_process.poll() is not None:
                print("server.py завершился. Завершаем main.py.")
                parser_process.terminate()  # Завершаем parser.py
                parser_process.wait()
                sys.exit(server_process.returncode)

    except KeyboardInterrupt:
        print("Получен сигнал завершения. Завершаем все процессы.")
        parser_process.terminate()
        server_process.terminate()
        parser_process.wait()
        server_process.wait()
        sys.exit(0)

if __name__ == '__main__':
    start_services()
