import sys
import os
import psutil


#此程序主要用于训练rasa model
#输入参数：
# id: dev ID;
# training_data: 训练数据（intent，exmmple，entity+value）
#   训练数据格式：
    # ## intent:check_balance
    # - what is my balance <!-- no entity -->
    # - how much do I have on my [savings](source_account) <!-- entity "source_account" has value "savings" -->
    # - how much do I have on my [savings account](source_account:savings) <!-- synonyms, method 1-->
    # - Could I pay in [yen](currency)?  <!-- entity matched by lookup table -->


#注：rasa服务器的训练数据位置：
# 工程文件夹下，每个model及其data处在同一个独立的文件夹中


def write_file(dev_str, filename):
    dev_file = open(filename, 'a')
    dev_file.write(dev_str)
    dev_file.write("\n")
    dev_file.close()


def load_port(f):
    port_list = []
    port_file = open(f, 'r')
    for line in port_file.readlines():
        port_list.append(line.split('\n')[0])
    port_file.close()
    return port_list


def write_port(port_str, f):
    port_file = open(f, 'a')
    port_file.write(port_str)
    port_file.write("\n")
    port_file.close()


def load_dev_port(dev_file, port_file):
    dev_list = load_devList(dev_file)
    port_list = load_port(port_file)
    dev_dict = dict()
    if len(dev_list) != 0:
        for i in range(len(dev_list)):
            dev_dict[dev_list[i]] = port_list[i]
    return dev_dict, dev_list, port_list


def load_devList(filename):
    dev_list = []
    dev_file = open(filename, 'r')
    for line in dev_file.readlines():
        dev_list.append(line.split('\n')[0])
    dev_file.close()
    return dev_list


def load_pidList(filename):
    pid_list = []
    pid_file = open(filename, 'r')
    for line in pid_file.readlines():
        pid_list.append(line.split('\n')[0])
    pid_file.close()
    return pid_list


def write_pid(pid, filename):
    pid_file = open(filename, 'a')
    pid_file.write(str(pid) + "\n")
    pid_file.close()


def update_pid(pidList, filename):
    pid_file = open(filename, 'w')
    for pid in pidList:
        pid_file.write(str(pid) + "\n")
    pid_file.close()


def kill_pro(cur_pid):
    pids = psutil.pids()
    for pid in pids:
        if pid == cur_pid:
            os.popen("kill -9 " + str(pid))


def kill_port(portnum):
    tmp = os.popen("lsof -i:5005 | grep Python")
    tmpout = tmp.readlines()
    if(len(tmpout) == 0):
        return
    pid = tmpout[0][8:13]
    os.popen("kill -9 " + pid)


cur_pid = os.getpid()
old_pid = -1

id = sys.argv[1]
training_data = sys.argv[2]

#检查dev是否已存在（读txt文件，遍历寻找）
dev_dict, dev_list, port_list = load_dev_port("devep_data/dev_list.txt", "devep_data/port_list.txt")
pid_list = load_pidList("devep_data/pid_list.txt")
# dev_list = load_devList("~/geno/devep_data/dev_list.txt")
exist=False
for tmp in dev_list:
    if int(tmp) == int(id):
        exist = True

dev_data_dir = "devep_data/dev_"+id
dev_model_dir = "devep_model/dev_"+id

#若不存在，则新建文件夹，并将名字加入list; 若已存在则不用添加
newport = "-1"
if (exist==False):
    os.mkdir(dev_data_dir)
    os.mkdir(dev_model_dir)
    #复制story进来
    os.popen("cp data/stories.md "+dev_data_dir+"/stories.md")
    write_file(id, "devep_data/dev_list.txt")
    if len(port_list) == 0:
        newport = "5005"
    else:
        newport = str(int(max(port_list))+1)
    write_port(newport, "devep_data/port_list.txt")
    write_pid(cur_pid,"devep_data/pid_list.txt")
else:
    #kill 进程
    newport = dev_dict[id]
    # kill_pro(newport)
    pid_index = dev_list.index(id)
    old_pid = pid_list[pid_index]
    os.popen("kill -9 "+str(old_pid))
    kill_port(newport)
    pid_list[pid_index] = cur_pid
    update_pid(pid_list, "devep_data/pid_list.txt")


#添加训练数据到相应文件中，并训练相应model
write_file(training_data, "devep_data/dev_"+id+"/nlu.md")

cmd = "cd ~/geno; rasa train --data "+dev_data_dir + " --out "+dev_model_dir
cmd_resp = os.popen(cmd)
# for tmp in cmd_resp.readlines():
#     print(tmp)

#运行rasa
run_cmd = "cd ~/geno; rasa run --enable-api -p "+newport+" -m "+dev_model_dir
run_cmd_resp = os.popen(run_cmd)
for tmp in run_cmd_resp.readlines():
    print(tmp)






