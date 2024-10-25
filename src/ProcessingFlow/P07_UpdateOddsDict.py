import json
from src.ProcessingFlow.BaseProcess import Processor
from src.Utils.Log import get_logger

class UpdateOddsDicts(Processor):
    required_fields = {
        "Platform": str,
        "league_name": str,
        "game_name": str,
        "home_team_name": str,
        "guest_team_name": str,
        'home_team_odds': (int, float, str),
        'guest_team_odds': (int, float, str),
        'draw_odds': (int, float, str),
        'standard_name': str, # 新增字段,一定会有
        'standard_name_list_for_gpt_request':list,
        # 也有可能没有standard_name_list_for_gpt_request字段
        'match_channels': str, #新增字段,一定会有
    }
    sample_of_standard_list_for_gpt_ask =[
        {'standard_name1': str, 'league_name1': str},
        {'standard_name2': str, 'league_name2': str},
        ...
    ]
    sample_of_mapping_dict = {
        'game_name_from_platform1': 'standard_name1',
        'game_name_from_platform2': 'standard_name2',
        # 添加更多的平台名称映射到标准名称
        # 这里显然是多对一的映射关系
    }
    # 样例聚合后的数据字典
    # 结构 为三层，[第一层--为标准名称]，[第二层--平台名称]，[第三层--为具体的数据字段]
    sample_of_aggregated_platform_dict = {
        'standard_name1': {
            'Stake': {
                'platform': str,
                'home_odds': float,
                'draw_odds': float,
                'away_odds': float,
                'game_name': str,
                'standard_name': str,
                'home_team_name': str,
                'guest_team_name': str,
            },
            'Rollbit': {
                'platform': str,
                'home_odds': float,
                'draw_odds': float,
                'away_odds': float,
                'game_name': str,
                'standard_name': str,
                'home_team_name': str,
                'guest_team_name': str,
            },
            # '更多平台'
        },
        'standard_name2': {
            'Stake': {
                'platform': str,
                'home_odds': float,
                'draw_odds': float,
                'away_odds': float,
                'original_game_name': str,
                'standardName': str,
                'home_team_name': str,
                'guest_team_name': str,
            },
            'Rollbit': {
                'platform': str,
                'home_odds': float,
                'draw_odds': float,
                'away_odds': float,
                'original_game_name': str,
                'standardName': str,
                'home_team_name': str,
                'guest_team_name': str,
            },
            # '更多平台'
        },
        'standard_name3':{
            'Stake':{}  # 只有一个平台
        }
    }
    sample_of_odds_dict ={
        'Feren23123 TC -- OGC Nice':{
            'home_max_odds': {
                        'odds': 2.3,
                        'Platform': 'Stake',
                        'game_name': 'Feren23123 TC -- OGC Nice',
                        'standard_name': 'FerenTC -- OGC Nice'
                    } ,
            'draw_max_odds': {
                'odds': 2.3,
                'Platform': 'Stake',
                'game_name': 'Feren23123 TC -- OGC Nice',
                'standard_name': 'FerenTC -- OGC Nice'
            },
            'away_max_odds': { 'odds': 2.3,
                        'Platform': 'Stake',
                        'game_name': 'Feren23123 TC -- OGC Nice',
                        'standard_name': 'FerenTC -- OGC Nice'},
            'total_odds': 1.2
        },
        'Eintracht  -- FK Rigas': {
            'home_max_odds': {
                'odds': 2.3,
                'Platform': 'Stake',
                'game_name': 'Eintracht  -- FK Rigas',
                'standard_name': 'Eintracht  -- FK Rigas'
            },
            'draw_max_odds': {
                'odds': 2.3,
                'Platform': 'Stake',
                'game_name': 'Eintracht  -- FK Rigas',
                'standard_name': 'Eintracht  -- FK Rigas'
            },
            'away_max_odds': {'odds': 2.3,
                              'Platform': 'Stake',
                              'game_name': 'Eintracht  -- FK Rigas',
                              'standard_name': 'Eintracht  -- FK Rigas'},
            'total_odds': 0.78
        }
    }



    def __init__(self, log_name='UpdateOddsDicts',**kwargs):
        super().__init__(**kwargs)
        self.log_name = log_name or './Log/UpdateOddsDicts.log'
        self.logger = get_logger(name=__name__, log_file=self.log_name)


    def process(self, data):
        self.update_odds_dict(data)
        return data


    def update_odds_dict(self, spider_data_dict):
        standard_name = spider_data_dict['standard_name']

        if standard_name not in self.aggregated_platform_dict:
            self.logger.info(f'标准名不在聚合字典中，添加新的标准名: {standard_name}')
            return None

        """
        one_odds_dict =  {
            'Stake': {
                'platform': str,
                'home_odds': float,
                ...
            },
            'Rollbit': {
                ...
            },
            # '更多平台'
        }
        它就是单纯的从aggregated_max_odds_dict 提取第一层的某一条记录
        """
        one_odds_dict = self.aggregated_platform_dict[standard_name]
        # self.logger.info(one_odds_dict)
        # self.logger.info(f"{json.dumps(one_odds_dict, ensure_ascii=False,indent=4)}")
        if len(one_odds_dict) == 1:
            return None

        if len(one_odds_dict) > 1:
            total_odds = 0
            max_home_odds = {'odds': 0, 'Platform': None, 'game_name': None,'standard_name': None}
            max_draw_odds = {'odds': 0, 'Platform': None, 'game_name': None,'standard_name': None}
            max_away_odds = {'odds': 0, 'Platform': None, 'game_name': None,'standard_name': None}
            for platform, game_info_dict in one_odds_dict.items():
                # self.logger.info(f"{json.dumps(game_info_dict,indent=4, ensure_ascii=False)}")
                if game_info_dict['home_team_odds'] > max_home_odds['odds']:
                    max_home_odds = {
                        'odds': game_info_dict['home_team_odds'],
                        'Platform': platform,
                        'game_name': game_info_dict['game_name'],
                        'standard_name':standard_name
                    }
                if game_info_dict['draw_odds'] > max_draw_odds['odds']:
                    max_draw_odds = {
                        'odds': game_info_dict['draw_odds'],
                        'Platform': platform,
                        'game_name': game_info_dict['game_name'],
                        'standard_name':standard_name
                    }
                if game_info_dict['guest_team_odds'] > max_away_odds['odds']:
                    max_away_odds = {
                        'odds': game_info_dict['guest_team_odds'],
                        'Platform': platform,
                        'game_name': game_info_dict['game_name'],
                        'standard_name':standard_name
                    }
            if all(odds['odds'] > 0 for odds in [max_home_odds, max_draw_odds, max_away_odds]):
                total_odds = sum(1 / odds['odds'] for odds in [max_home_odds, max_draw_odds, max_away_odds])
                self.aggregated_max_odds_dict[standard_name] = {
                    'home_max_odds': max_home_odds,
                    'draw_max_odds': max_draw_odds,
                    'away_max_odds': max_away_odds,
                    'total_odds': total_odds
                }


                if 0 < total_odds < 1:
                    self.betting_queue.put(self.aggregated_max_odds_dict[standard_name])
                    self.logger.warning(
                        f"发现套利机会：{json.dumps(self.aggregated_max_odds_dict[standard_name], indent=4, ensure_ascii=False)}")
            else:
                self.logger.debug(f"标准名称{standard_name}的赔率存在零或负数，无法计算total_odds。")

            self.logger.debug(f"计算标准名称{standard_name}的赔率：{self.aggregated_max_odds_dict.get(standard_name)}")
