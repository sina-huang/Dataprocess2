import json
import time
import queue
import threading
import redis
from cachetools import TTLCache
from settings import REDIS
from settings import url_sender, url_betting, url_receiver
from src.WS.WS_Receiver import Receiver
from src.WS.WebSocketSender import WebSocketSender

from expiringdict import ExpiringDict
from src.Pipeline import Pipeline

from src.Utils.Log import get_logger

from src.ProcessingFlow.P01_WsMessagesParser import WsMessagesParser
from src.ProcessingFlow.P02_Preprocessor import DataPreprocessor
from src.ProcessingFlow.P03_MatchMappingDict import MatchRegistration
from src.ProcessingFlow.P04_MathFuzzy import MatchFuzzy
from src.ProcessingFlow.P05_MatchGPT import MatchGPT
from src.ProcessingFlow.P06_UpdateDicts import UpdateDicts
from src.ProcessingFlow.P07_UpdateOddsDict import UpdateOddsDicts
from src.ProcessingFlow.p09_CalculateOddsLess1_1 import CalculateOddsLess1



logger = get_logger(name=__name__, log_file='./Log/main.log')


class Controller:
    def __init__(self, *args, **kwargs):

        self.input_queue = queue.Queue()
        self.output_queue = queue.Queue()
        self.betting_queue = queue.Queue()
        self.redis_client = redis.Redis(host=REDIS["host"], port=REDIS["port"], db=0, decode_responses=True)

        # todo 初始化线程
        self.processor_thread = None
        self.ws_sender = None
        self.sender_obj = None
        self.receiver_obj = None


        # todo 需要长期维护的变量
        self.mapping_dict = ExpiringDict(max_len=500, max_age_seconds=4 * 60 * 60)

        self.standard_list_for_gpt_ask = []
        self.standard_list_for_fuzzy_match = []
        self.aggregated_platform_dict = TTLCache(maxsize=500, ttl=4 * 60 * 60)
        self.aggregated_max_odds_dict = TTLCache(maxsize=500, ttl=4 * 60 * 60)

        # todo 初始化管道
        self.pipeline = Pipeline(mapping_dict=self.mapping_dict,
                                 standard_list_for_gpt_ask=self.standard_list_for_gpt_ask,
                                 standard_list_for_fuzzy_match=self.standard_list_for_fuzzy_match,
                                 aggregated_platform_dict=self.aggregated_platform_dict,
                                 aggregated_max_odds_dict=self.aggregated_max_odds_dict,
                                 output_queue=self.output_queue,
                                 betting_queue=self.betting_queue,
                                )  # 管道
        self.pipeline.add_processor(WsMessagesParser, log_name='./Log/测试/01解析ws消息.log')
        self.pipeline.add_processor(DataPreprocessor, log_name='./Log/测试/02数据预处理.log')
        self.pipeline.add_processor(MatchRegistration, log_name='./Log/测试/03匹配注册表.log')
        self.pipeline.add_processor(MatchFuzzy, log_name='./Log/测试/04模糊匹配.log')
        self.pipeline.add_processor(MatchGPT, log_name='./Log/测试/05gpt匹配.log')
        self.pipeline.add_processor(UpdateDicts, log_name='./Log/测试/06更新字典.log')
        self.pipeline.add_processor(UpdateOddsDicts,log_name='./Log/测试/07更新赔率字典.log')
        # self.pipeline.add_processor(CalculateOddsLess1, log_name='./Log/测试/08计算赔率小于1.log')
        self.pipeline.add_processor(CalculateOddsLess1, log_name='./Log/测试/09计算赔率小于1.log')  # 新添加的处理器



        self.initialize_threads()
    def initialize_threads(self):
        # todo Receiver--开启线程（ws接收者）
        self.receiver_obj = Receiver(url=url_receiver, input_queue=self.input_queue, log_file_name="./Log/Receiver.log")
        self.receiver_obj.start()
        logger.info("[进程开启] [01-- 接收者线程启动成功]")

        # todo Sender--开启线程（ws发送者）
        self.sender_obj = WebSocketSender(url=url_sender, output_queue=self.output_queue, log_file_name="./Log/Sender.log")
        self.sender_obj.start()
        logger.info("[进程开启] [02-- 发送者线程启动成功]")

        # todo Betting--开启线程（ws下单者）
        self.ws_sender = WebSocketSender(url=url_betting, output_queue=self.betting_queue, log_file_name="./Log/Betting.log")
        self.ws_sender.start()
        logger.info("[进程开启] [03-- 下单者线程启动成功]")

        # todo Processor--开启线程（process处理者），程序正式开始执行
        self.processor_thread = threading.Thread(
            target=self.process_data,
            daemon=True
        )
        self.processor_thread.start()
        logger.info("[进程开启] [04-- 数据加工线程启动成功]")

    def process_data(self):

        while True:
            # todo --[step-1]--提取数据

            try:
                message_str = self.input_queue.get(timeout=1)
            except queue.Empty:
                logger.debug(f"[ 接收者队列为空 ]")
                continue

            # todo --[step-2]-- 使用管道处理数据
            processed_data = self.pipeline.process(message_str)
            if processed_data is None:
                # 数据处理失败，丢弃该数据
                self.input_queue.task_done()
                continue
            self.input_queue.task_done()






    def update_platform_dict(self, spider_data_dict):
        home_odds, draw_odds, away_odds = spider_data_dict['home_team_name'], spider_data_dict['draw_odds'], spider_data_dict['guest_team_name']
        standard_name = spider_data_dict['standard_name']
        platform = spider_data_dict['Platform']
        original_game_name = spider_data_dict.get('game_name', '未知比赛名')

        if standard_name not in self.aggregated_platform_dict:
            self.aggregated_platform_dict[standard_name] = {}

        ''' input_queue
        required_fields = {
        "Platform": str,
        "league_name": str,
        "game_name": str,
        "home_team_name": str,
        "guest_team_name": str,  # 修正字段名称
        'home_team_odds': (int, float, str),
        'guest_team_odds': (int, float, str),
        'draw_odds': (int, float, str),
    }
        '''
        self.aggregated_platform_dict[standard_name][platform] = {
            'from': platform,
            'home_odds': home_odds,
            'draw_odds': draw_odds,
            'away_odds': away_odds,
            'original_game_name': original_game_name,
            'standardName': standard_name,
            'home_team_name': spider_data_dict['home_team_name'],
            'guest_team_name': spider_data_dict['guest_team_name'],
        }

    def update_odds_dict(self, spider_data_dict):
        standard_name = spider_data_dict['standardName']
        if standard_name not in self.aggregated_max_odds_dict:
            return
        # 只将一场比赛的赔率信息提取出来，也就是当前需要分析的这场比赛。
        match_odds = self.aggregated_max_odds_dict[standard_name]

        # 继续执行，更新 self.max_odds_dict

        max_home_odds = {'odds': 0, 'from': None, 'original_game_name': None}
        max_draw_odds = {'odds': 0, 'from': None, 'original_game_name': None}
        max_away_odds = {'odds': 0, 'from': None, 'original_game_name': None}

        for platform, game_info_dict in match_odds.items():
            if game_info_dict['home_odds'] >= max_home_odds['odds']:
                max_home_odds = {
                    'odds': game_info_dict['home_odds'],
                    'from': platform,
                    'original_game_name': game_info_dict['original_game_name']
                }
            if game_info_dict['draw_odds'] >= max_draw_odds['odds']:
                max_draw_odds = {
                    'odds': game_info_dict['draw_odds'],
                    'from': platform,
                    'original_game_name': game_info_dict['original_game_name']
                }
            if game_info_dict['away_odds'] >= max_away_odds['odds']:
                max_away_odds = {
                    'odds': game_info_dict['away_odds'],
                    'from': platform,
                    'original_game_name': game_info_dict['original_game_name']
                }

        self.aggregated_max_odds_dict[standard_name] = {
            'home_max_odds': max_home_odds,
            'draw_max_odds': max_draw_odds,
            'away_max_odds': max_away_odds
        }

    def check_redis(self, hash_key):
        """
        从 Redis 中获取标准名称。
        :param hash_key: Redis 中的键
        :return: 标准名称或 None
        """
        try:
            standard_name = self.redis.get(hash_key)
            if standard_name:
                if isinstance(standard_name, bytes):
                    return standard_name.decode('utf-8')  # 如果是 bytes，解码为字符串
                return standard_name  # 如果已经是 str 类型，直接返回
            return None
        except Exception as e:
            return None

    def register_to_list(self, gameName,leagueName):
        """
        将新的比赛名称添加到标准名称列表和 Redis 中。
        """
        # todo 注册到 列表
        data_= {'gameName':gameName,'league':leagueName}
        self.standard_name_list.insert(0, data_)
        self.standard_name_list = self.standard_name_list[:50]
        self.standard_name_list = list(dict.fromkeys(self.standard_name_list))

    def register_to_redis(self, game_name, hash_key):
        # todo 注册到 Redis
        self.redis.set(hash_key, game_name)
        self.redis.expire(hash_key, 3600 * 4)

    def calculate_inverse_sum(self, standard_name):
        def get_odds_value(odds_data):
            odds = odds_data.get('odds', 0)
            return odds if odds > 0 else float('inf')

        max_odds = self.aggregated_max_odds_dict.get(standard_name, {})
        max_home_odds = get_odds_value(max_odds.get('home_max_odds', {}))
        max_draw_odds = get_odds_value(max_odds.get('draw_max_odds', {}))
        max_away_odds = get_odds_value(max_odds.get('away_max_odds', {}))

        return 1 / max_home_odds + 1 / max_draw_odds + 1 / max_away_odds

    def initialize_standard_name(self, game_name, league_name, spider_data_dict):
        # 初始化标准名称列表
        logger.info(f"[标准名列表初始化]")
        self.register_to_list(game_name, league_name)
        self.register_to_redis(game_name, f"hash:{game_name}")
        standard_name = game_name
        spider_data_dict['standardName'] = standard_name
        return spider_data_dict

    def get_standard_name_from_redis(self, hash_key, spider_data_dict):
        # 从 Redis 中查找标准名称
        if standard_name := self.check_redis(hash_key):
            logger.info(f'[Redis 匹配成功] -- {standard_name}')
            spider_data_dict["standardName"] = standard_name
            return spider_data_dict
        return None

    def stop(self):
        # 停止各个线程
        if self.receiver_obj:
            self.receiver_obj.stop()
        if self.sender_obj:
            self.sender_obj.stop()
        if self.ws_sender:
            self.ws_sender.stop()
        if self.processor_thread:
            # 设置标志位或通过其他方式停止线程
            pass  # 根据具体实现
