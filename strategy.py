import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
# 设置参数
n1 = 1.0
n2 = 0.2
n3 = 2
Spread  = pd.read_csv(r"D:\project_cleandata\Spread.csv")
mu = np.mean(Spread['spread'])
std = np.std(Spread['spread'])

level = (float('-inf'),mu-n3*std,mu-n1*std,mu-n2*std,mu+n2*std,mu+n1*std,mu+n3*std,float('inf'))
prcLeveL = pd.cut(Spread['spread'],level,labels=False)-3

#交易信号函数
def TradeSig(prcLevel):
    n = len(prcLevel)
    signal = np.zeros(n)
    for i in range(1,n):
        if prcLevel[i-1] == 1 and prcLevel[i] == 2:
            signal[i] = -2
        elif prcLevel[i-1] == 1 and prcLevel[i] == 0:
            signal[i] = 2
        elif prcLevel[i-1] == 2 and prcLevel[i] == 3:
            signal[i] = 3
        elif prcLevel[i-1] == -1 and prcLevel[i] == -2:
            signal[i] = 1
        elif prcLevel[i-1] == -1 and prcLevel[i] == 0:
            signal[i] = -1
        elif prcLevel[i-1] == -2 and prcLevel[i] == -3:
            signal[i] = -3
    return (signal)

signal = TradeSig(prcLeveL)
position = [signal[0]]
ns = len(signal)

for i in range(1,ns):
    position.append(position[-1])  # 如果不满足以下条件则保持不变 
    if signal[i] == 1:
        position[i] = 1
    elif signal[i] == -2:
        position[i] = -1
    elif signal[i] == -1 and position[i-1] == 1:
        position[i] = 0
    elif signal[i] == 2 and position[i-1] == -1:
        position[i] = 0
    elif signal[i] == 3 :
        position[i] = 0
    elif signal[i] == -3:
        position[i] = 0

position = pd.DataFrame(position,columns=['position'])
position['TradingTime'] = Spread['Formal_time']
position.to_csv(r"D:\project_cleandata\Position.csv")

whether_in_process = False
record_list = [] #记录
for i in range(len(position)):
    cursor = position.loc[i,'position']
    if cursor != 0 and whether_in_process == False:
        starttime = position.loc[i,'TradingTime']
        whether_in_process = True
        direction = cursor
    elif cursor == 0 and whether_in_process == True:
        endtime = position.loc[i,'TradingTime']
        whether_in_process = False
        record_list = record_list+[(starttime,endtime,direction)]
    else:
        continue

pnl_date_dict = {}
#策略表现
date_list = []
for trade_tuple in record_list:
    if trade_tuple[1][:11] not in date_list:
        date_list.append(trade_tuple[1][:11])
for date in date_list:
    pnl_date_dict[date] = []

total_data = pd.read_csv(r'D:\project_cleandata\total.csv')
total_data.set_index(total_data['Formal_time'],inplace=True)


for trade_tuple in record_list:
    rate = (total_data['BidPrice1_y'][trade_tuple[1]]+total_data['AskPrice1_y'][trade_tuple[1]])/2  #用平仓时汇率的买一和卖一的平均值算汇率

    if trade_tuple[2] == -1:
        profit = -1000*(total_data['BPrice1'][trade_tuple[0]]-total_data['SPrice1'][trade_tuple[1]]
        +(total_data['AskPrice1_x'][trade_tuple[0]]-total_data['BidPrice1_x'][trade_tuple[1]])*rate)
        -7-2*rate

        pnl_date_dict[trade_tuple[1][:11]].append(profit)
    else:
        profit = -1000*(-total_data['SPrice1'][trade_tuple[0]]+total_data['BPrice1'][trade_tuple[1]]
        +(-total_data['BidPrice1_x'][trade_tuple[0]]+total_data['AskPrice1_x'][trade_tuple[1]])*rate)
        -7-2*rate

        pnl_date_dict[trade_tuple[1][:11]].append(profit)

total_times = 0
totol_success = 0
total_pnl = 0
pnl_y = []
for key in pnl_date_dict.keys():

    success = sum(i>0 for i in pnl_date_dict[key])
    success_rate = success/len(pnl_date_dict[key])
   
    total_times+=len(pnl_date_dict[key])
    totol_success+=success
    total_pnl += sum(pnl_date_dict[key])
    pnl_y.append(sum(pnl_date_dict[key]))
    print('日期：%s\n'%key)
    print('日交易回合数：%s 日胜率:%s 日均pnl:%s\n'%(len(pnl_date_dict[key]),success_rate,total_pnl/len(pnl_date_dict[key])))

print('\n总回合数:%s  胜率为：%s 总体回合平均pnl:%s'%(total_times,totol_success/total_times,total_pnl/total_times))

plt.plot(list(pnl_date_dict.keys()),pnl_y)
plt.title('Daily cumulative pnl')
plt.xlabel('Date')
plt.ylabel('RMB')
plt.show()