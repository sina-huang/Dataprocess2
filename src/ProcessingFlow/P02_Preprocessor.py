import json

from src.ProcessingFlow.BaseProcess import Processor
from src.Utils.Log import get_logger


class DataPreprocessor(Processor):
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
    本类用于数据预处理
    1. 检查数据结构是否完整，是否有空值。
    2. 赔率格式化，将字符串形式的赔率转换为浮点数，如果不能转换则将赔率设置为0
    '''

    def __init__(self, log_name='DataPreprocessor', **kwargs):
        super().__init__(**kwargs)
        self.log_name = log_name or './Log/02数据预处理.log'
        self.logger = get_logger(name=__name__, log_file=self.log_name)

    def process(self, data):
        """
        处理数据。如果通过验证结构检查，就转换赔率并返回数据；否则返回 None。
        """
        try:
            if self.validate_data_structure(data):  # 检查数据结构
                self.force_numeric_outcomes(data)  # 强制转换赔率字段
                # self.logger.warning(data)
                return data  # 验证通过，返回处理后的数据
            else:
                return None  # 验证失败，返回 None
        except Exception as e:
            self.logger.error(f"[管道02-->数据预处理] 处理数据时发生错误: {e}")
            return None  # 发生错误，返回 None

    def validate_data_structure(self, data):
        """
        验证数据是否包含所有必需字段，并且字段不为空。
        """
        missing_fields = []
        empty_fields = []

        for field in DataPreprocessor.required_fields:
            if field not in data:  # 检查是否缺少字段
                missing_fields.append(field)
            elif self.is_empty(data[field]):  # 检查字段是否为空
                empty_fields.append(field)

        if missing_fields or empty_fields:  # 如果有缺失或空字段，记录错误日志
            if missing_fields:
                self.logger.error(f"[管道02-->数据验证] 缺少字段: {', '.join(missing_fields)}")
            if empty_fields:
                self.logger.error(f"[管道02-->数据验证] 字段为空: {', '.join(empty_fields)}")
            return None  # 验证失败，返回 None

        return True  # 验证通过，返回 True

    def is_empty(self, value):
        """
        判断一个值是否为空。
        """
        if value is None:
            return True
        if isinstance(value, str) and not value.strip():
            return True
        if isinstance(value, (list, dict, set, tuple)) and not value:
            return True
        return False

    def force_numeric_outcomes(self, data):
        """
        将赔率字段转换为浮点数，转换失败则设为 0.0 并记录警告日志。
        """
        odds_fields = ['home_team_odds', 'guest_team_odds', 'draw_odds']
        for field in odds_fields:
            try:
                original_value = data[field]
                data[field] = float(data[field])
                self.logger.info(f"[管道02-->赔率转换] 字段 '{field}' 转换成功: '{original_value}' -> {data[field]}")
            except (ValueError, TypeError):
                self.logger.warning(f"[管道02-->赔率转换] 字段 '{field}' 的值 '{data[field]}' 不能转换为 float，设为 0.0")
                data[field] = 0.0
