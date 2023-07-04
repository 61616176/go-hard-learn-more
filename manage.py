# -*- coding:utf-8 -*-
import os, sys
# import ConfigParser
import socket
import threading
from DbMysql import DbMysql
from subprocess import PIPE, Popen, call
import time
import scapy
import pyshark
import pymysql
import configparser
import scapy.all as scapy
from scapy.utils import PcapWriter

sys.path.append('./utils/')

import traceback

from flask_cors import cross_origin
from flask import send_file
from flask import Flask, jsonify, render_template, request
import json
import logging

import scapy
from scapy.all import rdpcap
from scapy.utils import PcapReader

from xml.dom.minidom import parse
import xml.dom.minidom

import json
import tarfile
app = Flask(__name__)  # 实例化app对象

# load config
ns3_home = ''
openplc_home = ''
data_home = ''
cp = configparser.ConfigParser()
with open('sys_cfg.conf', 'r') as cfgfile:
    cp.readfp(cfgfile)
    ns3_home = cp.get('general', 'ns3_home')
    openplc_home = cp.get('general', 'openplc_home')
    data_home = cp.get('general', 'data_home')


###################################Services###################################
@app.route('/')
@cross_origin()
def hello():
    return 'hello'


@app.route('/saveStrategy/', methods=['POST', 'GET'])
@cross_origin()
def saveStrategy():
    jdata = request.get_data()
    jdata = json.loads(jdata)

    with open("./scratch/strategy.json", 'w') as strategy:
        json.dump(jdata, strategy)

    return "success"


@app.route('/getStrategy/', methods=['POST', 'GET'])
@cross_origin()
def getStrategy():
    with open("./scratch/strategy.json", 'r') as strategy:
        jdata = json.load(strategy)
    return jdata


@app.route('/saveDigitalTwinCover/', methods=['POST', 'GET'])
@cross_origin()
def saveDigitalTwinCover():
    jdata = request.get_data()
    jdata = json.loads(jdata)
    # topolist = jdata['topoList']
    name = jdata['name']
    data = jdata['data']
    links = jdata['links']
    jsondata = {'data': data, 'links': links}

    with open(data_home + "ns3/series/" + str(name) + ".json", 'w') as series:
        json.dump(jsondata, series)

    with open(data_home + "ns3/scene/" + str(name) + ".json", 'w') as scene:
        result = jdata['result']
        json.dump(result, scene)

    return "success"


@app.route('/saveDigitalTwinNew/', methods=['POST', 'GET'])
@cross_origin()
def saveDigitalTwinNew():
    jdata = request.get_data()
    jdata = json.loads(jdata)
    pre = jdata['pre']
    newname = jdata['newname']
    name = jdata['name']
    data = jdata['data']
    links = jdata['links']
    jsondata = {'data': data, 'links': links}

    with open(data_home + "ns3/series/" + str(name) + ".json", 'w') as series:
        json.dump(jsondata, series)

    with open(data_home + "ns3/scene/" + str(name) + ".json", 'w') as scene:
        result = jdata['result']
        json.dump(result, scene)

    db = DbMysql()
    sql = 'select DISTINCT pcap from topopcap where topo = "' + str(pre) + '"'
    datas = list(db.find(sql))
    for i in datas:
        db.insert("topopcap", 0, str(newname), str(i[0]))

    return "success"


@app.route('/updatePcapList/', methods=['POST', 'GET'])
@cross_origin()
def updatePcapList():
    jdata = request.get_data()
    jdata = json.loads(jdata)
    filename = jdata['filename']
    topo = jdata['topo']
    db = DbMysql()
    db.insert("topopcap", 0, str(topo), str(filename))
    db = pymysql.connect(host='127.0.0.1',
                             user='root',
                             password='123456',
                             database='ns3')
    cursor = db.cursor()
    sql = "delete from topopcap where topo='" + topo + "' and pcap is NULL"
    cursor.execute(sql)
    db.commit()
    cursor.close()
    db.close()
    return "success"


@app.route('/deletePcap/', methods=['POST', 'GET'])
@cross_origin()
def deletePcap():
    jdata = request.get_data()
    jdata = json.loads(jdata)
    pcap = jdata['pcap']
    topo = jdata['topo']
    db = DbMysql()
    sql = 'select DISTINCT pcap from topopcap where topo = "' + str(topo) + '"'
    datas = list(db.find(sql))
    if (len(datas) >= 2):
        db = pymysql.connect(host='127.0.0.1',
                             user='root',
                             password='123456',
                             database='ns3')
        cursor = db.cursor()
        sql = "delete from topopcap where pcap='" + pcap + "' and topo = '" + topo + "'"
        cursor.execute(sql)
        db.commit()
        cursor.close()
        db.close()
    else:
        db = pymysql.connect(host='127.0.0.1',
                             user='root',
                             password='123456',
                             database='ns3')
        cursor = db.cursor()
        sql = "update topopcap  set pcap = null where topo='" + topo + "'"
        cursor.execute(sql)
        db.commit()
        cursor.close()
        db.close()

    return "success"


