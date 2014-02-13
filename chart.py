#!/usr/bin/env python
#coding:utf-8

__author__ = 'York Wong'
__email__ = 'eth2net [at] gmail.com'
__date__ = '2013/08/04'

import os
import re
import sys
from pygal import Line
from pygal.style import NeonStyle
#from pygal.style import DarkSolarizedStyle

multidevtype = ['cpu', 'net_trans', 'net_err', 'diskio']
numblocktype = ['load', 'memswp', 'mem', 'pgswp', 'paging', 'swap']


def determine_block_type(keys):
    key_set = set(keys)
    if key_set & set(['%iowait', '%idle']):
        return 'cpu'

    if key_set & set(['ldavg-1', 'ldavg-5']):
        return 'load'

    if key_set & set(['pswpin/s', 'pswpout/s']):
        return 'pgswp'

    if set(['kbmemfree', 'kbswpfree']).issubset(keys):
        return 'memswp'

    if set(['kbmemfree', '%memused']).issubset(keys):
        return 'mem'

    if set(['kbswpfree', 'kbswpused']).issubset(keys):
        return 'swap'

    if key_set & set(['pgpgin/s', 'pgpgout/s']):
        return 'paging'

    if key_set & set(['rxpck/s', 'rxmcst/s']):
        return 'net_trans'

    if key_set & set(['rxerr/s', 'rxdrop/s']):
        return 'net_err'

    if key_set & set(['avgrq-sz', 'avgqu-sz']):
        return 'diskio'

    return 'ignore'


class BaseBlock(object):
    def __init__(self, line):
        self.blocktype = determine_block_type(line.split())
        self.block = {
            'timestamp': [],
        }
        self.graph = self._config_graph()

    def _config_graph(self):
        # config graph
        _g = Line()
        _g.js = [
            os.path.join(os.path.dirname(__file__), "svg.jquery.js"),
            os.path.join(os.path.dirname(__file__), "pygal-tooltips.js"),
        ]
        _g.width = 1000
        _g.label_font_size = 8
        _g.fill = True
        _g.x_label_rotation = 40
        _g.dots_size = 1.5
        _g.x_labels = self.block['timestamp']
        _g.show_minor_x_labels = False
        _g.logarithmic = True
        _g.style = NeonStyle

        return _g

    def insert(self, line):
        dentry = line.split()
        if dentry[0] not in self.block['timestamp']:
            self.block['timestamp'].append(dentry[0])

        for key in self.keys:
            p = self.block.setdefault(key, [])
            try:
                val = float(dentry[self.keys.index(key) + 1])
            except Exception, e:
                print line, e
                print 'dentry:', dentry
                print 'key:', key
                print 'index:', self.keys.index(key)
                sys.exit(1)
            p.append(val)

    def __repr__(self):
        return '<Block %s>' % self.blocktype


class NumBlock(BaseBlock):
    '''
    load_block = {
        'timestamp': [],
        'ldavg-1': [],
        'ldavg-5': [],
        'ldavg-15': [],
        'runq-sz': [],
        'plist-sz': [],
    }
    '''
    def __init__(self, line):
        super(NumBlock, self).__init__(line)
        if not re.match(r"^\d[^a-z]*\d$", line):
            self.keys = line.split()[1:]

    def get_graph(self, *args):
        self.graph = self._config_graph()
        for key in args:
            self.graph.add(key, self.block[key])
        self.graph.x_labels_major = self.graph.x_labels[::6]
        return self.graph


