import json

from src.ProcessingFlow.BaseProcess import Processor
from src.Utils.Log import get_logger

class UpdateDicts(Processor):
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
        }
    }


    def __init__(self, log_name='MathFuzzy',**kwargs):
        super().__init__(**kwargs)
        self.log_name = log_name or './Log/MathFuzzy.log'
        self.logger = get_logger(name=__name__, log_file=self.log_name)


    def process(self, data):
        standard_name = data.get('standard_name')
        is_new_entry = False

        if standard_name not in self.aggregated_platform_dict:
            self.aggregated_platform_dict[standard_name] = {}
            is_new_entry = True

        # 检查 Platform 是否是新的（对于现有的 standard_name）
        if data['Platform'] not in self.aggregated_platform_dict[standard_name]:
            is_new_entry = True

        if 'standard_name_list_for_gpt_request' in data:
            del data['standard_name_list_for_gpt_request']

        if data['standard_name'] == data['game_name']:
            data['match_channels'] = '精确匹配'
        else:
            data['match_channels'] = 'GPT匹配'
        # 更新聚合字典
        self.aggregated_platform_dict[standard_name][data['Platform']] = data

        # 仅在有新增项目时打印日志
        if is_new_entry:
            self.logger.info(
                f"[聚合字典更新成功] {json.dumps(self.aggregated_platform_dict, ensure_ascii=False, indent=4)}")
        self.summary_from_dict(is_new_entry)
        return data

    def summary_from_dict(self,is_new_entry):
        filtered_result = {}
        for standard_name, platforms in self.aggregated_platform_dict.items():
            # 提取第一层
            # if len(platforms) > 1:
            #     for platform_name, platform_info in platforms.items():
            #         print(f"平台: {platform_name}, 信息: {platform_info}")  # 插入打印语句查看信息

            filtered_result[standard_name] = {

                platform_name: {
                    'game_name': platform_info['game_name'],
                    'standard_name': platform_info['standard_name'],
                    'match_channels': platform_info['match_channels']
                }
                for platform_name, platform_info in platforms.items()
            }
            if len(platforms) == 1:
                pass
        if is_new_entry:
            self.logger.info(f"[聚合字典汇总结果] [匹配成功{len(filtered_result)}] 具体数据： {json.dumps(filtered_result, ensure_ascii=False,indent=4)}")
            self.logger.warning(
                f"[聚合字典汇总结果] [共找到匹对成功的比赛有： {len(filtered_result)} 场] ")

