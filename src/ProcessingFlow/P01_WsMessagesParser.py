import json
from  src.ProcessingFlow.BaseProcess import Processor
from src.Utils.Log import get_logger


class WsMessagesParser(Processor):
    Count_Valid_data = 0
    Count_Invlid_data = 0
    def __init__(self,log_name='WsMessagesParser', **kwargs):
        super().__init__(**kwargs)
        self.log_name = log_name
        self.logger = get_logger(name=__name__, log_file=self.log_name)
    def process(self, data):
        try:
            message_dict = json.loads(data)
            if 'message' in message_dict:
                data_str = message_dict['message']
                if isinstance(data_str, str):
                    data_dict = json.loads(data_str)
                    self.logger.info(f"[管道1--ws解析] 解析成功：{data_dict}")
                elif isinstance(data_str, dict):
                    self.logger.info(f"[管道1--ws解析] 解析成功：{data_str}")
                    data_dict = data_str
                else:
                    self.logger.error("[管道1--ws解析] message字段格式不正确")
                    return None
            else:
                self.logger.error("[管道1--ws解析] 缺少 message字段")
                return None
            return data_dict
        except json.JSONDecodeError as e:
            self.logger.error(f"[管道1--ws解析] JSON 解析错误：{e}")
            return None