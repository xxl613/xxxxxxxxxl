#!需要修改的内容:
#   1. cfg_path的文件地址
#   2. 所有的发包data，需要以实际记录为准
#   3. 处理的

import requests
import json
import configparser
import os
import datetime


#用于处理发包的数据，将其改为json类型
def modify_data(data):
    for i in range(0, len(data)):
        data[i] = data[i].replace('\n', '')
        data[i] = data[i].replace(' ','')
        list_i = list(data[i])
        list_i.insert(data[i].find(':') + 1, "\"")
        list_i.insert(data[i].find(':'), "\"")
        data[i] = ''.join(list_i)
        data[i] = "\"" + data[i] + "\""
        if(i!=len(data)-1):
            data[i] += ','
    return "{" + ''.join(data) + "}"

#检查配置文件
def check_userid():
    #解析用户表配置文件
    cfg = configparser.ConfigParser()
    cfg_path = os.getcwd()+"/user_id.ini"
    if os.path.exists(cfg_path) == False:# 如果配置文件为空就创建一个新的配置文件
        fp = open(cfg_path,"w")
        fp.close()
    cfg.read(cfg_path)

    #比对用户ID和门店名称
    # data_list = []
    # # 将文件的内容按行存入data_list中
    # with open(os.getcwd() + "/check_userid_data.txt") as f:
    #     for lines in f:
    #         tmp = lines
    #         data_list.append(tmp)
    # data = json.loads(modify_data(data_list))#这是用于发送的数据

    url = 'http://bzerp.folome.org/index.php/api/user/getstore'
    data = {'department_id': '2', 'token': '8938b208fb7ad8bafdc02f53bdd66bc6', 'auth_name': '/development/report/order', 'user_id': '1126', 'company_id': '1'}
    user_list = json.loads(requests.post(url, data).content)['data']['list']#获得用户的数据,并且转化成list,user_list就是存放用户数据的字典列表
    for per_list in user_list:
        system_name = per_list['system_name']#获取门店名称和ID
        store_id = per_list['store_id']
        if cfg.has_section(system_name)==False:
            cfg.add_section(system_name)
            cfg.set(system_name,"id",str(store_id))
        fp = open(cfg_path, "w")#将之前记录的所有ID都写入到文件中
        cfg.write(fp)
        fp.close()
    print("Finished checking")
    return cfg

#检查操作记录文件
def check_record():
    #确认是否有操作记录文件,没有就创建一个
    cfg_record = configparser.ConfigParser()
    DT = datetime.datetime
    cfg_record_path = os.getcwd() + "/record-" + DT.strftime(DT.today(),'%y') + DT.strftime(DT.today(),'%a') + ".ini"
    if os.path.exists(cfg_record_path)==False:
        fp = open(cfg_record_path,"w")
        fp.close()
    cfg_record.read(cfg_record_path)
    return cfg_record

#计算需要扣费的金额
def Calculate_insurance(person_number,line_type_name,days):
    switch = {"出境游":"1","国内游":"2","省内游":"3","港澳游":"4"}#做一个switch类型的字典用于处理线路编号
    line_no = int(switch[line_type_name])
    deduct_money = 0#最后返回的扣款金额
    if line_no==1 or line_no==4:#出境游或者港澳游扣费规则
        deduct_money = 15
    if line_no==2:#国内游
        if days<4:
            deduct_money = days
        else:
            deduct_money = 5
    if line_no==3:#省内游
        if days<11:
            deduct_money = days
        else:
            deduct_money = 10
    deduct_money *= person_number
    return deduct_money

