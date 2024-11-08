from string import Template

url_receiver = "ws://192.166.82.38:8000/ws/some_path/"
url_sender = "ws://192.166.82.38:8000/ws/456/"
url_betting = "ws://192.166.82.38:8000/ws/betting/"

GPT_API_KEY = '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'
GPTO1_mini = {
    'model':"openai/o1-mini-2024-09-12",
    'input_cost':3,
    'output_cost':12,
    'exchange_rate':7.2
}
GPT01_4o_mini = {
    'model':"openai/gpt-4o-mini",
    'input_cost':3,
    'output_cost':12,
    'exchange_rate':7.2
}
GPTO1_preview={
    'model':"openai/o1-preview-2024-09-12",
    'input_cost':15,
    'output_cost':60,
    'exchange_rate':7.2
}
GPT4 = "openai/gpt-4-turbo"
GPT3_5 = "openai/gpt-3.5-turbo"


GPT_MODEL = GPTO1_mini


REDIS= {
    "host": "127.0.0.1",
    "port": 6379,
}


GPT_DESC = """
1. 基本情况概述：不同的博彩平台对于同一场体育赛事中，球队命名存在差异，常见的差异包括但不限于，不同的语言、缩写等。
2. 任务描述：我将提供一个标准名称列表以及需要对齐的比赛数据字典。您的任务是根据比赛名称和相关信息，判断字典中的比赛是否与标准列表中的某场比赛相对应。考虑到命名规则的不同，比赛名称可能存在差异。在联赛相同的情况下，匹配条件应适当放宽，以确保能够正确识别相同的比赛。
3.1 基准列表用于存储标准化的比赛名称和对应的联赛名称。其格式如下：
       [{'gameName':'AC Sparta Prague -- Linkopings FC', 'leagueName':'International Clubs / UEFA Champions League Women'},
        {'gameName':'Maghreb AS de Fes -- Raja Beni Mellal' 'leagueName':' Morocco / Morocco Cup'},
         ...]，
3.2 需要对齐的数据：将以 JSON 格式发送，
       例如：{'gameName': 'Maghreb AS de Fes -- Raja Beni Mellal',
             'leagueName': 'Morocco / Morocco Cup'},
3.3 gameName： 表示比赛名称，--前后分别是参加比赛的两支球队，你分析时，无需考虑主队和客队问题。
    leagueName：表示联赛名称，是联赛的信息。
       
4. 匹配的结果，分为匹配成功和匹配失败两种情况，
    4.1如果匹配成功，返回：
   {
    "matchResult": "matchSuccess",
    "matchName": <标准列表中对应的比赛名称>,
    }
    4.2 如果匹配失败，返回：
    {"matchResult": "matchFail"}
  
6. 具体输入的真实数据如下：
    标准列表：{standard_list}
    需匹配字典：{platform_data}
7. 注意事项：请严格按照我的要求进行操作，仅返回我要求的 JSON 结构，不要包含任何解释、提示或说明。
"""
GPT_DESC_TEMPLATE = Template("""
1. **基本情况概述**  
   不同的博彩平台对同一场体育赛事中的球队名称可能存在差异。这些差异包括但不限于使用不同的语言、名称缩写、拼写变体等。

2. **任务描述**  
   我将提供一个标准名称列表以及需要对齐的比赛数据字典。您的任务是根据比赛名称和相关信息，判断字典中的比赛是否与标准列表中的某场比赛相对应。**考虑到命名规则的不同，比赛名称可能存在差异。在联赛相同的情况下，匹配条件应适当放宽，以确保能够正确识别相同的比赛。如果有某一支球队名称能够对应上，匹配条件放宽，通常可视为同一场比赛**

3. **数据格式说明**

   - **3.1 基准列表（Benchmark List）**  
     基准列表用于存储标准化的比赛名称和对应的联赛名称。其格式如下：

     ```json
     [
         {
             "gameName": "AC Sparta Prague -- Linkoping FC",
             "leagueName": "International Clubs / UEFA Champions League Women"
         },
         {
             "gameName": "Maghreb AS de Fes -- Raja Beni Mellal",
             "leagueName": "Morocco / Morocco Cup"
         },
         ...
     ]
     ```

     **说明：**
     - **`gameName`**：标准化后的比赛名称，格式为“主队名称 -- 客队名称”。
     - **`leagueName`**：比赛所属联赛的名称，格式为“联赛名称 / 联赛类型”。

   - **3.2 需要对齐的数据（Data to be Aligned）**  
     需要对齐的数据以 JSON 格式发送，示例如下：

     ```json
     {
         "gameName": "Maghreb AS de Fes -- Raja Beni Mellal",
         "leagueName": "Morocco / Morocco Cup"
     }
     ```

     **说明：**
     - **`gameName`**：比赛名称，格式为“主队名称 -- 客队名称”。
     - **`leagueName`**：比赛所属联赛的名称，格式为“联赛名称 / 联赛类型”。

4. **匹配结果格式说明**

   您需要将平台提供的数据与基准列表进行匹配，分为**匹配成功**和**匹配失败**两种情况，并最终返回以下结构的 JSON 数据：

   - **4.1 匹配成功**

     ```json
     {
         "matchResult": "matchSuccess",
         "matchName": "AC Sparta Prague -- Linkoping FC"
     }
     ```

     **说明：**
     - **`matchResult`**：表示匹配结果的状态，此处为 `"matchSuccess"`，表示匹配成功。
     - **`matchName`**：匹配到的标准比赛名称，来源于基准列表。

   - **4.2 匹配失败**

     ```json
     {
         "matchResult": "matchFail"
     }
     ```

     **说明：**
     - **`matchResult`**：表示匹配结果的状态，此处为 `"matchFail"`，表示匹配失败。

   **注意事项：**
   - **如果匹配成功**：
     - `matchResult` 的值为 `"matchSuccess"`。
     - `matchName` 中包含匹配到的标准名称。

   - **如果匹配失败**：
     - `matchResult` 的值为 `"matchFail"`。
     - `matchName` 字段被省略。

5. **本次需要匹配的真实数据如下：**

   - **标准列表**：${standard_list}
   - **需匹配字典**：${platform_data}

6. **注意事项**  
   请严格按照我的要求进行操作，仅返回我要求的 JSON 结构，不要包含任何解释、提示或说明。
""")


SLEEP_TIME = 1

TOTAL_BET = 100

