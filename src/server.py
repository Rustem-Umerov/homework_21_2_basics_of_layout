# Импорт встроенной библиотеки для работы веб-сервера
import mimetypes
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from src.logger_config import logger_function

logger = logger_function(file_path=__file__)

# Для начала определим настройки запуска
HOST = "localhost"  # Адрес для доступа по сети
PORT = 8080  # Порт для доступа по сети


def load_html(file_path: Path) -> str:
    """
    Читает HTML‑файл и возвращает его содержимое.

    :param file_path: Путь к HTML‑файлу.
    :return: Содержимое файла в виде строки.
    :raises FileNotFoundError: Если файл не найден или путь не является файлом.
    :raises Exception: Если произошла ошибка при чтении файла.
    """

    # 1. Проверяем существование файла
    if not file_path.exists() or not file_path.is_file():
        logger.error("HTML-файл '%s' не найден", file_path)
        raise FileNotFoundError(file_path)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        logger.info("Файл '%s' успешно прочитан", file_path)
        return content

    except Exception:
        logger.exception("Ошибка при чтении HTML-файла '%s'", file_path)
        raise


class MyServer(BaseHTTPRequestHandler):
    """
    HTTP‑сервер, обрабатывающий GET и POST запросы.

    Атрибуты:
    base_dir (Path): Корневая директория проекта.
    static_dir (Path): Папка со статическими файлами.
    templates_dir (Path): Папка с HTML‑шаблонами.
    """

    base_dir: Path
    static_dir: Path
    templates_dir: Path

    def __init__(self, *args, **kwargs) -> None:
        """
        Инициализация атрибутов класса:
            * self.base_dir - путь к базовой папке проекта,
            * self.static_dir - путь к папке с файлами стиля и дизайна,
            * self.templates_dir - путь к папке с html-файлами,
            * получение атрибутов родительского класса.
        """

        self.base_dir: Path = Path(__file__).resolve().parent.parent
        self.static_dir = self.base_dir / "static"
        self.templates_dir = self.base_dir / "templates"
        super().__init__(*args, **kwargs)

    def do_GET(self) -> None:
        """Метод для обработки входящих GET-запросов"""

        logger.info("GET %s от %s", self.path, self.client_address[0])

        if self.path.lower().startswith("/static/"):
            self.serve_static()
        else:
            self.serve_html()

    def serve_html(self) -> None:
        """
        Отдаёт HTML‑страницу.
        Сейчас отдаётся один файл: contacts.html.
        """

        file_path = self.base_dir / "templates" / "contacts.html"

        try:
            html = load_html(file_path)
        except FileNotFoundError:
            logger.error("Файл '%s' не найден. Отправляю 404.", file_path)
            self.send_error(404, "Страница не найдена")
            return
        except Exception:
            logger.exception("Не удалось прочитать HTML-файл '%s'", file_path)
            self.send_error(500, "Внутренняя ошибка сервера")
            return

        self.send_response(200)  # Отправка кода ответа
        self.send_header("Content-type", "text/html")  # Отправка типа данных, который будет передаваться
        self.end_headers()  # Завершение формирования заголовков ответа

        self.wfile.write(html.encode("utf-8"))  # Тело ответа

    def serve_static(self) -> None:
        """
        Безопасно отдаёт статические файлы.
        """

        remove_static_dir = self.path[len("/static/") :]
        requested = Path(remove_static_dir)
        full_path = (self.static_dir / requested).resolve()

        logger.debug("Static запрос: %s → %s", self.path, full_path)

        # Проверка безопасности
        if self.static_dir not in full_path.parents:
            logger.warning("Попытка выхода за пределы static: %s", full_path)
            self.send_error(403, "Forbidden")
            return

        try:
            with full_path.open("rb") as f:  # Открытие файла
                data = f.read()  # Чтение файла
            logger.info("Отдаю static-файл: %s", full_path)

        except FileNotFoundError:
            logger.error("Static-файл '%s' не найден. Отправляю 404.", full_path)
            self.send_error(404, "Файл не найден")
            return

        except Exception:
            logger.exception("Ошибка при чтении static-файла '%s'", full_path)
            self.send_error(500, "Внутренняя ошибка сервера")
            return

        mime_type, _ = mimetypes.guess_type(full_path)
        self.send_response(200)
        self.send_header("Content-type", mime_type or "application/octet-stream")
        self.end_headers()
        self.wfile.write(data)  # Тело ответа

    def do_POST(self) -> None:
        """Обработка входящих POST‑запросов"""

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            raw_data = self.rfile.read(content_length)
            text_data = raw_data.decode("utf-8")

            logger.info("POST данные от клиента: %s", text_data)

        except Exception:
            logger.exception("Ошибка при обработке POST-запроса")
            self.send_error(400, "Некорректный POST-запрос")
            return

        try:
            self.send_response(200)  # Отправка кода ответа
            self.send_header("Content-type", "text/html")  # Отправка типа данных, который будет передаваться
            self.end_headers()  # Завершение формирования заголовков ответа

            self.wfile.write(raw_data)  # Тело ответа

        except Exception:
            logger.exception("Ошибка при отправке ответа клиенту")
            return


if __name__ == "__main__":
    # Инициализация веб-сервера, который будет по заданным параметрах в сети
    # принимать запросы и отправлять их на обработку специальному классу, который был описан выше
    logger.info("Server starting at http://%s:%s", HOST, PORT)

    try:
        webServer = HTTPServer((HOST, PORT), MyServer)
    except Exception:
        logger.exception("Не удалось создать сервер. Возможно, порт занят.")
        raise

    try:
        # Cтарт веб-сервера в бесконечном цикле прослушивания входящих запросов
        webServer.serve_forever()

    except KeyboardInterrupt:
        # Корректный способ остановить сервер в консоли через сочетание клавиш Ctrl + C
        logger.info("Остановка сервера по Ctrl+C...")

    except Exception:
        logger.exception("Неожиданная ошибка в работе сервера")
        raise

    finally:
        # Корректная остановка веб-сервера, чтобы он освободил адрес и порт в сети, которые занимал
        webServer.server_close()
        logger.info("Server stopped.")
