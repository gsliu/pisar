#!/usr/bin/env python
#coding:utf-8

__author__ = 'York Wong'
__email__ = 'eth2net [at] gmail.com'
__date__ = '2013/08/24'

import sys

from flask import Flask
#from flask import redirect
from flask import render_template
from flask import Markup
from werkzeug.contrib.cache import SimpleCache

from chart import mkchart
app = Flask(__name__)
cache = SimpleCache()


@app.route('/')
def index():
    #if 'sb' not in session:
        #return 'Nothing'
    #sb = mkchart(app.config['file'])
    menu = app.config['menu']
    sb = app.config['sb']
    cpu = sb['cpu']
    if sb['sysinfo']['kernel'].startswith('2.6.32'):
        cpu0_graph = cpu.get_dev_graph('all', '%usr', '%sys', '%iowait')
    elif sb['sysinfo']['kernel'].startswith('2.6.18'):
        cpu0_graph = cpu.get_dev_graph('all', '%user', '%system', '%iowait')

    cpu0_graph.title = 'CPU All'
    svg = cpu0_graph.render(is_unicode=True)
    graph_list = []
    graph_list.append(Markup(svg))
    return render_template('index.html', **locals())


@app.route('/cpu/', defaults={'core_id': 'all'})
@app.route('/cpu/<core_id>')
def cpu(core_id):
    menu = app.config['menu']
    sb = app.config['sb']
    cpu = sb['cpu']

    graph_list = cache.get('cpu_graph_%s' % core_id)
    #print graph_list
    if graph_list is None:
        graph_list = []
        if sb['sysinfo']['kernel'].startswith('2.6.32'):
            _g = cpu.get_dev_graph(core_id, '%usr', '%sys', '%iowait')
        elif sb['sysinfo']['kernel'].startswith('2.6.18'):
            _g = cpu.get_dev_graph(core_id, '%user', '%system', '%iowait')
        _g.title = 'CPU %s' % core_id.capitalize()
        svg = _g.render(is_unicode=True)
        graph_list.append(Markup(svg))
        cache.set('cpu_graph_%s' % core_id, graph_list, timeout=5 * 60)

    return render_template('index.html', **locals())


@app.route('/load/')
def load():
    menu = app.config['menu']
    sb = app.config['sb']
    ld = sb['load']
    graph_list = []

    ld151_graph = ld.get_graph('ldavg-15', 'ldavg-1')
    ld151_graph.title = 'Load-AVG 1 & 15'
    #ld1_graph.logarithmic = True
    ld151_svg = ld151_graph.render(is_unicode=True)
    graph_list.append(Markup(ld151_svg))

    return render_template('index.html', **locals())


@app.route('/mem/')
def mem():
    menu = app.config['menu']
    sb = app.config['sb']
    mem = sb.get('mem', sb.get('memswp'))
    graph_list = []

    mem_graph = mem.get_graph('kbmemused', 'kbmemfree', '%memused')
    mem_graph.title = 'Memory Usage'
    #mem_graph.logarithmic = False
    svg_used = mem_graph.render(is_unicode=True)
    graph_list.append(Markup(svg_used))

    bc_graph = mem.get_graph('kbcached', 'kbbuffers')
    bc_graph.title = 'Buffer & Cache'
    bc_svg = bc_graph.render(is_unicode=True)
    graph_list.append(Markup(bc_svg))
    return render_template('index.html', **locals())


@app.route('/swap/')
def swap():
    menu = app.config['menu']
    sb = app.config['sb']
    swap = sb.get('swap', sb.get('memswp'))
    graph_list = []

    swap_graph = swap.get_graph('kbswpfree', 'kbswpused', '%swpused')
    swap_graph.title = 'Swap Usage'
    svg_swap = swap_graph.render(is_unicode=True)
    graph_list.append(Markup(svg_swap))
    return render_template('index.html', **locals())


