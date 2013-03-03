#!/usr/bin/env python

'''
Created on Jan 29, 2013

@author: rriggio
'''

import optparse

from backends.fvctl import import_vnrequest
from backends.fvctl import import_substrate
from backends.fvctl import create_slice

if __name__ == "__main__":
    
    p = optparse.OptionParser()
    p.add_option("-a", "--algorithm", dest="algorithm", default="vtplanner")
    p.add_option('-d', '--dryrun', action="store_true", dest="dryrun", default=False)    
    p.add_option('-r', '--request', dest="request", default='request.xml')
    p.add_option("-f", "--passwd-file", dest="passwdfile", default="passwd")
    p.add_option("-p", "--port", dest="port", type="int", default="8080")
    p.add_option("-u", "--user", dest="user", default="fvadmin")
    p.add_option("-n", "--name", dest="host", default="localhost")
    p.add_option("-m", "--mcr", dest="mcr", default="/usr/local/MATLAB/MATLAB_Compiler_Runtime/v717")
    options, arguments = p.parse_args()

    embedding = __import__("embedding.%s" % options.algorithm, fromlist=["embedding"])

    # load vn request
    ( virt_devices, virt_links ) = import_vnrequest(options)

    # load substrate
    ( sub_devices, sub_links ) = import_substrate(options)
        
    # compute embedding
    params = { 'mcr' : options.mcr, 'alpha' : 0.5 }
    success = embedding.compute_embedding(sub_devices, sub_links, virt_devices, virt_links, params)
    
    # create_slice
    if success and not options.dryrun:
        create_slice(virt_devices, virt_links, options)