@app.route('/deleteTopo/', methods=['POST', 'GET'])
@cross_origin()
def deleteTopo():
    jdata = request.get_data()
    jdata = json.loads(jdata)
    topo = jdata['topo']
    db = pymysql.connect(host='127.0.0.1',
                         user='root',
                         password='123456',
                         database='ns3')
    cursor = db.cursor()
    sql = "delete from topopcap where topo='" + topo + "'"
    cursor.execute(sql)
    db.commit()
    cursor.close()
    db.close()
    return "success"


@app.route('/getTopoListIntrusion/', methods=['POST', 'GET'])
@cross_origin()
def getTopoListIntrusion():
    db = DbMysql()
    sql = 'select DISTINCT topo from topopcap order by topo;'
    datas = list(db.find(sql))
    jsondata = []
    for i in datas:
        tmpdata = {
            "label": str(i[0]),
            "value": str(i[0])
        }
        jsondata.append(tmpdata)
    # f = open(os.getcwd() + "/scratch/topolist.txt", "r", encoding = "gb2312")
    # data = json.load(f)
    res = {
        'data': jsondata
    }
    return res


@app.route('/getPcapListIntrusion/', methods=['POST', 'GET'])
@cross_origin()
def getPcapListIntrusion():
    jdata = request.get_data()
    jdata = json.loads(jdata)
    topo = str(jdata['topo'])
    db = DbMysql()
    sql = 'select DISTINCT pcap from topopcap where topo = "' + str(topo) + '"'
    datas = list(db.find(sql))
    jsondata = []
    for i in datas:
        tmpdata = {
            "label": str(i[0]),
            "value": str(i[0])
        }
        jsondata.append(tmpdata)
    # f = open(os.getcwd() + "/scratch/pcaplist.txt", "r", encoding = "gb2312")
    # data = json.load(f)
    res = {
        'data': jsondata
    }
    return res


@app.route('/getDigitalTwin/', methods=['POST', 'GET'])
@cross_origin()
def getDT():
    jdata = request.get_data()
    jdata = json.loads(jdata)
    curTopo = str(jdata['curTopo'])
    if (curTopo == '-1'):
        curTopo = 'test'
    with open(data_home + "ns3/series/" + str(curTopo) + ".json", 'r') as series:
        jdata = json.load(series)
    return jdata


@app.route('/upLoadPcapTwin/', methods=['POST', 'GET'])
@cross_origin()
def upLoadPcap():
    f = request.files['file']
    name = f.__dict__.get("filename")
    f.save(data_home + "ns3/pcap/" + str(name))
    return "success"


