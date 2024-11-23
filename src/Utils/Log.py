import logging
import sys
import time
from logging.handlers import RotatingFileHandler

class DeduplicationFilter(logging.Filter):
    def __init__(self, deduplicate=True, max_entries=1000):
        super().__init__()
        self.deduplicate = deduplicate
        self.logged_messages = set()
        self.max_entries = max_entries

    def filter(self, record):
        if not self.deduplicate:
            return True

        log_entry = (record.levelno, record.getMessage())
        if log_entry in self.logged_messages:
            return False
        else:
            self.logged_messages.add(log_entry)
            # 限制集合大小
            if len(self.logged_messages) > self.max_entries:
                self.logged_messages.pop()
            return True

def get_logger(name='main_logger', log_file='./Log/main.log',
               level=logging.WARNING,
               console_level=logging.WARNING,
               file_mode='a',
               deduplicate=False):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 清除已有的处理器，防止重复
    if logger.hasHandlers():
        logger.handlers.clear()

    # 创建文件处理器，设置 maxBytes=15MB，backupCount=1 表示保留一个备份
    file_handler = RotatingFileHandler(
        log_file, mode=file_mode, maxBytes=15 * 1024 * 1024, backupCount=1, encoding='utf-8')
    file_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # 添加去重过滤器（如果启用）
    if deduplicate:
        dedup_filter = DeduplicationFilter(deduplicate=True)
        logger.addFilter(dedup_filter)

    logger.propagate = False

    return logger
