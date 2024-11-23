from src.Utils.Log import get_logger
from src.WS.WebSocketThread import WebSocketThread
import queue
class Receiver(WebSocketThread):
    Num = 0
    def __init__(self, url, input_queue,log_file_name=None):
        # 动态生成日志文件名，例如 "Receiver.log"
        self.log_file_name = log_file_name or f'./Log/{self.__class__.__name__}.log'
        self.logger = get_logger(name=__name__, log_file=self.log_file_name)
        self.num = 0
        # 调用父类初始化，并传递 logger
        super().__init__(url, logger=self.logger)

        # 初始化输入队列
        self.input_queue = input_queue

    def on_message(self, ws, message):
        # self.logger.info(f"[收到消息]：{message}")
        # print(f"[收到消息]：{message}")
        self.num += 1
        if self.num % 100 == 0 or self.num == 1:
            print(f"[收到消息]：第 {self.num} 条消息，程序正在运行中...")
        self.input_queue.put(message)

        try:
            self.input_queue.put(message, timeout=1)
        except queue.Full:
            # self.logger.warning("[接收队列已满] 丢弃消息")
            pass