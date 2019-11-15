"""
functions of I/O
"""


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


def kill_port(port_num):
    cmd_str = "lsof -i:" + str(port_num) + " | grep Python"
    tmp = os.popen(cmd_str)
    tmpout = tmp.readlines()
    if (len(tmpout) == 0):
        return
    pid = tmpout[0][8:13]
    os.popen("kill -9 " + pid)