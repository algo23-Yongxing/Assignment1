import pandas as pd
import datetime
import numpy as np
import matplotlib.pyplot as plt
import os 

# 得到固定起始时间点，间隔为s的列表
def get_all_time_list_as_df(time_start:str,time_end:str): #time format is: YYYY/M/Y H:MM
    time_interval =  datetime.datetime.strptime(time_end, "%Y/%m/%d %H:%M:%S")-datetime.datetime.strptime(time_start, "%Y/%m/%d %H:%M:%S")
    time_second_numbner = time_interval.seconds + time_interval.days * 24 * 3600 + 1
    # print(time_second_numbner)
    time_list = [str(x).replace('-','/') for x in list(pd.date_range(start=time_start,periods=time_second_numbner,freq='s'))]
    time_df = pd.DataFrame()
    time_df['time'] = time_list
    return time_df

# 对时间戳进行处理
def tran_time(s):
    s = str(int(s))[:-3].rjust(6,'0')
    return s[:2]+':'+s[2:4]+':'+s[4:]
# 对不同表格的日期进行处理
def trans_date(s):
    s = str(s)
    s = s.replace('-','').replace('/','')
    return s[:4]+'/'+s[4:6]+'/'+s[6:]

# 判断时间是否是在国内交易时间段
def identify_time_in_range(trade_time_interval,s):
    trade_time_interval = [(int(x[0].replace(':','')),int(x[1].replace(':',''))) for x in trade_time_interval]
    s = int(s.replace(':',''))
    for time_interval in trade_time_interval:
        if s>= time_interval[0] and s<= time_interval[1]:
            return True
    return False

# 利用identify_time_in_range函数对dataframe进行处理
def keep_time_in_range(trade_time_interval:list,df,time_col_name = 'Time'): #trade_time_interval:[(start,end),...]
    df = df[df[time_col_name].apply(lambda x : identify_time_in_range(trade_time_interval,x))]
    return df



def this_fun(f_path):
    #读取数据
    df = pd.read_csv(f_path)
    df['Time'] = df['Time'].apply(lambda s : tran_time(s))
    df['InternalDate'] = df['InternalDate'].apply(lambda s : trans_date(s))
    df['Formal_time'] = df['InternalDate'] +' '+df['Time']

    #获取时间的起点和终点
    start_time = df['Formal_time'][df.index[0]]
    end_time = df['Formal_time'][df.index[-1]]
    # print(start_time,end_time)

    #获取完整的时间序列
    complete_time = get_all_time_list_as_df(start_time,end_time)
    # print(complete_time)
    complete_time.columns = ['Formal_time']

    #开始合并时间段
    complete_df = pd.merge(complete_time,df,how = 'left',on='Formal_time')

    #识别非交易时间
    trade_time = [('09:00:00','10:15:00'),('10:30:00','11:30:00'),('13:30:00','15:00:00'),('21:00:00','23:59:00'),('00:00:00','02:30:00')]
    complete_df['Time'] = complete_df['Formal_time'].apply(lambda x : x.split(' ')[1])
    complete_df = keep_time_in_range(trade_time,complete_df)

    complete_df = complete_df.interpolate()
    exclude_list = ['InternalDate','Time','Symbol','InternalTime','Exchange']
    complete_df = complete_df[[x for x in complete_df.columns if x not in exclude_list]]
    # complete_df.to_excel('test3.xlsx',index=False)
    return complete_df


g = os.walk("D:\project_data")
fils_dict = {}
for a,b,c in g:
    for file in c:
        if file.endswith('.csv'):
            fils_dict[file] = os.path.join(a,file)

clean_data_B = []
clean_data_SC = []
clean_data_usdcnh = []

for k,v in fils_dict.items():
    if k.startswith('B'):
        clean_data_B.append(this_fun(v))
    elif k.startswith('sc'):
        clean_data_SC.append(this_fun(v))
    else:
        clean_data_usdcnh.append(this_fun(v))
        