@app.route('/runDigitalTwin/', methods=['POST', 'GET'])
@cross_origin()
def runDT():
    # start plc
    start_plc()
    time.sleep(1)

    log_file = open("/root/ns3/ns-allinone-3.33/ns-3.33/scene_output.txt", 'w').close()
    jdata = request.get_data()
    jdata = json.loads(jdata)
    curPcap = jdata['curPcap']
    curTopo = jdata['curTopo']
    open("./scratch/topopcapcfg.json", 'w').close()
    cfg = {
        "topo": curTopo,
        "pcap": curPcap
    }
    with open("./scratch/topopcapcfg.json", 'w') as series:
        json.dump(cfg, series)
    # run
    loadPcap(curPcap)
    os.system('./waf --run scratch/scene 1> ' + ns3_home + 'scene_output.txt')
    time.sleep(3)
    with open(ns3_home + "scene_output.txt", 'r', encoding='utf-8') as infile:
        out_puts = infile.readlines()
        pac_list = []
        print("-----------------------------------------------------------------")
        for line in out_puts:
            # if "Sending packet:" in line:
            #     pac = {}
            #     line = line[:-1]  # remove \n
            #     line = line.split(' ')
            #     pac["time"] = line[4][1:-1]
            #     pac["src"] = line[6]
            #     pac["sport"] = line[8]
            #     pac["dst"] = line[13]
            #     pac["dport"] = line[15]
            #     pac["size"] = line[10]
            #     pac["action"] = '0'
            #     pac_list.append(pac)
            #     print(line)
            if "Master sending packet:" in line:
                pac = {}
                line = line[:-1]  # remove \n
                line = line.split(' ')
                pac["time"] = line[5][1:-1]
                pac["src"] = line[7]
                pac["sport"] = line[9]
                pac["dst"] = line[14]
                pac["dport"] = line[16]
                pac["size"] = line[11]
                pac["action"] = '0'
                pac_list.append(pac)
                print(line)
            elif "Slave sending packet" in line:
                pac = {}
                line = line[:-1]  # remove \n
                line = line.split(' ')
                pac["time"] = line[5][1:-1]
                pac["src"] = line[7]
                pac["sport"] = line[9]
                pac["dst"] = line[14]
                pac["dport"] = line[16]
                pac["size"] = line[11]
                pac["action"] = '3'
                pac_list.append(pac)
                print(line)
            # elif "Received packet:" in line:
            #     pac = {}
            #     line = line[:-1]  # remove \n
            #     line = line.split(' ')
            #     pac["time"] = line[4][1:-1]
            #     pac["src"] = line[13]
            #     pac["sport"] = line[15]
            #     pac["dst"] = line[6]
            #     pac["dport"] = line[8]
            #     pac["size"] = line[10]
            #     pac["action"] = '1'
            #     pac_list.append(pac)
            #     print(line)
            elif "Master received packet:" in line:
                pac = {}
                line = line[:-1]  # remove \n
                line = line.split(' ')
                pac["time"] = line[5][1:-1]
                pac["src"] = line[14]
                pac["sport"] = line[16]
                pac["dst"] = line[7]
                pac["dport"] = line[9]
                pac["size"] = line[11]
                pac["action"] = '1'
                pac_list.append(pac)
                print(line)
            elif "Slave received packet:" in line:
                pac = {}
                line = line[:-1]  # remove \n
                line = line.split(' ')
                pac["time"] = line[5][1:-1]
                pac["src"] = line[14]
                pac["sport"] = line[16]
                pac["dst"] = line[7]
                pac["dport"] = line[9]
                pac["size"] = line[11]
                pac["action"] = '4'
                pac_list.append(pac)
                print(line)
            elif "Drop packet:" in line:
                pac = {}
                line = line[:-1]  # remove \n
                line = line.split(' ')
                pac["time"] = line[4][1:-1]
                pac["src"] = line[6]
                pac["sport"] = line[10]
                pac["dst"] = line[8]
                pac["dport"] = line[12]
                pac["action"] = '2'
                pac["size"] = line[18]
                pac_list.append(pac)
                print(line)
    ret = {}
    ret["packets"] = loadPackets()
    ret["logs"] = pac_list
    ret = jsonify(ret)
    # stop plc and get log
    writelog()
    time.sleep(3)
    stop_plc()

    return ret


def start_plc():
    os.system('sh ' + openplc_home + 'start_plc.sh')


def writelog():
    os.system('sh ' + openplc_home + 'writelog_plc.sh')


def stop_plc():
    os.system('sh ' + openplc_home + 'stop_plc.sh')


@app.route('/getPlcLogIntrusion/', methods=['POST', 'GET'])
@cross_origin()
def getPlcLogIntrusion():
    f = open(openplc_home + 'plclog.txt', 'r')
    content = f.read()
    res = {
        'content': content
    }
    return res


@app.route('/getDigitalTwinLogIntrusion/', methods=['POST', 'GET'])
@cross_origin()
def getDigitalTwinLogIntrusion():
    res = []
    with open(ns3_home + "scene_output.txt", 'r', encoding='utf-8') as infile:
        out_puts = infile.readlines()
        for line in out_puts:
            if 'AnimationInterface' in line:
                continue
            else:
                res.append(line)
    res = {
        'content': res
    }
    return res


