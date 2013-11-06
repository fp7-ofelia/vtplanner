import amsoil.core.pluginmanager as pm

def setup():
    # setup config keys
    config = pm.getService("config")
    # please do not touch these
    config.install("vtplannerrm.max_reservation_duration", 10*60, "Maximum duration a VTPlanner resource can be held allocated (not provisioned).")
    config.install("vtplannerrm.dbpath", "deploy/vtplanner.db", "Path to the vtplanner database (if relative, AMsoil's root will be assumed).")
    config.install("vtplannerrm.mcr", '/root/MATLAB_MCR_R2012A/v717', "MCR path.")
    # edit this if needed
    config.install("vtplannerrm.foam_host", '127.0.0.1', "FOAM IPAddress.")
    config.install("vtplannerrm.foam_port", 3626, "FOAM Port.")

    config.install("vtplannerrm.vtam_host", '10.216.32.5', "VTAM IPAddress.")
    config.install("vtplannerrm.vtam_port", 8445, "VTAM Port.")
    config.install("vtplannerrm.vtam_username", 'openflow', "VTAM Username.")
    config.install("vtplannerrm.vtam_password", 'p3rv4s1v3', "VTAM Password.")

    config.install("vtplannerrm.vtam2_host", 'exp.i2cat.fp7-ofelia.eu', "VTAM IPAddress.")
    config.install("vtplannerrm.vtam2_port", 8445, "VTAM Port.")
    config.install("vtplannerrm.vtam2_username", 'xmlrpc_i2cat_user', "VTAM Username.")
    config.install("vtplannerrm.vtam2_password", 'xmlrpc_407343_i2cat', "VTAM Password.")

    from vtplannerresourcemanager import VTPlannerResourceManager
    import vtplannerexceptions as exceptions_package
    rm = VTPlannerResourceManager()
    pm.registerService('vtplannerresourcemanager', rm)
    pm.registerService('vtplannerexceptions', exceptions_package)
    

