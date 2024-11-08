from src.ProcessingFlow.BaseProcess import Processor
from src.Utils.Log import get_logger


class MatchRegistration(Processor):
    '''
       本类用于 新来的比赛 去标准列表映射表中 查找标准名称。
    '''
    # 爬虫数据结构
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
    # todo'   key-比赛名，value-标准名
    _mapping_dict = {
        'Feren TC -- OGC Nice': 'Feren23123 TC -- OGC Nice',
        'Eintracht  -- FK Rigas': 'Eintracht -- FK Rigas',
        'Ferencvarosi TC -- OGC Nice': 'Ferencvarosi TC -- OGC Nice',
        'key-比赛名': 'value-标准名',
    }

    # todo [{},{},{},{}] 这样的结构
    _standard_list_for_gpt_ask = [
        {'standard_name': str, 'league_name': str},
        {'standard_name': str, 'league_name': str},
        {'standard_name': str, 'league_name': str},
        ...
    ]

    def __init__(self, log_name='Preprocessor', **kwargs):
        super().__init__(**kwargs)
        self.log_name = log_name or './Log/03_1_在映射表中查找.log'
        self.logger = get_logger(name=__name__, log_file=self.log_name)

    def process(self, data):
        game_name = data['game_name']
        league_name = data['league_name']

        if not self.mapping_dict:
            # mapping_dict 为空
            data_ = {'standard_name': game_name, 'league_name': league_name}
            # 注册到映射表中，注册到标准列表中
            self.standard_list_for_gpt_ask.insert(0, data_)
            self.mapping_dict[game_name] = game_name
            data['standard_name'] = game_name
            return data

        if self.mapping_dict.get(game_name):
            # 在映射表中找到对应的标准名称
            data['standard_name'] = self.mapping_dict[game_name]
            return data

        return data