# def runDT():
#     # run
#     loadPcap()
# 
#     log_file = open("/home/cz/desktop/ns-allinone-3.33/ns-3.33/scene_output.txt", 'w').close()
#     os.system('./waf --run scratch/scene 1> /home/cz/desktop/ns-allinone-3.33/ns-3.33/scene_output.txt')
#     time.sleep(3)
#     with open("/home/cz/desktop/ns-allinone-3.33/ns-3.33/scene_output.txt", 'r', encoding='utf-8') as infile:
#         out_puts = infile.readlines()
#         pac_list = []
#         print("-----------------------------------------------------------------")
#         for line in out_puts:
#             if "Sending packet:" in line:
#                 pac = {}
#                 line = line[:-1]  # remove \n
#                 line = line.split(' ')
#                 pac["time"] = line[4][1:-1]
#                 pac["src"] = line[6]
#                 pac["sport"] = line[8]
#                 pac["dst"] = line[13]
#                 pac["dport"] = line[15]
#                 pac["size"] = line[10]
#                 pac["action"] = '0'
#                 pac_list.append(pac)
#                 print(line)
#             elif "Received packet:" in line:
#                 pac = {}
#                 line = line[:-1]  # remove \n
#                 line = line.split(' ')
#                 pac["time"] = line[4][1:-1]
#                 pac["src"] = line[13]
#                 pac["sport"] = line[15]
#                 pac["dst"] = line[6]
#                 pac["dport"] = line[8]
#                 pac["size"] = line[10]
#                 pac["action"] = '1'
#                 pac_list.append(pac)
#                 print(line)
#             elif "Drop packet:" in line:
#                 pac = {}
#                 line = line[:-1]  # remove \n
#                 line = line.split(' ')
#                 pac["time"] = line[4][1:-1]
#                 pac["src"] = line[6]
#                 pac["sport"] = line[10]
#                 pac["dst"] = line[8]
#                 pac["dport"] = line[12]
#                 pac["action"] = '2'
#                 pac["size"] = line[18]
#                 pac_list.append(pac)
#                 print(line)
#     ret = {}
#     ret["packets"] = loadPackets()
#     ret["logs"] = pac_list
#     ret = jsonify(ret)
#     return ret

@app.route('/getPcapResultByTaskNodeIntrusion/', methods=['POST', 'GET'])
@cross_origin()
def getPcapResultByTaskNode():
    db = DbMysql()
    data = json.loads(request.get_data())['msg']
    task = data['task']
    node_index = data['nodeindex']
    sql = 'select * from alert_json where task = "' + task + '" and nodeindex = ' + str(node_index)
    datas = db.find(sql)
    res = {
        'msg': sql_to_json(datas)
    }
    return res


@app.route('/getTaskAllresultIntrusion/', methods=['POST', 'GET'])
@cross_origin()
def getTaskAllresult():
    db = DbMysql()
    data = json.loads(request.get_data())['msg']
    task = data['task']
    sql = 'select * from alert_json where task = "' + task + '"'
    datas = db.find(sql)
    res = {
        'msg': sql_to_json(datas)
    }
    return res


@app.route('/getPcapResultByTaskIntrusion/', methods=['POST', 'GET'])
@cross_origin()
def getPcapResultByTask():
    db = DbMysql()
    data = json.loads(request.get_data())['msg']
    task = data['task']
    sql = 'select * from alert_json where task = "' + task + '"'
    datas = db.find(sql)
    print(sql)
    res = {
        'msg': sql_to_json(datas)
    }
    return res


@app.route('/getFullPcapByTaskNodeIntrusion/', methods=['POST', 'GET'])
@cross_origin()
def getFullPcapByTaskNode():
    data = json.loads(request.get_data())['msg']
    task = data['task']
    nodeindexs = get_all_node_index(task)
    path = data_home + 'pcap/' + task + '/'
    os.system('rm -rf ' + path + 'test.tar ' + path + 'pcap')
    os.system('mkdir ' + path + 'pcap')
    files = os.listdir(path)
    for file in files:
        for nodeindex in nodeindexs:
            if file.startswith(task) and file.split('-')[1] == str(nodeindex[0]):
                fullpath = path + file
                os.system('cp ' + fullpath + ' ' + path + 'pcap')
    cmd = 'cd ' + path + ' && tar cvf pcap.tar pcap'
    print(cmd)
    os.system(cmd)
    time.sleep(2)
    return send_file(path + 'pcap.tar', path)

def get_all_node_index(task):
    db = DbMysql()
    sql = 'select DISTINCT pcapNode from detection_node where task = "' + task + '" '
    print(sql)
    datas = db.find(sql)
    return datas

# @app.route('/getPcapByTaskNodeIntrusion/', methods=['POST', 'GET'])
# @cross_origin()
# def getPcapByTaskNode():
#     data = json.loads(request.get_data())['msg']
#     task = data['task']
#     nodeindex = get_node_index(task)
#     indexinpcap = data['indexinpcap']
#     path = data_home + 'pcap/' + task + '/'
#     file_name = getpcapbyindex(path, nodeindex, indexinpcap)
#     return send_file(path + file_name, path)