class MultiDevBlock(BaseBlock):
    '''
    cpu_block = {
        'timestamp': [],
        '0': {
            '%iowait':[],
            '%idle':[],
            },
        '1': {
            '%iowait':[],
            '%idle':[],
            },
        }
    '''
    def __init__(self, line):
        super(MultiDevBlock, self).__init__(line)
        if not re.match(r"^\d[^a-z]*\d$", line):
            self.keys = line.split()[2:]
        self.devlist = []

    def insert(self, line):
        dentry = line.split()
        if dentry[0] not in self.block['timestamp']:
            self.block['timestamp'].append(dentry[0])
        #dentry[1] is the device name
        dev_name = dentry[1]
        dev = self.block.setdefault(dev_name, {})

        if dev_name not in self.devlist:
            self.devlist.append(dev_name)

        for key in self.keys:
            try:
                val = float(dentry[self.keys.index(key) + 2])
            except Exception, e:
                print line, e
                print 'dentry:', dentry
                print 'key:', key
                print 'index:', self.keys.index(key)
                sys.exit(1)
            if key in dev:
                dev[key].append(val)
            else:
                dev[key] = [val]

    def get_dev_graph(self, dev, *args):
        self.graph = self._config_graph()
        if dev not in self.block and dev != 'timestamp':
            self.graph.no_data_text = 'No device found'
            self.graph.add('line', [])
            return self.graph
        for key in args:
            self.graph.add(key, self.block[dev][key])
        self.graph.x_labels_major = self.graph.x_labels[::6]
        return self.graph


def mkchart(log):
    sarblock = {}
    sys_info = {}
    dline_pattern = re.compile(r"^\d")
    #data_pattern = re.compile(r"^\d[^a-z]*\d$")
    data_pattern = re.compile(r"^\d[\S\s:]*[^a-z-/]{2,3}\d$")
    sarlog = open(log, "r")
    finish = False

    for line in sarlog:
        if line.startswith("Linux"):
            res = re.search(r"Linux\s(?P<kernel>2.6.\d+\S+?)\s+\((?P<hostname>\S+?)\)\s+?(?P<date>\S+).*", line)
            sys_info['kernel'] = res.group('kernel')
            sys_info['hostname'] = res.group('hostname')
            sys_info['date'] = res.group('date')
            #print sys_info

        if line == '\n':
            finish = True

        # determine the block type and initialize the struct
        if finish and dline_pattern.match(line):
            finish = False
            keys = line.split()
            keys[0] = 'timestamp'
            block_type = determine_block_type(line.split())

            if block_type != 'ignore':
                block = sarblock.get(block_type, None)
            else:
                block = None

            # if it's new type of block , create it
            if not block and block_type in multidevtype:
                block = MultiDevBlock(line)
                sarblock[block.blocktype] = block

            if not block and block_type in numblocktype:
                block = NumBlock(line)
                sarblock[block.blocktype] = block

            if line.endswith("RESTART\n"):
                sys_info['reboot'] = line.split()[0]

        # it's real data entry, insert the line to the block
        if not finish and data_pattern.match(line):
            if block_type != 'ignore':
                block = sarblock.get(block_type)
                block.insert(line)

    #TEST
    #TODO test the corrupted file
    assert len(sarblock['cpu'].block['1']['%iowait']) == len(sarblock['cpu'].block['timestamp'])

    assert len(sarblock['load'].block['ldavg-15']) == len(sarblock['load'].block['timestamp'])

    #print sarblock
    sarblock['sysinfo'] = sys_info
    return sarblock


if __name__ == '__main__':
    sarblock = mkchart(sys.argv[1])
    print sarblock
    print sarblock['cpu'].keys

    # CPU chart
    cpu = sarblock['cpu']
    cpu0_graph = cpu.get_dev_graph('all', '%usr', '%sys', '%iowait')
    cpu0_graph.title = 'CPU All'
    cpu0_graph.render_to_file("cpu_chart.svg")
    f = open("svg.html", "w")
    #f.write(cpu0_graph.render())
    f.write(cpu0_graph.render())
    f.close()

    load = sarblock['load']
    load_graph = load.get_graph('ldavg-1', 'ldavg-5', 'ldavg-15')
    load_graph.title = 'Load'
    load_graph.logarithmic = True
    load_graph.render_to_file("load_chart.svg")
    #load_graph.render_in_browser()
