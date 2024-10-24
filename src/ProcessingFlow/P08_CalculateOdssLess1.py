import json
from src.ProcessingFlow.BaseProcess import Processor
from src.Utils.Log import get_logger
import time

class CalculateOddsLess1(Processor):

    sample_of_odds_dict ={
        'Malki SC -- Sohryngkham SC':{
            "home_max_odds": {
                "odds": 2.85,
                "Platform": "Rollbit",
                "game_name": "Malki SC -- Sohryngkham SC",
                "standard_name": "Malki SC -- Sohryngkham SC"
            },
            "draw_max_odds": {
                "odds": 2.1,
                "Platform": "Rollbit",
                "game_name": "Malki SC -- Sohryngkham SC",
                "standard_name": "Malki SC -- Sohryngkham SC"
            },
            "away_max_odds": {
                "odds": 3.75,
                "Platform": "Rollbit",
                "game_name": "Malki SC -- Sohryngkham SC",
                "standard_name": "Malki SC -- Sohryngkham SC"
            },
            "total_odds": 1.093734335839599
        },
        'Gil Vicente FC -- Leixoes SC':{
            "home_max_odds": {
                "odds": 1.45,
                "Platform": "Rollbit",
                "game_name": "Gil Vicente FC -- Leixoes SC",
                "standard_name": "Gil Vicente FC -- Leixoes SC"
            },
            "draw_max_odds": {
                "odds": 4.05,
                "Platform": "Rollbit",
                "game_name": "Gil Vicente FC -- Leixoes SC",
                "standard_name": "Gil Vicente FC -- Leixoes SC"
            },
            "away_max_odds": {
                "odds": 6.25,
                "Platform": "Rollbit",
                "game_name": "Gil Vicente FC -- Leixoes SC",
                "standard_name": "Gil Vicente FC -- Leixoes SC"
            },
            "total_odds": 1.0965687526607066
        }
    }


    def __init__(self, log_name='CalculateOddsLess1',**kwargs):
        super().__init__(**kwargs)
        self.log_name = log_name or './Log/CalculateOddsLess1.log'
        self.logger = get_logger(name=__name__, log_file=self.log_name)

        self.odds_tracking = {}

    def process(self, data):
        self.calculate_odds_less_than_1()

        return None

    def calculate_odds_less_than_1(self):
        for standard_name, odds_info in self.aggregated_max_odds_dict.items():
            if standard_name not in self.odds_tracking:
                self.odds_tracking[standard_name] = {
                    "tracking": False,
                    "start_time": None,
                    "last_below_odds": None,
                    "events": []
                }

            total_odds = odds_info.get("total_odds")
            if total_odds is None or total_odds ==0:
                continue

            # 获取当前比赛的跟踪状态
            game_tracking = self.odds_tracking[standard_name]

            # 如果total_odds小于1并且没有开始追踪，则开始记录
            if total_odds < 1 and not game_tracking["tracking"]:
                game_tracking["tracking"] = True
                game_tracking["start_time"] = time.time()
                game_tracking["last_below_odds"] = total_odds
                game_tracking["events"].append({
                    "event": "start_tracking",
                    "total_odds": total_odds,
                    "time": game_tracking["start_time"]
                })
                # self.logger.info(f"开始追踪比赛:[{standard_name}], 当前赔率: [{total_odds}]")


            # 如果total_odds大于或等于1并且正在追踪，则停止记录
            elif total_odds >= 1 and game_tracking["tracking"]:
                game_tracking["tracking"] = False
                end_time = time.time()
                game_tracking["events"].append({
                    "event": "stop_tracking",
                    "total_odds": game_tracking["last_below_odds"],
                    "start_time": game_tracking["start_time"],
                    "end_time": end_time,
                    "duration": end_time - game_tracking["start_time"]
                })
                game_tracking["start_time"] = None
                game_tracking["last_below_odds"] = None
                self.log_tracking_results()

    def log_tracking_results(self):
        for game, tracking_info in self.odds_tracking.items():
            for record in tracking_info["events"]:

                duration = record.get('duration', 'N/A')
                if not isinstance(duration, (int, float)):
                    try:
                        duration = float(duration)
                    except (ValueError, TypeError):
                        duration = 0

                if duration > 1 and record['total_odds'] > 0.5:
                    self.logger.info(
                        f"比赛:[{game}] 赔率: [{record['total_odds']}], 持续时间[{duration} 秒]")

    def print_tracking_results(self):
        for game, tracking_info in self.odds_tracking.items():
            for record in tracking_info["events"]:
                print(
                    f"Game: {game}, Event: {record['event']}, Total Odds: {record['total_odds']}, Duration: {record.get('duration', 'N/A')} seconds")