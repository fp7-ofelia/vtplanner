import amsoil.core.pluginmanager as pm
from vtplannergenithreedelegate import VTPlannerGENI3Delegate

def setup():
    # setup config keys
    # config = pm.getService("config")
    
    delegate = VTPlannerGENI3Delegate()
    handler = pm.getService('geniv3handler')
    handler.setDelegate(delegate)

