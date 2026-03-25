import logging
import os
from logging import Logger, LogRecord
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

# Определяю корневую папку проекта.
ROOT_DIR = Path(__file__).resolve().parent.parent
# Прописываю путь к папке logs.
LOG_DIR = ROOT_DIR / "logs"
# Создаю папку и все родительские папки, если их нет.
LOG_DIR.mkdir(exist_ok=True, parents=True)


class SizeAndTimeRotatingFileHandler(TimedRotatingFileHandler):
    """
    Хендлер, который сочетает ротацию по времени и по размеру.

    Он выполняет ротацию в двух случаях:
    1. Когда наступает время ротации (например, каждый день в полночь).
    2. Когда размер файла превышает заданный порог `maxBytes`.
    """

    def __init__(
        self,
        *,
        filename: str,
        when: str = "midnight",
        interval: int = 1,
        backupCount: int = 7,
        maxBytes: int = 100 * 1024 * 1024,
        encoding: str = "utf-8",
    ) -> None:
        """
        Инициализация комбинированного хендлера.

        :param filename: Путь к файлу логов.
        :param when: Период ротации по времени (например, "midnight").
        :param interval: Интервал ротации по времени.
        :param backupCount: Сколько файлов хранить.
        :param maxBytes: Максимальный размер файла в байтах.
        :param encoding: Кодировка файла.
        """

        super().__init__(filename=filename, when=when, interval=interval, backupCount=backupCount, encoding=encoding)
        self.maxBytes = maxBytes

    def shouldRollover(self, record: LogRecord) -> bool:
        """
        Определяет, нужно ли выполнять ротацию файла.

        :param record: Объект класса LogRecord (структура данных, с информацией о лог‑сообщении)
        :return: True — если пора ротировать, False — если нет.
        """

        # 1. Проверка по времени (родительский класс)
        if super().shouldRollover(record):
            return True

        # 2. Проверка по размеру
        if self.stream is not None:
            self.stream.flush()
            current_size = os.stat(self.baseFilename).st_size
            if current_size >= self.maxBytes:
                return True
        return False


def logger_function(*, file_path: str, fmt: str = "%(asctime)s - %(levelname)s - %(name)s - %(message)s") -> Logger:
    """
    Создаёт и настраивает логгер для модуля.

    :param file_path: Путь к модулю
    :param fmt: Форматер для лог-сообщения
    :return: Logger
    """

    # 1. Преобразуем путь к файлу в имя без расширения
    module_name = Path(file_path).stem

    # 2. Создаём логгер
    logger = logging.getLogger(module_name)
    logger.setLevel(logging.DEBUG)

    # 3. Удаляем все хендлеры
    logger.handlers.clear()

    # 4. Создаём форматтер
    formatter = logging.Formatter(fmt)

    # 5. Консольный хендлер
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # 6. Файловый хендлер
    file_handler = SizeAndTimeRotatingFileHandler(
        filename=str(LOG_DIR / f"{module_name}.log"),
        when="midnight",
        interval=1,
        backupCount=7,
        maxBytes=100 * 1024 * 1024,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # 7. Добавления хендлеров
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
