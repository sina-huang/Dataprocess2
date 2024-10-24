import time
from src.Controler import Controller
import redis


if __name__ == "__main__":
    # todo 传入参数：三个url，GPT的API_KEY，GPT的描述，GPT的模型
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.flushdb()

    controller = Controller()

    try:
        while True:
            time.sleep(1)  # 保持主线程活动
    except KeyboardInterrupt:
        controller.stop()
        print("程序结束")
