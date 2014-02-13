#!/usr/bin/env python
#coding:utf-8

__author__ = 'York Wong'
__email__ = 'eth2net [at] gmail.com'
__date__ = '2013/04/27'

import sys


class Record(object):
    def __init__(self, head):
        self.head = head
        self.rtype = self._determine_type()
        self.record = []
        self.timestamp = self._determine_time()

    def _determine_time(self):
        return ''

    def _determine_type(self):
        #print self.head
        h_set = set(self.head)
        #print h_set
        #print set(['proc/s']) & h_set
        #print set(['cswch/s']) & h_set

        #print set(['%iowait', '%idle']) & h_set
        if set(['%iowait', '%idle']) & h_set:
            rtype = 'CPU'

        #elif set(['proc/s']) & h_set:
            #rtype = 'proc'

        #elif set(['cswch/s']) & h_set:
            #rtype = 'cswch'

        #elif set(['intr/s']) & h_set:
            #rtype = 'intr'

        #elif set(['pswpin/s', 'pswpout/s']) & h_set:
            #rtype = 'pswp'
        else:
            rtype = 'ignore'

        return rtype


def __interrupt(saroutput):
    'interrupts the sar output and returns in a nice format'
    results = saroutput.split('\n')
    # remove our header and first blank line
    header = results.pop(0)
    results.pop(0)

    # sar report need at least 3 lines to parse data
    if len(results) > 3:
        keys = results.pop(0).split()
        keys[0] = 'timestamp'  # rename actual timestamp with a key name
    else:
        raise Exception('''Sar Output does not appear to be over 5 lines,
this means not enough data to run report''')

    # create a list of dicts for our data
    output = []
    IS_KEY = False

    record_list = []
    r = Record(keys)
    oldkeys = ''

    for line in results:
        if line != '':  # skip blank lines
            if IS_KEY:  # determin it's table head or not
                keys = line.split()
                keys[0] = 'timestamp'
                IS_KEY = False
                if keys == oldkeys:
                    print 'here'
                    pass
                elif r.rtype != 'ignore':
                    record_list.append(r)
                    r = Record(keys)
                    #print r.rtype

            if r.rtype == 'ignore':
                continue

            if line.split()[1:] != keys[1:]:  # skip header lines
                if line.split()[0] != 'Average:':  # skip the end average
                    data = line.split()

                    # be sure our key and data are the same length
                    if len(keys) != len(data):
                        #print output
                        raise Exception("Keys and data are not of the same length")

                    d = {}
                    for i in range(len(data)):
                        d[keys[i]] = data[i]
                    #output.append(d)
                    r.record.append(d)
        else:
            IS_KEY = True
            oldkeys = keys

    #return output
    return record_list

if __name__ == '__main__':
    saroutput = open(sys.argv[1], 'r').read()
    output = __interrupt(saroutput)
    all_sys = []
    timeset = []
    #print output
    #print len(output)
    #for i in output:
        #print i.rtype
        #print i.record
    for i in output[0].record:
        if i['CPU'] == 'all':
            timeset.append(i['timestamp'])
            all_sys.append(i['%sys'])

    print all_sys