def getpcapbyindex(path, nodeindex, indexinpcap):
    curtime = str(time.time())
    pcap_name = path + str(nodeindex) + '.pcap'
    packets = rdpcap(pcap_name)
    cap = packets[int(indexinpcap)]
    cap_file_name = curtime + '.pcap'
    new_cap = PcapWriter(path + cap_file_name, append=True)
    new_cap.write(cap)
    return cap_file_name


class TextArea(object):
    def __init__(self):
        self.buffer = []

    def write(self, *args, **kwargs):
        self.buffer.append(args)


def get_node_index(task, nodeip):
    db = DbMysql()
    sql = 'select pcapNode from detection_node where task = "' + task + '" and detectIp = ' + '"'+ str(nodeip) + '" limit 1'
    print(sql)
    datas = db.find(sql)
    return datas[0][0]


@app.route('/getPcapDetailByTaskNodeIntrusion/', methods=['POST', 'GET'])
@cross_origin()
def getPcapDetailByTaskNode():
    data = json.loads(request.get_data())['msg']
    task = data['task']
    nodeip = data['nodeip']
    nodeindex = get_node_index(task, nodeip)
    indexinpcap = data['indexinpcap']
    path = data_home + 'pcap/' + task + '/'
    stdout = sys.stdout
    sys.stdout = TextArea()
    packets = rdpcap(path + str(nodeindex) + '.pcap')
    print(packets[int(indexinpcap)].show())
    text_area, sys.stdout = sys.stdout, stdout
    # print(text_area.buffer)
    # with open(path + str(nodeindex) + '_' + str(indexinpcap) + '.txt', 'w') as file0:
    #     print(packets[int(indexinpcap)].show(), file=file0)
    # f = open(path + str(nodeindex) + '_' + str(indexinpcap) + '.txt', 'r')
    content = text_area.buffer
    res = {
        'content': content
    }
    return res


def sql_to_json(datas):
    res = []
    for i in datas:
        content = {
            "index": i[0], "task": i[1],"nodeindex": i[2],"nodeip":i[3], "indexInPcap": i[4], "seconds": i[5], "action": i[6],"class": i[7], "dir": i[8], "dst_addr": i[9], "dst_ap": i[10], "dst_port": i[11],
            "eth_dst": i[12], "eth_len": i[13], "eth_src": i[14], "eth_type": i[15], "gid": i[16], "iface": i[17],
            "ip_id": i[18], "ip_len": i[19], "msg": i[20], "mpls": i[21], "pkt_gen": i[22],
            "pkt_num": i[24], "priority": i[25], "proto": i[26], "rev": i[27], "rule": i[28], "service": i[29],
            "sid": i[30], "src_addr": i[31], "src_ap": i[32], "src_port": i[33], "tcp_ack": i[34],
            "tcp_flags": i[35], "tcp_len": i[36], "tcp_seq": i[37], "tcp_win": i[38], "tos": i[39], "ttl": i[40],
            "vlan": i[41], "timestamp": i[42], "pcap_path": i[43]}
        res.append(content)
    return res


def ConfigureOfRule(rules):
    open(data_home + "rules/rules.rules", 'w').close()
    sid = 2000000
    for rule in rules:
        # rule header
        IP_Orin = rule['IP_Orin']
        IP_Dest = rule['IP_Dest']
        portOrin = rule['portOrin']
        portDest = rule['portDest']
        Actions = rule['Action']
        for Action in Actions:
            operator = rule['operator']
            prots = rule['prot']

            for prot in prots:

                ruleHeader = str(Action) + ' ' + str(prot) + ' ' + str(IP_Orin) + ' ' + \
                             str(portOrin) + ' ' + str(operator) + ' ' + str(IP_Dest) + ' ' + str(portDest)

                # rule options
                ruleOptions = ''
                if 'message' in rule:
                    msg = rule['message']
                    if (msg != ''):
                        ruleOptions = ruleOptions + 'msg:"' + str(msg) + '";'

                if 'pcre' in rule:
                    pcre = rule['pcre']
                    if (pcre != ''):
                        ruleOptions = ruleOptions + 'pcre:"' + str(pcre) + '";'

                if 'http' in rule:
                    httpOption = rule['http']
                    if (httpOption != ''):
                        ruleOptions = ruleOptions + 'http:' + str(httpOption) + ';'

                if 'content' in rule:
                    content = rule['content']
                    if (content != ''):
                        ruleOptions = ruleOptions + 'content:"' + str(content) + '";'

                if 'classtype' in rule:
                    classtype = rule['classtype']
                    if (classtype != ''):
                        ruleOptions = ruleOptions + 'classtype:' + str(classtype) + ';'

                if 'rev' in rule:
                    rev = rule['rev']
                    if (rev != ''):
                        ruleOptions = ruleOptions + 'rev:' + str(rev) + ';'

                # if 'metadata' in rule:
                #     insertMetaDta(sid, rule['metadata'])

                if 'flow' in rule:
                    if (len(rule['flow']) != 0):
                        flowTos = rule['flow']
                        for flowTo in flowTos:
                            ruleOptions = ruleOptions + 'flow:' + str(flowTo) + ';'

                            ruleOptions = ruleOptions + 'sid:' + str(sid) + ';'
                            # rule
                            data = ruleHeader + '(' + ruleOptions + ')' + '\n'

                            with open(data_home + 'rules/rules.rules', 'a') as file_rules:
                                file_rules.write(data)

                            sid += 1
                    else:
                        ruleOptions = ruleOptions + 'sid:' + str(sid) + ';'
                        # rule
                        data = ruleHeader + '(' + ruleOptions + ')' + '\n'

                        with open('/usr/local/etc/rules/rules.rules', 'a') as file_rules:
                            file_rules.write(data)

                        sid += 1