# 将国外原油、国内原油、汇率清洗完的数据进行拼接
B_clean_data = pd.concat(clean_data_B,sort=False)
SC_clean_data = pd.concat(clean_data_SC,sort=False)
usdcnh_clean_data = pd.concat(clean_data_usdcnh,sort=False)

B_clean_data.to_csv(r"D:\project_cleandata\B.csv",index=False)
SC_clean_data.to_csv(r"D:\project_cleandata\SC.csv",index=False)
usdcnh_clean_data.to_csv(r"D:\project_cleandata\usdcnh.csv",index=False)

df = pd.merge(B_clean_data,SC_clean_data,on='Formal_time')
df = pd.merge(df,usdcnh_clean_data,on='Formal_time')
df.to_csv(r"D:\project_cleandata\total.csv",index=False)

df = pd.read_csv(r"D:\project_cleandata\total.csv")


# 1s序列
minusdf1 = pd.DataFrame()
minusdf1['Formal_time'] = df['Formal_time']
# 价差 = 上海原油最新价 - 汇率卖一价*布伦特原油最新价
minusdf1['spread'] = list(df['LastPrice_y'] - df['BidPrice1_y']*df['LastPrice_x'])
#异常值处理
minusdf1 = minusdf1[abs(minusdf1['spread'])<400]
minusdf1 = minusdf1[minusdf1['spread'].notnull()]
minusdf1.to_csv(r"D:\project_cleandata\Spread.csv")

n1 = 0.6
n2 = 0.2
n3 = 1.0

mu = np.mean(minusdf1['spread'])
std = np.std(minusdf1['spread'])
#画图
minusdf1.plot()
plt.title('1s time series')
plt.xlabel('Time')
plt.ylabel('spread(¥)')
plt.axhline(y = mu,color = 'black')
plt.axhline(y = mu+n1*std,color = 'blue')
plt.axhline(y = mu-n1*std,color = 'blue')
plt.axhline(y = mu+n2*std,color = 'yellow')
plt.axhline(y = mu-n2*std,color = 'yellow')
plt.axhline(y = mu+n3*std,color = 'red')
plt.axhline(y = mu-n3*std,color = 'red')



# 1min序列
# minusdf1['pick'] = list(pd.Series(list(minusdf1.index)).apply(lambda x : str(x)[-2:]=='00'))
minusdf2 = minusdf1[minusdf1['Formal_time'].apply(lambda x : str(x)[-2:]=='00')]
mu = np.mean(minusdf2['spread'])
std = np.std(minusdf2['spread'])

minusdf2.plot()
plt.title('1min time series')
plt.xlabel('Time')
plt.ylabel('spread(¥)')
plt.axhline(y = mu,color = 'black')
plt.axhline(y = mu+n1*std,color = 'blue')
plt.axhline(y = mu-n1*std,color = 'blue')
plt.axhline(y = mu+n2*std,color = 'yellow')
plt.axhline(y = mu-n2*std,color = 'yellow')
plt.axhline(y = mu+n3*std,color = 'red')
plt.axhline(y = mu-n3*std,color = 'red')

# 5min序列
# minusdf1['pick'] = list(pd.Series(list(minusdf1.index)).apply(lambda x : float(str(x)[-5:-3])%5==0))
minusdf3 = minusdf1[minusdf1['Formal_time'].apply(lambda x : float(str(x)[-5:-3])%5==0)]
mu = np.mean(minusdf3['spread'])
std = np.std(minusdf3['spread'])

minusdf3.plot()
plt.title('5min time series')
plt.xlabel('Time')
plt.ylabel('spread(¥)')
plt.axhline(y = mu,color = 'black')
plt.axhline(y = mu+n1*std,color = 'blue')
plt.axhline(y = mu-n1*std,color = 'blue')
plt.axhline(y = mu+n2*std,color = 'yellow')
plt.axhline(y = mu-n2*std,color = 'yellow')
plt.axhline(y = mu+n3*std,color = 'red')
plt.axhline(y = mu-n3*std,color = 'red')

plt.show()