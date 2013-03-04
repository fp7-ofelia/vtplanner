#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# VTPlanner OFELIA OCF module
#
# Copyright (C) 2013 Roberto Riggio <roberto.riggio@create-net.org>
#
# VTPlanner is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# COPYING file for more details.

import subprocess 
import re

from lxml import etree

OFPPF_10MB_HD = 0 # 10 Mb half-duplex rate support 
OFPPF_10MB_FD = 1 # 10 Mb full-duplex rate support
OFPPF_100MB_HD = 2 # 100 Mb half-duplex rate support
OFPPF_100MB_FD = 3 # 100 Mb full-duplex rate support
OFPPF_1GB_HD = 4 # 1 Gb half-duplex rate support
OFPPF_1GB_FD = 5 # 1 Gb full-duplex rate support
OFPPF_10GB_FD = 6 # 10 Gb full-duplex rate support
OFPPF_COPPER = 7 # Copper medium
OFPPF_FIBER = 8 # Fiber medium
OFPPF_AUTONEG = 9 # Auto-negotiation
OFPPF_PAUSE = 10 # Pause
OFPPF_PAUSE_ASYM = 11 # Asymmetric pause

def decode_port_speed(features):

    if int(features,0) & (1 << OFPPF_10MB_HD | 1 << OFPPF_10MB_FD):
        return 10 
    elif int(features,0) & (1 << OFPPF_100MB_HD | 1 << OFPPF_100MB_FD):
        return 100
    elif int(features,0) & (1 << OFPPF_1GB_HD | 1 << OFPPF_1GB_FD):
        return 1000
    elif int(features,0) & (1 << OFPPF_10GB_FD):
        return 10000 

    return 100

def decode_edge_bw(bw):

    capacity = 1 
        
    match = re.search("^([0-9]*)(K|M|G)", bw)
    
    if match:
        
        if match.group(2) == 'K':
            capacity = int(match.group(1)) / 1000
        elif match.group(2) == 'M':
            capacity = int(match.group(1))
        elif match.group(2) == 'G':
            capacity = int(match.group(1)) * 1000
        else:
            capacity = int(match.group(1))
        
    return capacity

def resolve_by_dpid(devices, dpid):
    for device in devices:
        if devices[device]['DPID'] == dpid:
            return device
    return -1

def run_process(exe):    
    p = subprocess.Popen(exe, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd='./')
    while(True):
        retcode = p.poll() #returns None while subprocess is running
        line = p.stdout.readline()
        yield line
        if(retcode is not None):
            break

def fvctl(options, cmds):
    return [ 'fvctl', 
            '--user=%s' % options.user, 
            '--passwd-file=%s' % options.passwdfile, 
            '--url=https://%s:%d/xmlrpc' % (options.host, options.port) ] + cmds

def import_vnrequest(options):

    print "Importing VN request definition from file: %s" % options.request
    
    virt_devices = {}
    virt_links = {}

    doc = etree.parse(options.request)
    nsmap = doc.getroot().nsmap
    
    for item in doc.findall('//{%s}switch' % nsmap['openflow']): 
        switch_id = int(item.get('id'))
        virt_devices[switch_id] = { 'type' : 'switch', 
                                    'tablesize' : item.get('tablesize'), 
                                    'switchtype' : item.get('switchtype') }
    
    link_id = 0
    
    for item in doc.findall('//{%s}edge' % nsmap['openflow']):
        src = int(item.get('src'))
        dst = int(item.get('dst'))
        capacity = decode_edge_bw(item.get('bw'))
        virt_links[link_id] = { 'src' : src, 'dst' : dst, 'capacity' : capacity }
        link_id = link_id + 1

    return ( virt_devices, virt_links )
                    
def import_substrate(options):

    # list substrate devices
    print "Loading substrate devices"
    sub_devices = {}
    for line in run_process(fvctl(options, ['listDevices'])):
        match = re.search("^Device (.*): (.*).*", line)
        if match:
            sub_devices[match.group(1)] = { 'DPID' : match.group(2), 'type' : 'switch' }

    if len(sub_devices) == 0:
        raise Exception("Unable to load devices")

    # list substrate links
    print "Loading substrate links"
    sub_links = {}
    for line in run_process(fvctl(options, ['getLinks'])):
        match = re.search("^Link (.*): Link\[srcDPID=(.*),srcPort=(.*),dstDPID=(.*),dstPort=(.*)\].*", line)
        if match:
            sub_links[match.group(1)] = { 'srcDPID' : match.group(2),
                                          'srcPort' : match.group(3),
                                          'dstDPID' : match.group(4),
                                          'dstPort' : match.group(5) }

    if len(sub_links) == 0:
        raise Exception("Unable to load links")

    # add port info to substrate devices
    print "Loading port info"
    for device in sub_devices:
        DPID = sub_devices[device]['DPID']
        for line in run_process(fvctl(options, [ 'getDeviceInfo', DPID] )):
            match = re.search("^portList=(.*)", line)
            if match:
                ports = match.group(1).split(',')
                sub_devices[device]['ports'] = ports
        if len(sub_devices[device]['ports']) == 0:
            raise Exception("Unable to load port list for %s" % DPID)

    # add capacity info to substrate links
    print "Loading capacity info"
    
    for link in sub_links:
    
        srcDPID = sub_links[link]['srcDPID']
        dstDPID = sub_links[link]['dstDPID']

        srcPort = sub_links[link]['srcPort']
    
        sub_links[link]['src'] = resolve_by_dpid(sub_devices, srcDPID)
        sub_links[link]['dst'] = resolve_by_dpid(sub_devices, dstDPID)

        for line in run_process(fvctl(options, [ 'getVTPlannerPortInfo', srcDPID, srcPort] )):
            match = re.search("^(.*)\s*0x(.*)\s*0x(.*)\s*0x(.*)\n", line)
            if match:
                features = hex(int(match.group(3),16));
                sub_links[link]['capacity'] = decode_port_speed(features)

        if 'capacity' not in sub_links[link]:
            raise Exception("Unable to load port list for %s / %s" % ( srcDPID, srcPort))

    return ( sub_devices, sub_links )

def create_slice(virt_devices, virt_links, options):

    # create new slice
    
    doc = etree.parse(options.request)
    nsmap = doc.getroot().nsmap
    
    sliver = doc.find('//{%s}sliver' % nsmap['openflow'])
    email = sliver.get('email')

    controller = doc.find('//{%s}controller' % nsmap['openflow'])
    url = controller.get('url')
    
    group = doc.find('//{%s}group' % nsmap['openflow'])
    name = group.get('name')

    print "Creating slice: %s" % name

    cmds = [ 'createSlice', 
            name,
            url,
            email ]
    
    retcode = subprocess.call(fvctl(options, cmds))
    
    if retcode != 0:
        raise Exception("Unable to create slice")
    
    cmds = [ 'addFlowSpace', 'all', '2', 'any', 'Slice:%s=4' % name ] 
    
    retcode = subprocess.call(fvctl(options, cmds))

    if retcode != 0:
        raise Exception("Unable to add flowspace")

    for link in virt_links:
        vpath = ""
        for hop in virt_links[link]['hops']:
            if not vpath == "":
                vpath = vpath + ","
            vpath = vpath + "%s/%s-%s/%s" % tuple(hop) 
        cmds = [ 'addLink', name, vpath ]
        retcode = subprocess.call(fvctl(options, cmds))
        if retcode != 0:
            raise Exception("Unable to create link (%s)" % vpath)
        else:
            print "Link created (%s)" % vpath
            
if __name__ == '__main__':
    pass