def insertMetaDta(sid, metadata):
    dic = (metadata)
    m = {
        'sid': sid
    }
    dic.update(m)
    keys = ','.join(dic.keys())
    valuesTuple = tuple(dic.values())
    values = ','.join(['%s'] * len(dic))
    table = 'rule_metadata'
    insertSql = 'INSERT INTO {table}({keys}) VALUES ({values})'.format(table=table, keys=keys, values=values)
    sql_operation(insertSql, valuesTuple)


def sql_operation(sql, values):
    db = pymysql.connect(host='127.0.0.1',
                         user='user',
                         password='123456',
                         database='ns3')
    cursor = db.cursor()
    if (values == 0):
        cursor.execute(sql)
    else:
        cursor.execute(sql, values)
    db.commit()
    cursor.close()
    db.close()


@app.route('/configRulesIntrusion/', methods=['POST', 'GET'])
@cross_origin()
def ConfigureOfRules():
    data = json.loads(request.get_data())['rules']
    with open(os.getcwd() + "/scratch/rule.txt", "w", encoding='gbk') as fp:
        fp.write(json.dumps(data).encode('utf-8').decode('unicode_escape'))

    # clear previous metadata
    clear_sql = 'DELETE FROM rule_metadata'
    sql_operation(clear_sql, 0)

    ConfigureOfRule(data)
    res = {
        'msg': 'success'
    }
    return res


@app.route('/getRulesIntrusion/', methods=['POST', 'GET'])
@cross_origin()
def getrules():
    f = open(os.getcwd() + "/scratch/rule.txt", "r", encoding="gb2312")
    data = json.load(f)
    res = {
        'rules': data
    }
    return res


@app.route('/getRuleMetadataIntrusion/', methods=['POST', 'GET'])
@cross_origin()
def getRuleMetadataIntrusion():
    db = DbMysql()
    sid = json.loads(request.get_data())['sid']
    sql = 'select * from rule_metadata where sid = ' + str(sid)
    datas = db.find(sql)[0]
    print(datas)
    res = {
        'metadata': {
            'sid': datas[1],
            'created_at': datas[2],
            'updated_at': datas[3],
            'attack_target': datas[4],
            'affected_product': datas[5],
            'subtype': datas[6],
            'event': datas[7],
            'signature_severity': datas[8],
            'signature_reliability': datas[9],
            'attack_phase': datas[10],
            'attack_status': datas[11],
            'module': datas[12],
        }
    }
    return res


@app.route('/getIllegalConnection/', methods=['POST', 'GET'])
@cross_origin()
def getIllegalConnection():
    print('\ngetIllegalConnection\n')
    db = DbMysql()
    sql ='select * from illegal_connection'
    datas = db.find(sql)
    illegal_ins = []
    for data in datas:
        i = {
            'src': data[0],
            'dst': data[1],
            'ts':data[2],
            'dport':data[3],
            'sport':data[4],
            'protocle':data[6],
        }
        illegal_ins.append(i)
    res = {
        'msg': illegal_ins
    }
    return res

@app.route('/getCrossOrigin/', methods=['POST', 'GET'])
@cross_origin()
def getCrossOrigin():
    print('\ngetCrossOrigin\n')
    db = DbMysql()
    sql ='select * from cross_origin'
    datas = db.find(sql)
    cross_origin_list = []
    for data in datas:
        i = {
            'src': data[0],
            'dst': data[1],
            'ts': data[4],
            'dport':data[2],
            'sport': data[3],
            'protocle':data[6],
        }
        cross_origin_list.append(i)
    res = {
        'msg': cross_origin_list
    }
    print(res)
    return res

