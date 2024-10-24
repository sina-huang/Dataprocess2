
class Register:
    def __init__(self):
        self.mapping_dict = None
        self.standard_list_for_fuzzy_match = None
        self.standard_list_for_gpt_ask = None

    def list_for_gpt_ask(self, game_name, league_name):
        """
        将新的比赛名称添加到标准名称列表和 Redis 中。
        """
        # todo 注册到 列表
        data_ = {'gameName': game_name, 'leagueName': league_name}
        self.standard_list_for_gpt_ask.insert(0, data_)
        self.standard_list_for_gpt_ask = self.standard_list_for_gpt_ask[:100]


    def dict_for_mapping(self,game_name,standard_name):
        # todo 注册到映射字典
        self.mapping_dict[game_name] = standard_name

