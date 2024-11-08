import time
from src.ProcessingFlow.BaseProcess import Processor
from src.Utils.Log import get_logger
from settings import TOTAL_BET
import json

class CalculateOddsLess1(Processor):
    def __init__(self, log_name='CalculateOddsLess1', **kwargs):
        super().__init__(**kwargs)
        self.log_name = log_name or './Log/CalculateOddsLess1.log'
        self.logger = get_logger(name=__name__, log_file=self.log_name)
        self.last_total_odds = {}  # 记录每个比赛的上一次 total_odds 值
        self.sent_total_odds = {}  # 记录每个比赛已发送过的 total_odds

    def process(self, data):
        standard_name = data['standard_name']

        # 检查是否在聚合赔率字典中
        if standard_name not in self.aggregated_max_odds_dict:
            return data

        odds_info = self.aggregated_max_odds_dict[standard_name]
        total_odds = odds_info.get('total_odds', None)

        # 检查 total_odds 是否在 0 到 1 之间
        if total_odds is not None and 0 < total_odds < 1:
            previous_total_odds = self.last_total_odds.get(standard_name)

            if previous_total_odds != total_odds:
                # total_odds 发生了变化，更新 last_total_odds
                self.last_total_odds[standard_name] = total_odds

                # 检查是否已经发送过该 total_odds
                sent_odds = self.sent_total_odds.get(standard_name, set())
                if total_odds not in sent_odds:
                    # 计算投注额并发送数据
                    self.calculate_bet_amounts(odds_info)
                    # 将结果放入 betting_queue
                    self.betting_queue.put(odds_info)
                    self.logger.warning(
                        f"[套利机会] 发送比赛：{standard_name}\n数据：{json.dumps(odds_info, indent=4, ensure_ascii=False)}")
                    # 记录已发送的 total_odds
                    sent_odds.add(total_odds)
                    self.sent_total_odds[standard_name] = sent_odds
                else:
                    self.logger.info(f"[已发送] 比赛 {standard_name} 的 total_odds {total_odds} 已发送过，跳过发送")
            else:
                self.logger.info(f"[未变化] 比赛 {standard_name} 的 total_odds 未变化，值为 {total_odds}")
        else:
            self.logger.debug(f"[忽略] 比赛 {standard_name} 的 total_odds 不在 0 到 1 之间")

        return data

    def calculate_bet_amounts(self, odds_info):
        # 提取各项赔率
        home_odds = odds_info['home_max_odds']['odds']
        draw_odds = odds_info['draw_max_odds']['odds']
        away_odds = odds_info['away_max_odds']['odds']

        # 计算投注额
        inverse_home = 1 / home_odds
        inverse_draw = 1 / draw_odds
        inverse_away = 1 / away_odds
        total_inverse = inverse_home + inverse_draw + inverse_away

        # 根据比例分配投注额，总额为 TOTAL_BET
        home_bet = (inverse_home / total_inverse) * TOTAL_BET
        draw_bet = (inverse_draw / total_inverse) * TOTAL_BET
        away_bet = (inverse_away / total_inverse) * TOTAL_BET

        # 保留小数点后一位
        home_bet = round(home_bet, 1)
        draw_bet = round(draw_bet, 1)
        away_bet = round(away_bet, 1)

        # 调整总和为 TOTAL_BET（由于四舍五入可能导致总和不为 TOTAL_BET）
        total_bet = home_bet + draw_bet + away_bet
        difference = TOTAL_BET - total_bet

        # 将差值添加到最大的投注额上，以确保总和为 TOTAL_BET
        bets = {'home_bet': home_bet, 'draw_bet': draw_bet, 'away_bet': away_bet}
        max_bet_key = max(bets, key=bets.get)
        bets[max_bet_key] += difference

        # 更新 odds_info 中的 bet_amount
        odds_info['home_max_odds']['bet_amount'] = bets['home_bet']
        odds_info['draw_max_odds']['bet_amount'] = bets['draw_bet']
        odds_info['away_max_odds']['bet_amount'] = bets['away_bet']

        self.logger.info(f"[投注额计算] 比赛 {odds_info['home_max_odds']['standard_name']} 的投注额已计算完成")
