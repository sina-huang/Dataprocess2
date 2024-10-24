from src.Utils.Log import get_logger
from src.WS.WebSocketThread import WebSocketThread
import threading
import queue
import json
import time

class WebSocketSender(WebSocketThread):
    def __init__(self, url, output_queue, log_file_name="Sender"):
        # 保存实例名称
        self.log_file_name = log_file_name or f'./Log/{self.__class__.__name__}.log'
        self.logger = get_logger(name=__name__, log_file=self.log_file_name)

        # 调用父类初始化，并传递 logger
        super().__init__(url, logger=self.logger)

        # 初始化输出队列
        self.output_queue = output_queue

        # 初始化发送线程
        self.sender_thread = threading.Thread(target=self.send_messages)
        self.sender_thread.daemon = True
        self.sender_thread.start()

    def send_messages(self):
        while self.is_active:
            if self.ws:
                try:
                    message = self.output_queue.get(timeout=1)
                    if isinstance(message, dict):
                        message = json.dumps(message, ensure_ascii=False)
                    self.ws.send(message)
                    self.logger.info(f"[{self.name} 发送消息]：{message}")
                    self.output_queue.task_done()
                except queue.Empty:
                    continue
                except Exception as e:
                    self.logger.error(f"[{self.name} 发送消息失败]：{e}")
                    time.sleep(1)
            else:
                time.sleep(0.1)  # 等待连接建立
