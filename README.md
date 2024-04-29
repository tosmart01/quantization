## CoinDreamer
<br>

**警告⚠️:** 总体杠杆比例绝对不能超过5倍，否则有爆仓风险。<br><br>
- (实盘测试过的) 自定义策略 + 回测 + 币安自动化交易的最小实现<br>
- 目前实现做空策略, 下图所示，红色开空，绿色平仓 <br>
- 手续费统一按 千分之一(0.001)计算，实际测试币安手续费在 0.0009- 0.00098 之间(非vip账户)，考虑到滑点统一按 0.001计算
- 最终结果只返回 开仓价，平仓价格日期，等字段，利润需要统一减去 0.001
<br><br>

![](./asset/img/开仓点位.png)

## 环境要求

- Python 3.10+
- 适用于 Windows/linux/mac 系统

## 安装指南

1. 克隆仓库到本地：

   ```shell
   git clone git@github.com:tosmart01/quantization.git
   ```

2. 安装所需依赖：

   ```shell
   pip install -r requirements.txt
   ```

## 使用说明

1. 配置 `config.settings` 文件，设置 `BINANCE_KEY`, `BINANCE_SECRET` 和其他环境变量。

2. 运行
   
   - 实盘运行
     <br><br>
   ```python
    # 设置策略
    strategy = strategy_factory(name='m_head')
    scheduler = BlockingScheduler()
    # 时间周期
    interval = '1h'
    model = strategy(symbol="ETHUSDT",
                     interval=interval,
                     backtest=False,
                     usdt=1200, #下单金额
                     leverage=5, # 杠杆
                     order_kind=OrderKindEnum.BINANCE,
                     )
    scheduler.add_job(model.execute, 'cron', hour='*',
                      minute=CRON_INTERVAL[interval], second='40',
                      )
    scheduler.start()
   ```
   
   ```shell
   # 运行实盘
   python main.py
   ```
   
   - 回测
      - [到币安官网下载历史数据](https://data.binance.vision/?prefix=data/spot/monthly/klines/ETHUSDT/)
      - [将币安csv数据修改为pandas pkl 格式](./src/scripts/export.py)<br>
      <br>
      
      ```
               date                 open      high  ...       volume  pct_change    symbol
         0   2021-03-01 08:00:00  45134.11  46571.30  ...  4899.574833         NaN  BTC/USDT
         1   2021-03-01 09:00:00  46217.18  46492.33  ...  2685.386005   -0.119782  BTC/USDT
         2   2021-03-01 10:00:00  46166.16  46796.94  ...  2926.951099    0.558318  BTC/USDT
         3   2021-03-01 11:00:00  46414.70  46540.31  ...  1970.348912   -0.179213  BTC/USDT
         4   2021-03-01 12:00:00  46336.38  46688.13  ...  2152.379904    0.263206  BTC/USDT
         ..                  ...       ...       ...  ...          ...         ...       ...
         739 2024-04-01 03:00:00  70856.61  71145.97  ...   948.185980    0.235546  BTC/USDT
         740 2024-04-01 04:00:00  71023.51  71119.93  ...   685.359750   -0.258365  BTC/USDT
         741 2024-04-01 05:00:00  70840.00  70941.17  ...   732.469530    0.022586  BTC/USDT
         742 2024-04-01 06:00:00  70855.99  71070.93  ...   735.395990    0.160890  BTC/USDT
         743 2024-04-01 07:00:00  70969.99  71366.00  ...  1514.230030    0.436818  BTC/USDT
     ```
      
   - 修改 [历史数据路径](./src/strategy/tests/m_test.py)<br>
     
   ```python
       MTestStrategy(symbol="ETHUSDT",
                     interval='1h',
                     usdt=20,
                     leverage=3,
                     order_kind=OrderKindEnum.BINANCE,
                     backtest=True, # 设置为True 
                     backtest_path="币安下载数据导出成pkl的路径", 
                     ).execute()
   ```
   
   - 运行回测
     
   ```shell
   python /src/strategy/tests/m_test.py
   # 结果输出路径为 /src/strategy/tests/{symbol}_backdump.json
   ```
   
   - 回测结果统计 
   
   ![](./asset/img/统计信息.png)
   ![](./asset/img/回测折线图.png) 


   ```python
   import json
   import pandas as pd
   data = json.load(open("symbol_backdump.json"))
   res = []
   for row in data:
       row['open_price'] = row['start_data']['close']
       res.append({k:v for k,v in row.items() if k not in ['start_data', 'end_data']})
   result = pd.DataFrame(res)
   result['start_time'] = result['start_time'].astype('datetime64')
   result['end_time'] = result['end_time'].astype('datetime64')
   result['profit'] = (result['open_price'] - result['close_price']) / result['open_price']
   result.profit = result.profit - 0.001
   result['profit_sum'] = result.profit.cumsum()
   note = """
   时间范围：2021-01-01-2024-02-28
   标的： ETHUSDT
   本次调整后数据：
   """
   win = result.loc[result.profit>0]
   loss = result.loc[result.profit<0]
   print(note)
   print(f"总盈利: {result.profit.sum():.2%}")
   print(f"总数量：{len(result)},盈数量=:{win.__len__()}, 亏：{loss.__len__()},比例: {win.__len__()/result.__len__():.2%}")
   print(f"亏损平均跌幅: {loss.profit.mean():.4%}")
   print(f"盈利平均涨幅: {win.profit.mean():.4%}")
   print(f"非止损单亏损总计: {result.loc[(~result.stop_loss)&(result.profit<0),'profit'].sum():.2%}")
   print(f"止损单总计: {result.loc[(result.stop_loss),'profit'].sum():.2%}")
   print(f"去除止损后纯盈利总计: {result.loc[result.profit>0,'profit'].sum():.2%}")
   print("result.profit.describe = \n",result.profit.describe())
   
   # 收益走势图
   result.start_time = result["start_time"].astype('datetime64')
   result['cumsum_p'] = result.profit.cumsum()
   summary = result.resample('1m', on='start_time').sum()
   summary['cumsum_p'] = summary.profit.cumsum()
   import matplotlib.pyplot as plt
   plt.figure(figsize=(20, 8))
   plt.plot(summary.index, summary['cumsum_p'], marker='o', linestyle='-')
   plt.title('Cumulative Profit Over Weeks')
   plt.xlabel('Week')
   plt.ylabel('Cumulative Profit')
   for i in summary.index:
       plt.text(i, summary.loc[i, 'cumsum_p'], f'{summary.loc[i, "cumsum_p"]:.1%}', fontsize='medium', verticalalignment ='bottom', )
   plt.grid(True)
   plt.show() 
   ```


## 代码结构

- `main.py`: 主程序入口。
- `order/`: 包含 `OrderBinance` 类，负责币安订单执行逻辑,可自定义实现其他交易所
- `strategy/`: 策略模块，目前实现M头策略
- `client/`: Binance API 交互的客户端配置。
- `common/`: 常用工具和日志配置。
- `config/`: 项目配置和环境变量。
- `models/`: 订单表记录
- `schema/`: 数据模型和枚举类。
- `service/`: 邮件服务。
- `controller/`: 订单表ORM操作
- `dataset/`: 数据获取逻辑
- `notices/`: 通知模块，目前支持email