def startServer():
    # start openplc
    # os.system('sh /home/cz/desktop/OpenPLC_v3/start_openplc.sh')
    app.run(host='0.0.0.0',
            port=8066, debug=False)


##############################################################################
import binascii
import codecs


def loadPcap(curPcap):
    """
    load pcap file to generate instrucsion list as:
    {
    'load': '0000000000070b0204cd6bb205',
    'src': '10.1.1.1',
    'dst': '10.1.2.2',
    'ts': '4.010638',
    'dport': 49153,
    'sport': 502
    }
    """
    ins_list = []
    udpins_list = []
    modbusins_list = []
    tcpins_list = []
    tcpsins_list = []
    packets = rdpcap(data_home + "ns3/pcap/" + str(curPcap))
    
    minTime = 999999999999
    for data in packets:
        if 'Raw' in data:
            minTime = min(data.time, minTime)
            ins = {}
            src = data['IP'].src
            dst = data['IP'].dst
            ins['src'] = src
            ins['dst'] = dst
            ins['sport'] = data['UDP'].sport
            ins['dport'] = data['UDP'].dport
            ins['ts'] = str(data.time) + "s"
            ins['load'] = codecs.encode(data['Raw'].load, 'hex').decode('ascii')
            ins_list.append(ins)
        if 'UDP' in data:
            if 'Raw' in data:
                #s = repr(data)
                ins = {}
                src = data['IP'].src
                dst = data['IP'].dst
                ins['src'] = src
                ins['dst'] = dst
                # if src == '192.9.200.101' :
                #     src = '192.9.220.101'
                # if dst == '192.9.200.134' :
                #     dst = '192.9.220.134'
                ins['sport'] = data['UDP'].sport
                ins['dport'] = data['UDP'].dport
                ins['load'] = codecs.encode(data['Raw'].load, 'hex').decode('ascii')
                # ins['load'] = data['Raw'].load.decode()binascii.b2a_hex
                #ins['ts'] = str(data.time - minTime) + "s"
               
                udpins_list.append(ins)

        #modbus提取
        if 'TCP' in data and data[TCP].dport == 502:
            if 'Raw' in data[TCP]:
                s = repr(data)
                ins = {}
                ins['src'] = data['IP'].src
                ins['dst'] = data['IP'].dst
                ins['sport'] = data['TCP'].sport
                ins['dport'] = data['TCP'].dport
                ins['load'] = codecs.encode(data['Raw'].load, 'hex').decode('ascii')
                # ins['load'] = data['Raw'].load.decode()binascii.b2a_hex
                ins['ts'] = str(data.time) + "s"
                modbusins_list.append(ins)


        #TCP全部提取
        if 'TCP' in data:
            s = repr(data)
            ins = {}
            ins['src'] = data['IP'].src
            ins['dst'] = data['IP'].dst
            ins['sport'] = data['TCP'].sport
            ins['dport'] = data['TCP'].dport
            if 'Raw' in data[TCP]:
                ins['load'] = codecs.encode(data['Raw'].load, 'hex').decode('ascii')
                # ins['load'] = data['Raw'].load.decode()binascii.b2a_hex
            else:
                ins['load'] = ""
            ins['ts'] = str(data.time) + "s"
            tcpins_list.append(ins)

        #TCP请求指令提取
        if 'TCP' in data and data[TCP].flags & 0x02 and data[TCP].ack == 0:
            s = repr(data)
            ins = {}
            ins['src'] = data['IP'].src
            ins['dst'] = data['IP'].dst
            ins['sport'] = data['TCP'].sport
            ins['dport'] = data['TCP'].dport
            if 'Raw' in data[TCP]:
                ins['load'] = codecs.encode(data['Raw'].load, 'hex').decode('ascii')
                # ins['load'] = data['Raw'].load.decode()binascii.b2a_hex
            else:
                ins['load'] = ""
            ins['ts'] = str(data.time) + "s"
            tcpsins_list.append(ins)

        else:
            pass
    
    json_data = json.dumps(udpins_list)
    with open('udp_ins,json','w') as file:
        file.write(json_data)
    
    json_data1 = json.dumps(modbusins_list)
    with open('modbus_ins.json', "w") as ins_file:
        ins_file.write(json_data1)
    
    json_data2 = json.dumps(tcpins_list)
    with open('tcp_ins.json', "w") as ins_file:
        ins_file.write(json_data2)
    
    json_data3 = json.dumps(tcpsins_list)
    with open('tcps_ins.json', "w") as ins_file:
        ins_file.write(json_data3)
    
    findCrossOrigin(ins_list)
    findIllegalConnectionFromPcap()
    '''
    json_data = json.dumps(ins_list)
    with open('ins.json', "w") as ins_file:
        ins_file.write(json_data)
    '''

