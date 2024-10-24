class Pipeline:
    def __init__(self, mapping_dict, standard_list_for_gpt_ask, standard_list_for_fuzzy_match, aggregated_platform_dict,
                 aggregated_max_odds_dict):
        # 保存共享参数
        self.mapping_dict = mapping_dict
        self.standard_list_for_gpt_ask = standard_list_for_gpt_ask
        self.standard_list_for_fuzzy_match = standard_list_for_fuzzy_match
        self.aggregated_platform_dict = aggregated_platform_dict
        self.aggregated_max_odds_dict = aggregated_max_odds_dict
        self.processors = []

    def add_processor(self, processor_cls, **kwargs):
        # 实例化处理器时自动注入共享参数
        processor = processor_cls(
            mapping_dict=self.mapping_dict,
            standard_list_for_gpt_ask=self.standard_list_for_gpt_ask,
            standard_list_for_fuzzy_match=self.standard_list_for_fuzzy_match,
            aggregated_platform_dict=self.aggregated_platform_dict,
            aggregated_max_odds_dict=self.aggregated_max_odds_dict,
            **kwargs
        )
        self.processors.append(processor)

    def process(self, data):
        for processor in self.processors:
            if data is None:
                return None
            data = processor.process(data)
        return data
