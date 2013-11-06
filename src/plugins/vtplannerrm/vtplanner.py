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

import os
import subprocess 
import scipy.io
import numpy

INPUT_SUBSTRATE = "/tmp/vtplanner_input_substrate.mat"
INPUT_VIRTUAL = "/tmp/vtplanner_input_virtual.mat"

OUTPUT = "/tmp/vtplanner_output.mat"

def run_process(exe):   

    os.chdir('/root/vtplanner/src/plugins/vtplannerrm/')

    current_env = os.environ.copy()
    current_env["LC_ALL"] = "C"

    p = subprocess.Popen(exe, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=current_env)

    while(True):
        retcode = p.poll() #returns None while subprocess is running
        line = p.stdout.readline()
        yield line
        if(retcode is not None):
            break
        
def write_substrate_mat(sub_devices, sub_links):

    # write mat files (substrate)
    Nsubstrate = len(sub_devices)
    Csubstrate = [0] * Nsubstrate
    Msubstrate = numpy.matrix([ [0] * Nsubstrate ] * Nsubstrate)
        
    for device in sub_devices:
        if sub_devices[device]['type'] == "vm":
            Csubstrate[device] = sub_devices[device]['memory_mb']

    for link in sub_links:
        srcId = int(sub_links[link]['src'])
        dstId = int(sub_links[link]['dst'])
        Msubstrate[srcId,dstId] = sub_links[link]['capacity']
        Msubstrate[dstId,srcId] = sub_links[link]['capacity']
        
    substrate = {'Nsubstrate': Nsubstrate, 'Csubstrate' : Csubstrate, 'Msubstrate' : Msubstrate}
    
    if os.path.isfile(INPUT_SUBSTRATE):
        os.remove(INPUT_SUBSTRATE)

    print "Number of substrate nodes: %s" % substrate['Nsubstrate']
    print "Nodes' capacity:"
    print substrate['Csubstrate']
    print "Connectivity matrix:"
    print substrate['Msubstrate']

    scipy.io.savemat(INPUT_SUBSTRATE, mdict=substrate, oned_as='row')

def write_vnrequest_mat(virt_devices, virt_links):

    # write mat files (virtual)
    Nvirtual = len(virt_devices)
    Cvirtual = [0] * Nvirtual
    Mvirtual = numpy.matrix([ [0] * Nvirtual ] * Nvirtual)

    for device in virt_devices:
        if virt_devices[device]['type'] == "vm":
            Cvirtual[device] = virt_devices[device]['memory_mb']

    for link in virt_links:
        
        srcId = int(virt_links[link]['src'])
        dstId = int(virt_links[link]['dst'])
        Mvirtual[srcId,dstId] = virt_links[link]['capacity']
        Mvirtual[dstId,srcId] = virt_links[link]['capacity']
        
    virtual = {'Nvirtual': Nvirtual, 'Cvirtual' : Cvirtual, 'Mvirtual' : Mvirtual}
    
    if os.path.isfile(INPUT_VIRTUAL):
        os.remove(INPUT_VIRTUAL)
        
    print "Number of vn request nodes: %s" % virtual['Nvirtual']
    print "Nodes' capacity:"
    print virtual['Cvirtual']
    print "Connectivity matrix:"
    print virtual['Mvirtual']
        
    scipy.io.savemat(INPUT_VIRTUAL, mdict=virtual, oned_as='row')
    
def compute_embedding(sub_devices, sub_links, virt_devices, virt_links, params):
    
    print "Writing MAT files"
    
    write_substrate_mat(sub_devices, sub_links)
    write_vnrequest_mat(virt_devices, virt_links)

    print "Running MATLAB algorithm"
    
    if os.path.isfile(OUTPUT):
        os.remove(OUTPUT)
        
    cmds = ['./run_vtplanner_standalone.sh', 
            params['mcr'], 
            str(params['alpha']), 
            INPUT_VIRTUAL, 
            INPUT_SUBSTRATE, 
            OUTPUT ]
        
    for line in run_process(cmds):
        if line != '':
            print line.replace('\n','')
        
    if not os.path.isfile(OUTPUT):
        print "Embedding failed: topology rejected"
        return False
    
    mat = scipy.io.loadmat(OUTPUT, struct_as_record=False)
                     
    if 'exitflag' not in mat or mat['exitflag'][0] != 1:
        print "Embedding failed: topology rejected!"
        return False
    
    matVirt = scipy.io.loadmat(INPUT_VIRTUAL, struct_as_record=False)

    print "Embedding was successful: topology accepted!"

    edge_nb = 0

    for v in range(0, len(mat['mappings'][0])):
        pnode = mat['mappings'][0][v] - 1
        print "Processing: VNode %d -> SNode %d (%s)" % (v, pnode, sub_devices[pnode]['dpid'])
        virt_devices[v]['dpid'] = sub_devices[pnode]['dpid']
        if sub_devices[pnode]['type'] == "vm":
            virt_devices[v]['component_name'] = sub_devices[pnode]['component_name']
        virt_devices[v]['component_manager_id'] = sub_devices[pnode]['component_manager_id']
        virt_devices[v]['component_id'] = sub_devices[pnode]['component_id']
        for w in range(v, len(mat['mappings'][0])):
            if v == w:
                continue
            if matVirt['Mvirtual'][v,w] == 0:
                continue
            w_t = mat['mappings'][0][w] - 1;                        
            print "VLink %d -> %d (%d)" % (v, w, matVirt['Mvirtual'][v,w] )
            virt_links[edge_nb]['hops'] = []
            pred = mat['preds'][edge_nb]
            cur = w_t
            prev = pred[w_t] - 1;
            while prev != -1:
                curDPID = sub_devices[cur]['dpid']
                prevDPID = sub_devices[prev]['dpid']
                curPort = 0
                prevPort = 0
                for link in sub_links.values():
                    if link['srcDPID'] == curDPID and link['dstDPID'] == prevDPID:
                        curPort = link['srcPort']
                        prevPort = link['dstPort']
                print " + %d -> %d (%s/%s -> %s/%s)" % (cur, prev, curDPID, curPort, prevDPID, prevPort)
                virt_links[edge_nb]['hops'].append([curDPID, curPort, prevDPID, prevPort])             
                cur = prev;
                prev = pred[prev] - 1;
            edge_nb = edge_nb + 1    

    return True

if __name__ == '__main__':
    pass
