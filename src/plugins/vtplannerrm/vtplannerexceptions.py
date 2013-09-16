from amsoil.core.exception import CoreException
        
class VTPlannerException(CoreException):
    def __init__(self, desc):
        self._desc = desc
    def __str__(self):
        return "VTPlanner: %s" % (self._desc,)

class VTPlannerNoResources(VTPlannerException):
    def __init__(self, slicename):
        super(VTPlannerNoResources, self).__init__("Not enough resource available on the substrate network to embed %s" % slicename)

class VTPlannerDurationExceeded(VTPlannerException):
    def __init__(self, slicename):
        super(VTPlannerDurationExceeded, self).__init__("Max duration for an embedding exceeded %s" % slicename)

class VTPlannerEmbeddingAlreadyDefined(VTPlannerException):
    def __init__(self, slicename, end_time):
        super(VTPlannerEmbeddingAlreadyDefined, self).__init__("A slice with the name %s has already been allocated. Allocation will expire at %s" % (slicename, end_time))