#实际扣款的发包程序
def deduct(store_id,deduct_money,order,days):
    store_id = 1122#用作测试，！！！！！！！！！！！
    url = 'http://bzerp.folome.org/index.php/api/recharge/BuckleMoney'
    data = {'type': '3', 'store_id': '1122', 'amount': '1', 'remarks': '娴嬭瘯', 'token': 'b5ac4655f9a001b51b136502f95f1d9c', 'auth_name': '/finance/settlement/Creditlist', 'user_id': '1121', 'company_id': '1', 'department_id': '6'}
    data['store_id'] = str(store_id)#将原始字典中的内容替换成需要扣费的内容
    data['amount'] = str(deduct_money)
    data['remarks'] = "订单号：" + order['order_code']

    response = requests.post(url,data).content#发包扣款
    response = json.loads(str(response,'utf-8').strip("b'"))


    global successful_order
    global fail_order
    if response['msg'] == "操作成功":#计算成功失败的个数
        successful_order += 1
    else:
        fail_order += 1

    order_code = order['order_code']
    line_type_name = order['line_type_name']
    person_number = order['person_number']

    DT = datetime.datetime#将操作结果记录到record.ini中
    if cfg_record.has_section(today)==False:
        cfg_record.add_section(today)
    cfg_record.set(today,order_code,response['msg'] + "——扣款金额：" + str(deduct_money) + "，线路类型：" + line_type_name + "，人数：" + str(person_number) + "，天数：" + str(days));

#扣除保险的执行程序
def deduct_insurance():
    # data_list = []
    # with open(os.getcwd() + '/deduct_insurance_data.txt') as f:
    #     for lines in f:
    #         data_list.append(lines)
    # data = json.loads(modify_data(data_list))
    url = 'http://bzerp.folome.org/index.php/api/report/getorderreport'
    data = {'start_date': 'START_DATA,END_DATA', 'page': '1', 'pagesize': '500', 'line_name_id': '', 'store_id': '', 'token': '8938b208fb7ad8bafdc02f53bdd66bc6', 'auth_name': '/development/report/order', 'user_id': '1126', 'company_id': '1', 'department_id': '7'}
    target_date = datetime.date.today()+datetime.timedelta(days=-1)
    data['start_date'] = str(target_date) + ',' + str(target_date)# 将日期改为前一天
    # 发包获取订单数据
    response = requests.post(url,data)
    list = json.loads(response.content)['data']['list']#list是订单数据
    global total_order
    total_order = len(list)-1
    for order in list[1:4]:#跳过0号数据，0号是订单统计！！！！！！！！！！！！！
        store_name = order['store_name'] #店铺名字
        person_number = order['person_number']#订单人数
        line_type_name = order['line_type_name']#线路类型
        DT = datetime.datetime#声明一个时间类
        start_date = DT.strptime(order['start_date'],"%Y-%m-%d")#出发日期
        return_date = DT.strptime(order['return_date'], "%Y-%m-%d")  # 返程日期
        delta_days = return_date - start_date
        days = delta_days.days+1#行程天数
        deduct_money = Calculate_insurance(person_number,line_type_name,days)#扣费金额
        store_id = cfg.get(store_name,"id")
        deduct(store_id,deduct_money,order,days)
    print("Finished Deducting")

def test():
    DT = datetime.datetime
    today = DT.today() + datetime.timedelta(days=-1)
    today = today.strftime("%Y-%m-%d")
    if cfg_record.has_section(today)==False:
        cfg_record.add_section(today)
    cfg_record.set(today,"订单号","2");

    cfg_record_path = os.getcwd() + "/record-" + DT.strftime(DT.today(), '%y') + DT.strftime(DT.today(), '%a') + ".ini"
    fp = open(cfg_record_path,"w")
    cfg_record.write(fp)
    fp.close()


#main入口

total_order = 0#全局变量声明
successful_order = 0
fail_order = 0

cfg = check_userid()#用户id配置文件
cfg_record = check_record()#操作记录配置文件

DT = datetime.datetime#全局时间类声明
today = DT.today() + datetime.timedelta(days=-1)#today代表操作的那一天的数据,默认是当前时间的前一天
today = today.strftime("%Y-%m-%d")
cfg_record_path = os.getcwd() + "/record-" + DT.strftime(DT.today(), '%y') + DT.strftime(DT.today(), '%a') + ".ini"

deduct_insurance()

cfg_record.set(today,"total",str(total_order))
cfg_record.set(today,"success",str(successful_order))
cfg_record.set(today,"fail",str(fail_order))

fp = open(cfg_record_path, "w")#将最后的操作结果写入record.ini中
cfg_record.write(fp)
fp.close()