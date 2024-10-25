# Log.py

import logging
import sys
import time
import logging
from logging.handlers import RotatingFileHandler  # 确保从 logging.handlers 导入
"""
Logger: 日志记录器，可以设置日志级别，过滤器，处理器等
Handler: 日志处理器,将logger创建的日志分发到不同的目标 ，这里可以单独设置日志级别
Formatter: 日志格式化器，定义日志的输出格式
Level: 日志级别，定义了日志的输出级别，DEBUG < INFO < WARNING < ERROR < CRITICAL
"""

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


def get_logger(name, log_file,
               level=logging.INFO,
               console_level=logging.WARNING,
               file_mode='w',
               deduplicate=False):
    """
    获取日志器

    :param deduplicate: 是否启用日志去重功能，默认 False
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        # 创建文件处理器
        file_handler = RotatingFileHandler(log_file, mode=file_mode, encoding='utf-8')
        file_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # 创建控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(console_level)
        console_formatter = logging.Formatter(
            '[%(levelname)s] [%(name)s] %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # 添加去重过滤器（如果启用）
        if deduplicate:
            dedup_filter = DeduplicationFilter(deduplicate=True)
            logger.addFilter(dedup_filter)

        # 防止日志传播到父日志器，避免重复
        logger.propagate = False

    return logger

if __name__ == '__main__':
    logger = get_logger(
        name='my_logger',
        log_file='test_log.log',
        level=logging.DEBUG,  # 设置日志记录器的日志级别
        console_level=logging.INFO,  # 控制台输出日志的级别
        file_mode='w',  # 重写文件
        deduplicate=True  # 启用日志去重功能
    )


    # 创建一些测试数据
    def test_logging():
        # 测试输出各种级别的日志，包含重复内容
        logger.debug('这是 DEBUG 级别日志')
        logger.info('这是 INFO 级别日志')
        logger.warning('这是 WARNING 级别日志')
        logger.error('这是 ERROR 级别日志')
        logger.critical('这是 CRITICAL 级别日志')

        # 再次记录相同的日志来测试去重功能
        logger.debug('这是 DEBUG 级别日志')  # 应该被过滤掉
        logger.info('这是 INFO 级别日志')  # 应该被过滤掉
        logger.warning('这是 WARNING 级别日志')  # 应该被过滤掉
        logger.error('这是 ERROR 级别日志')  # 应该被过滤掉
        logger.critical('这是 CRITICAL 级别日志')  # 应该被过滤掉

        # 记录一些不同的日志信息
        logger.info('新的 INFO 日志消息')
        logger.error('不同的 ERROR 日志消息')

        # 延迟记录日志以模拟实际情况
        time.sleep(1)
        logger.info('另一个 INFO 日志消息')


    if __name__ == "__main__":
        test_logging()