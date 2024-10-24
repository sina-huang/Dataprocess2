from src.Utils.Log import get_logger
from src.WS.WebSocketThread import WebSocketThread

class Receiver(WebSocketThread):
    def __init__(self, url, input_queue,log_file_name=None):
        # 动态生成日志文件名，例如 "Receiver.log"
        self.log_file_name = log_file_name or f'./Log/{self.__class__.__name__}.log'
        self.logger = get_logger(name=__name__, log_file=self.log_file_name)

        # 调用父类初始化，并传递 logger
        super().__init__(url, logger=self.logger)

        # 初始化输入队列
        self.input_queue = input_queue

    def on_message(self, ws, message):
        self.logger.info(f"[收到消息]：{message}")
        self.input_queue.put(message)