def loadPackets():
    """
    load packet traces from a xml file generated by ns3.
    """
    domtree = xml.dom.minidom.parse('packets.xml')
    pac_collection = domtree.documentElement
    pac_list = []
    for pac in pac_collection.getElementsByTagName("p"):
        buf = {}
        if pac.hasAttribute('fId'):
            buf['fId'] = pac.getAttribute("fId")
        if pac.hasAttribute('tId'):
            buf['tId'] = pac.getAttribute("tId")
        if pac.hasAttribute('fbTx'):
            buf['fTm'] = pac.getAttribute("fbTx")
        if pac.hasAttribute('fbRx'):
            buf['tTm'] = pac.getAttribute("fbRx")
        pac_list.append(buf)
    return pac_list

def findIllegalConnectionFromPcap():
    print('begin findIllegalConnection\n')
    net_segment = []
    #找到本地网段
    print('begin'+'\n')
    #with open(data_home + 'ns3/scene/1.json' , "r") as target:
    with open(data_home + 'ns3/scene/testwailian.json' , "r") as target:
        jdata = json.load(target)#到处成字典模式
        deviceData = jdata['deviceInfo']
        for key in deviceData:
            ipStr = key['ip']
            print(ipStr)
            if (ipStr.find('/') != -1):
                ipList = ipStr.split('/')
                '''
                print(ipList)
                ip_1 = ipList[0].split('.')
                ip_2 = ipList[1].split('.')
                net1 = ip_1[0] +'.'+ ip_1[1] +'.'+ ip_1[2] +'.'+'0'
                net2 = ip_2[0] +'.'+ ip_2[1] +'.'+ ip_2[2] +'.'+'0'
                '''
                net1 = findNetSegment(ipList[0])
                net2 = findNetSegment(ipList[1])
                if net1 not in net_segment:
                    net_segment.append(net1)
                if net2 not in net_segment:
                    net_segment.append(net2)
    print(net_segment)
    print('success1'+'\n')
    #读取跨网段访问的ip
    db = DbMysql()
    sql = 'select * from cross_origin'
    datas = db.find(sql)#datas是一个多元组
    print('excute SQL'+'\n')
    print(datas)
    #如果不在net_segment中，非法访问
    for line in datas:
        net1 = findNetSegment(line[0])
        net2 = findNetSegment(line[1])
        if (net1 not in net_segment) or (net2 not in net_segment):
            partOfSQL = '\''+line[0]+'\',\''+line[1]+'\',\''+line[2]+'\',\''+line[3]+'\',\''+line[4]+'\''
            sql = 'insert into illegal_connection(src,dst,dport,sport,ts) values('+partOfSQL+')'
            print(sql)
            sql_operation(sql,0)

def findCrossOrigin(ins_list):
    print('begin findCrossOrigin\n')
    for key in ins_list:
        ipSrc = key['src']
        ipDst = key['dst']
        ipSrc_net = findNetSegment(ipSrc)
        ipDst_net = findNetSegment(ipDst)
        #插入数据库时没有考虑数据的重复，可能运行两次以后数据库会有许多条重复的数据。可能以后需要改进。
        if (ipSrc_net != ipDst_net):
            partOfSQL = '\''+key['src']+'\',\''+key['dst']+'\',\''+str(key['sport'])+'\',\''+str(key['dport'])+'\',\''+str(key['ts'])+'\''
            sql = 'insert into cross_origin(src,dst,sport,dport,ts) values('+partOfSQL+')'
            print(sql)
            sql_operation(sql,0)
        else:
            pass


def findNetSegment(ipIns):
    ip_1 = ipIns.split('.')
    res_net = ip_1[0] +'.'+ ip_1[1] +'.'+ ip_1[2] +'.'+'0'
    return res_net


if __name__ == '__main__':
    #startServer()
    #ins_list=[]
    packets = rdpcap('/root/snort/etc/ns3/pcap/tpncp_udp.pcap')
    #packets = rdpcap(data_home + "ns3/pcap/" + str(curPcap))
    print(packets[0].mysummary)
    print(packets[1].mysummary)

    pass

