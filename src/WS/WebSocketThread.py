import threading
import websocket
import time


class WebSocketThread(threading.Thread):
    def __init__(self, url, retry_delay=3, logger=None):
        super().__init__()
        # 使用 get_logger 创建 logger
        self.logger = logger
        self.url = url
        self.retry_delay = retry_delay
        self.ws = None
        self.is_active = True
        self.daemon = True
        self.closed_event = threading.Event()

    def run(self):
        while self.is_active:
            self.closed_event.clear()
            try:
                self.ws = websocket.WebSocketApp(
                    self.url,
                    on_open=self.on_open,
                    on_message=self.on_message if hasattr(self, 'on_message') else None,
                    on_error=self.on_error,
                    on_close=self.on_close
                )
                self.ws.run_forever()
            except Exception as e:
                self.logger.error(f"[连接错误]: {e}")
                if self.ws:
                    self.ws.close()
                    self.ws = None
            finally:
                self.closed_event.wait()
                if self.is_active:
                    self.logger.warning(f"[重试连接] {self.retry_delay} 秒后重试连接")
                    time.sleep(self.retry_delay)

    def on_open(self, ws):
        self.logger.warning("[连接开启] 连接已成功建立")

    def on_error(self, ws, error):
        self.logger.error(f"[连接错误]: WebSocket 遇到错误: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        self.logger.warning(f"[连接关闭]: 状态码: {close_status_code}, 信息: {close_msg}")
        self.closed_event.set()

    def stop(self):
        self.is_active = False
        if self.ws:
            self.ws.close()
        self.closed_event.set()
