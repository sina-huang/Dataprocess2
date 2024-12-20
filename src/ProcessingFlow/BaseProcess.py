class Processor:
    def __init__(self, mapping_dict, standard_list_for_gpt_ask, standard_list_for_fuzzy_match, aggregated_platform_dict,
                 aggregated_max_odds_dict,betting_queue,output_queue):
        self.mapping_dict = mapping_dict
        self.standard_list_for_gpt_ask = standard_list_for_gpt_ask
        self.standard_list_for_fuzzy_match = standard_list_for_fuzzy_match
        self.aggregated_platform_dict = aggregated_platform_dict
        self.aggregated_max_odds_dict = aggregated_max_odds_dict
        self.output_queue = output_queue
        self.betting_queue = betting_queue
    def process(self, data):
        raise NotImplementedError("Processor subclasses must implement the process method.")