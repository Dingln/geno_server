"""
Functions for I/O
"""

import psutil

def write_file(data, filename):
    with open(filename, 'a+') as f:
        f.write(str(data) + "\n")

def load_dev_port(dev_file, port_file):
    dev_list = load_list(dev_file)
    port_list = load_list(port_file)
    dev_dict = dict()

    for (dev, port) in zip(dev_list, port_list):
        dev_dict[int(dev)] = int(port)

    return dev_dict, dev_list, port_list


def load_list(filename):
    try:
        return [int(line.rstrip('\n')) for line in open(filename, 'r+')]
    except FileNotFoundError:
        return []


def update_pid(pidList, filename):
    with open(filename, 'w+') as pid_file:
        for pid in pidList:
            pid_file.write(str(pid) + "\n")


def kill_port(port_num):
    cmd_str = "lsof -i:" + str(port_num) + " | grep Python"
    tmp = os.popen(cmd_str)
    tmpout = tmp.readlines()

    if tmpout:
        pid = tmpout[0][8:13]
        psutil.Process(pid).kill()
