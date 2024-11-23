import json
import requests
from src.ProcessingFlow.BaseProcess import Processor
from src.Utils.Log import get_logger
from settings import GPT_DESC_TEMPLATE, GPT_API_KEY,GPT_MODEL


class MatchGPT(Processor):
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
        'standard_name_list_for_gpt_request':list,
        # 也有可能没有standard_name_list_for_gpt_request字段
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

    def __init__(self, log_name='MathFuzzy',**kwargs):
        super().__init__(**kwargs)
        self.log_name = log_name or './Log/MathFuzzy.log'
        self.logger = get_logger(name=__name__, log_file=self.log_name)
        self.num_gpt_ask=0

    def process(self, data):
        # 已经挂载了 standard_name 则直接返回，不做处理
        if 'standard_name' in data and data['standard_name']:
            return data

        if 'standard_name_list_for_gpt_request' in data and data['standard_name_list_for_gpt_request'] == []:
            # 模糊匹配结果为空，说明是全新的数据，直接使用game_name
            standard_name = data['game_name']
            game_name = data['game_name']
            # 将标准名称添加到数据中
            self.mapping_dict[data['game_name']] = standard_name
            data_ = {'standard_name': standard_name, 'league_name': data['league_name']}
            self.standard_list_for_gpt_ask.insert(0, data_)
            data['standard_name'] = game_name
            return data


        # TODO: 实现匹配逻辑
        if 'standard_name_list_for_gpt_request' in data and data['standard_name_list_for_gpt_request']:
            if response := self.request_gpt(data):  # 如果有返回值
                self.calculate_cost(response)  # 打印费用
                if response_dict := self.parse_gpt_response(response):  # 如果解析成功
                    if 'success' in response_dict["matchResult"].lower():
                        standard_name = response_dict["matchName"]
                        # 将标准名称添加到数据中
                        self.mapping_dict[data['game_name']] = standard_name
                        data['standard_name'] = standard_name
                        return data
                    else:
                        standard_name = data['game_name']
                        self.mapping_dict[data['game_name']] = standard_name
                        data_={'standard_name':standard_name,'league_name':data['league_name']}
                        self.standard_list_for_gpt_ask.insert(0,data_)
                        self.standard_list_for_gpt_ask = self.standard_list_for_gpt_ask[:500]

        data['standard_name'] = data['game_name']
        return data


    def request_gpt(self, spider_data):
        platform_data = {
            "gameName": spider_data['game_name'],
            "leagueName": spider_data['league_name'],
        }
        # 构造 GPT 描述
        desc = GPT_DESC_TEMPLATE.safe_substitute(
            standard_list=json.dumps(spider_data['standard_name_list_for_gpt_request'], ensure_ascii=False),
            platform_data=json.dumps(platform_data, ensure_ascii=False)
        )

        self.num_gpt_ask += 1
        # self.logger.info(f"[GPT 请求] 描述: {desc}")
        self.logger.warning(
            f"[这是第 {self.num_gpt_ask} 次GPT请求]-----------------------------------------------------------------")
        print(f"[这是第 {self.num_gpt_ask} 次GPT请求]-----------------------------------------------------------------")
        self.log_(spider_data,platform_data)

        try:
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GPT_API_KEY}",
                },
                json={
                    "model": GPT_MODEL['model'],
                    "messages": [{"role": "user", "content": desc}],
                },
                timeout=10  # 设置请求超时时间，避免长时间等待
            )

            if response.status_code == 200:
                self.logger.debug(f"[GPT 请求] 成功，状态码：{response.status_code}")
                return response
            else:
                self.logger.error(f"[GPT 请求] 失败，状态码：{response.status_code}")
                self.logger.error(f"[GPT 请求] 响应内容：{response.text}")
                return None
        except requests.exceptions.RequestException as e:
            self.logger.error(f"[GPT 请求] 发生异常：{str(e)}")
            return None

    def parse_gpt_response(self, response):
        try:
            response_json = response.json()
            self.logger.debug(f"[GPT 响应解析] 响应 JSON: {response_json}")
            choices = response_json.get('choices', [])
            if not choices:
                self.logger.error("[GPT 响应解析报错] 没有 'choices' 字段")
                return None

            message = choices[0].get('message', {})
            content = message.get('content', '').strip()

            if not content:
                self.logger.error(f"[GPT 响应解析报错] 内容为空: {response.text}")
                return None

            self.logger.debug(f"[GPT 响应解析] 原始内容: {content}")

            # 移除代码块标记（如果存在）
            if content.startswith("```json") and content.endswith("```"):
                content = content.replace('```json', '').replace('```', '').strip()

            # 解析 JSON 内容
            content_dict = json.loads(content)

            self.logger.info(f"[GPT 响应解析] 解析后的内容字典: {json.dumps(content_dict,indent=4, ensure_ascii=False)}")

            match_result = content_dict.get('matchResult', None)

            if match_result == 'matchSuccess':
                self.logger.warning('[GPT 匹配结果] 匹配成功')
                match_name = content_dict.get('matchName', None)
                if match_name:
                    return {
                        "matchResult": "matchSuccess",
                        "matchName": match_name
                    }

                else:
                    self.logger.error("[GPT 响应解析报错] 'matchName' 字段缺失")
                    return None
            elif match_result == 'matchFail':
                self.logger.warning('[GPT 匹配结果] 没有找到合适的比赛，匹配失败')
                return {
                    "matchResult": "matchFail"
                }
            else:
                self.logger.error("[GPT 响应解析报错] 'matchResult' 字段值不合法或缺失")
                return None

        except json.JSONDecodeError as e:
            self.logger.error(f"[GPT 响应解析报错] JSON 解析错误：{str(e)}")
            self.logger.error(f"[GPT 响应解析报错] 响应内容为：{response.text}")
            return None
        except KeyError as e:
            self.logger.error(f"[GPT 响应解析报错] KeyError: {str(e)}")
            self.logger.error(f"[GPT 响应解析报错] 响应内容为：{response.text}")
            return None
        except Exception as e:
            self.logger.error(f"[GPT 响应解析报错] 未知错误：{str(e)}")
            self.logger.error(f"[GPT 响应解析报错] 响应内容为：{response.text}")
            return None

    def calculate_cost(self, response,
                       input_cost_per_million=GPT_MODEL['input_cost'],
                       output_cost_per_million=GPT_MODEL['output_cost'],
                       exchange_rate=GPT_MODEL['exchange_rate']):
        try:
            response_json = response.json()
            usage = response_json.get('usage', {})
            prompt_tokens = usage.get('prompt_tokens', 0)
            completion_tokens = usage.get('completion_tokens', 0)

            cost_usd = (prompt_tokens * input_cost_per_million / 1_000_000) + \
                   (completion_tokens * output_cost_per_million / 1_000_000)
            # 转换为人民币
            cost_cny = cost_usd * exchange_rate
            yuan = int(cost_cny)
            jiao = int((cost_cny - yuan) * 10)
            fen = int(round((cost_cny - yuan - jiao / 10) * 100))
            self.logger.warning(
                f"[GPT 费用计算] 发送 Tokens 数量: {prompt_tokens}, 接收 Tokens 数量: {completion_tokens}, 费用人民币: {yuan}元{jiao}角{fen}分")
            return cost_cny
        except Exception as e:
            self.logger.error(f"[GPT 费用计算报错] 发生错误：{str(e)}")
            self.logger.error(f"[GPT 费用计算报错] 响应内容为：{response.text}")
            return None

    def log_(self,spider_data,platform_data):
        standard_list = json.dumps(spider_data['standard_name_list_for_gpt_request'], indent=4, ensure_ascii=False)
        platform_data_str = json.dumps(platform_data, indent=4, ensure_ascii=False)

        # 逐行打印标准列表中的每一个标准名称
        standard_names = '\n'.join(
            [f"[{item['standard_name']}]" for item in spider_data['standard_name_list_for_gpt_request']])

        # 构造最终日志字符串
        final_log_message = (
            f"\n标准列表中的比赛如下:\n{standard_names}\n"   
            f"被匹配的比赛为: \n[{platform_data['gameName']}]\n"
            f"被匹配比赛所在联赛为: [{platform_data['leagueName']}]\n"
        )

        # 打印最终日志
        self.logger.warning(final_log_message)