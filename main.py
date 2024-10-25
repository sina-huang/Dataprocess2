import time
from src.Controler import Controller
import threading


if __name__ == "__main__":
    # # todo 传入参数：三个url，GPT的API_KEY，GPT的描述，GPT的模型
    # r = redis.Redis(host='localhost', port=6379, db=0)
    # r.flushdb()

    controller = Controller()
    stop_event = threading.Event()
    try:
        while not stop_event.is_set():
            time.sleep(1)  # 保持主线程活动
    except KeyboardInterrupt:
        print("接收到退出信号，正在停止程序...")
    except Exception as e:
        print(f"程序发生异常：{e}")
    finally:
        controller.stop()
        print("程序已结束")