@app.route('/pgswp/')
def pgswap():
    sb = app.config['sb']
    pgswp = sb['pgswp']
    menu = app.config['menu']
    graph_list = []

    pgswp_graph = pgswp.get_graph('pswpout/s', 'pswpin/s')
    pgswp_graph.title = 'Swap Usage'
    pgswp_svg = pgswp_graph.render(is_unicode=True)
    graph_list.append(Markup(pgswp_svg))
    return render_template('index.html', **locals())


@app.route('/pg/')
def pg():
    sb = app.config['sb']
    pg = sb['paging']
    menu = app.config['menu']
    graph_list = []

    pg_graph = pg.get_graph('pgpgin/s', 'pgpgout/s')
    pg_graph.title = 'Paging Activity'
    pg_svg = pg_graph.render(is_unicode=True)
    graph_list.append(Markup(pg_svg))
    return render_template('index.html', **locals())


@app.route('/net/', defaults={'dev': 'lo'})
@app.route('/net/<dev>')
def net(dev):
    sb = app.config['sb']
    net = sb['net_trans']
    menu = app.config['menu']
    graph_list = []

    net_pck_graph = net.get_dev_graph(dev, 'rxpck/s', 'txpck/s')
    net_pck_graph.title = '%s Packets' % dev
    net_pck_svg = net_pck_graph.render(is_unicode=True)
    graph_list.append(Markup(net_pck_svg))

    if sb['sysinfo']['kernel'].startswith('2.6.32'):
        net_trans_graph = net.get_dev_graph(dev, 'rxkB/s', 'txkB/s')
        net_trans_graph.title = '%s Transfer kBytes' % dev
    elif sb['sysinfo']['kernel'].startswith('2.6.18'):
        net_trans_graph = net.get_dev_graph(dev, 'rxbyt/s', 'rxbyt/s')
        net_trans_graph.title = '%s Transfer Bytes' % dev
    net_trans_svg = net_trans_graph.render(is_unicode=True)
    graph_list.append(Markup(net_trans_svg))

    return render_template('index.html', **locals())


@app.route('/net/error/', defaults={'dev': 'lo'})
@app.route('/net/error/<dev>')
def net_error(dev):
    sb = app.config['sb']
    net_error = sb['net_err']
    menu = app.config['menu']
    graph_list = []

    net_err_graph = net_error.get_dev_graph(dev, 'rxerr/s', 'txerr/s')
    net_err_graph.title = '%s Errors' % dev
    net_err_svg = net_err_graph.render(is_unicode=True)
    graph_list.append(Markup(net_err_svg))

    net_drop_graph = net_error.get_dev_graph(dev, 'rxerr/s', 'txerr/s')
    net_drop_graph.title = '%s Drops' % dev
    net_drop_svg = net_drop_graph.render(is_unicode=True)
    graph_list.append(Markup(net_drop_svg))

    return render_template('index.html', **locals())


@app.route('/disk/<dev>', defaults={'dev': None})
@app.route('/disk/<dev>')
def disk(dev):
    sb = app.config['sb']
    disk = sb['diskio']
    menu = app.config['menu']

    graph_list = cache.get('disk_graph_list_%s' % dev)
    #print graph_list
    if graph_list is None:
        graph_list = []
        disk_rw_graph = disk.get_dev_graph(dev, 'rd_sec/s', 'wr_sec/s')
        disk_rw_graph.title = '%s Read & Write' % dev
        disk_rw_svg = disk_rw_graph.render(is_unicode=True)
        graph_list.append(Markup(disk_rw_svg))
        cache.set('disk_graph_list_%s' % dev, graph_list, timeout=5 * 60)

    return render_template('index.html', **locals())


if __name__ == '__main__':
    app.debug = True
    sb = mkchart(sys.argv[1])
    app.config['sb'] = sb
    app.config['SECRET_KEY'] = 'abcx123$'
    app.config['menu'] = {}

    multidevtype = ['cpu', 'net_trans', 'diskio']
    for devtype in multidevtype:
        dev = sb.get(devtype)
        if dev is not None:
            app.config['menu'][devtype] = dev.devlist
    app.run()
