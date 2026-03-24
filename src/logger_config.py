import logging
from logging import Logger
from pathlib import Path


def logger_function(
    *, file_path: str, fmt: str = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
) -> Logger:
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

    # Удаляем все хендлеры, которые могли быть добавлены PyCharm
    logger.handlers.clear()

    # 3. Создаём форматтер
    formatter = logging.Formatter(fmt)

    # 4. Консольный хендлер
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # 5. Файловый хендлер
    file_handler = logging.FileHandler(f"{module_name}.log", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # 6. Добавления хендлеров
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
