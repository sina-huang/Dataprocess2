import json

from src.ProcessingFlow.BaseProcess import Processor
from src.Utils.Log import get_logger
from rapidfuzz import process


class MatchFuzzy(Processor):
    required_fields = {
        "Platform": str,
        "league_name": str,
        "game_name": str,
        "home_team_name": str,
        "guest_team_name": str,  # 修正字段名称
        'home_team_odds': (int, float, str),
        'guest_team_odds': (int, float, str),
        'draw_odds': (int, float, str),
        'standard_name': str,
        # 也有可能没有standard_name字段
    }
    sample_of_standard_list_for_gpt_ask =[
        {'gameName': str, 'leagueName': str},
        {'gameName': str, 'leagueName': str},
        ...
    ]
    sample_of_mapping_dict = {
        'game_name_from_platform1': 'standard_name1',
        'game_name_from_platform2': 'standard_name2',
        # 添加更多的平台名称映射到标准名称
        # 这里显然是多对一的映射关系
    }

    def __init__(self, log_name='MathFuzzy',**kwargs):
        super().__init__(**kwargs)
        self.log_name = log_name or './Log/MathFuzzy.log'
        self.logger = get_logger(name=__name__, log_file=self.log_name)

    def process(self, data):
        if 'standard_name' in data and data['standard_name']:
            return data

        # 如果不存在 'standard_name' 字段，说明上一步没有匹配到数据
        # 这里的逻辑是，在标准名称列表中找到最接近的5项，挂载到data上，以供后续步骤使用
        match_data = self.find_top_matches(game_name=data['game_name'])
        data['standard_name_list_for_gpt_request'] = match_data
        return data

    def find_top_matches(self, game_name):
        # 在标准名称列表中找到最接近的5项
        game_names = [item['standard_name'] for item in self.standard_list_for_gpt_ask]

        # 使用 rapidfuzz 提取前 5 个最匹配的 gameName
        matches = process.extract(game_name, game_names, limit=5)

        filtered_matches = [(match_name, score) for match_name, score, _ in matches if score >= 60]

        # 打印 game_name
        self.logger.info(f"正在查找与 \"{game_name}\" 最匹配的标准名称：")
        # 打印匹配结果，添加层次感
        if filtered_matches:
            self.logger.info("匹配结果（得分 >= 60%）：")
            for i, (match_name, score) in enumerate(filtered_matches, 1):
                self.logger.info(f"  匹配 {i}:")
                self.logger.info(f"    - 标准名称: {match_name}")
                self.logger.info(f"    - 匹配得分: {score:.2f}")
        else:
            self.logger.info("没有找到得分 >= 60% 的匹配项。")

        # 找到匹配的标准名称对应的完整字典
        matched_results = []
        for match_name, score in filtered_matches:
            for item in self.standard_list_for_gpt_ask:
                if item['standard_name'] == match_name:
                    matched_results.append(item)
                    break

        return matched_results