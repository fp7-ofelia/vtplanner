
import amsoil.core.pluginmanager as pm
import amsoil.core.log
import re

from lxml import etree
from lxml.builder import E
from lxml.etree import tostring

logger=amsoil.core.log.getLogger('vtplannergeniv3delegate')

GENIv3DelegateBase = pm.getService('geniv3delegatebase')
geni_ex = pm.getService('geniv3exceptions')
vtplanner_ex = pm.getService('vtplannerexceptions')

class VTPlannerGENI3Delegate(GENIv3DelegateBase):
    """
    """

    def __init__(self):
        super(VTPlannerGENI3Delegate, self).__init__()
        self._resource_manager = pm.getService("vtplannerresourcemanager")
    
    def get_request_extensions_mapping(self):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        return {'vtplanner' : 'http://example.com/vtplanner'} # /request.xsd
    
    def get_manifest_extensions_mapping(self):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        return {'vtplanner' : 'http://example.com/vtplanner'} # /manifest.xsd
    
    def get_ad_extensions_mapping(self):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        return {'vtplanner' : 'http://example.com/vtplanner'} # /ad.xsd
    
    def is_single_allocation(self):
        """Documentation see [geniv3rpc] GENIv3DelegateBase.
        We allow to address single slivers (IPs) rather than the whole slice at once."""
        return False

    def get_allocation_mode(self):
        """Documentation see [geniv3rpc] GENIv3DelegateBase.
        We allow to incrementally add new slivers (IPs)."""
        return 'geni_many'

    def list_resources(self, client_cert, credentials, geni_available):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        self.auth(client_cert, credentials, None, ('listslices',))
        
        root_node = self.lxml_ad_root()
        E = self.lxml_ad_element_maker('vtplanner')
        for embedding in self._resource_manager.get_all_embeddings():
            if (not embedding.available) and geni_available: continue # taking care of geni_available
            r = E.resource()
            r.append(E.available("True" if embedding.available else "False"))
            # possible to list other properties
            r.append(E.embedding(embedding.slice_name))
            root_node.append(r)
        
        return self.lxml_to_string(root_node)
    
    def describe(self, urns, client_cert, credentials):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        rspec, sliver_list = self.status(urns, client_cert, credentials)
        return rspec

    def allocate(self, slice_urn, client_cert, credentials, rspec, end_time=None):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        client_urn, client_uuid, client_email = self.auth(client_cert, credentials, slice_urn, ('createsliver',))
        try:
            embedding = self._resource_manager.reserve_embedding(rspec, slice_urn, client_uuid, client_email, end_time)
        except vtplanner_ex.VTPlannerNoResources as e: 
            raise geni_ex.GENIv3SearchFailedError("The desired slice could not be allocated.")
            
        # assemble slivers list
        sliver_list = self._get_sliver_status_hash(embedding, True, True, "")
        return self.lxml_to_string(self._get_manifest_rspec(embedding)), sliver_list

    def renew(self, urns, client_cert, credentials, expiration_time, best_effort):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        # client_urn, client_uuid, client_email = self.auth(client_cert, credentials, slice_urn, ('shutdown',))
        raise geni_ex.GENIv3GeneralError("Method not implemented")
    
    def provision(self, urns, client_cert, credentials, best_effort, end_time, geni_users):
        """Documentation see [geniv3rpc] GENIv3DelegateBase.
        {geni_users} is not relevant here."""
        if len(urns) > 1:
            raise geni_ex.GENIv3OperationUnsupportedError('Only one slice at the time can be provisioned by this aggregate')
        provisioned_embeddings = []
        for urn in urns:
            if (self.urn_type(urn) == 'slice'):
                client_urn, client_uuid, client_email = self.auth(client_cert, credentials, urn, ('createsliver',)) # authenticate for each given slice
                embeddings = self._resource_manager.embeddings_in_slice(urn)
                for embedding in embeddings: 
                    try:
                        self._resource_manager.extend_embedding(embedding, end_time)
                    except vtplanner_ex.VTPlannerDurationExceeded as e:
                        raise geni_ex.GENIv3BadArgsError("Embedding can not be extended that long (%s)" % (str(e),))
                    # really instanciate the resources
                    self._resource_manager.provision(urn, embedding)
                provisioned_embeddings.extend(embeddings)
            else:
                raise geni_ex.GENIv3OperationUnsupportedError('Only slice URNs can be provisioned by this aggregate')
        
        if len(provisioned_embeddings) == 0:
            raise geni_ex.GENIv3SearchFailedError("There are no resources in the given slice(s); perform allocate first")
        # assemble return values
        sliver_list = self._get_sliver_status_hash(provisioned_embeddings[0], True, True, "") 
        return self.lxml_to_string(self._get_manifest_rspec(provisioned_embeddings[0])), sliver_list

    def status(self, urns, client_cert, credentials):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        # This code is similar to the provision call.
        if len(urns) > 1:
            raise geni_ex.GENIv3OperationUnsupportedError('Only one slice at the time can be queried by this aggregate')
        embeddings = []
        for urn in urns:
            if (self.urn_type(urn) == 'slice'):
                client_urn, client_uuid, client_email = self.auth(client_cert, credentials, urn, ('sliverstatus',)) # authenticate for each given slice
                slice_embeddings = self._resource_manager.embeddings_in_slice(urn)
                embeddings.extend(slice_embeddings)
            else:
                raise geni_ex.GENIv3OperationUnsupportedError('Only slice URNs can be given to status in this aggregate')
        
        if len(embeddings) == 0:
            raise geni_ex.GENIv3SearchFailedError("There are no resources in the given slice(s)")
        # assemble slivers list
        sliver_list =  self._get_sliver_status_hash(embeddings[0], True, True, "")
        return self.lxml_to_string(self._get_manifest_rspec(embeddings[0])), sliver_list

    def perform_operational_action(self, urns, client_cert, credentials, action, best_effort):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        # client_urn, client_uuid, client_email = self.auth(client_cert, credentials, slice_urn, ('shutdown',))
        raise geni_ex.GENIv3GeneralError("Method not implemented")

    def delete(self, urns, client_cert, credentials, best_effort):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        # This code is similar to the provision call.
        if len(urns) > 1:
            raise geni_ex.GENIv3OperationUnsupportedError('Only one slice at the time can be deleted by this aggregate')
        for urn in urns:
            if (self.urn_type(urn) == 'slice'):
                client_urn, client_uuid, client_email = self.auth(client_cert, credentials, urn, ('deletesliver',)) # authenticate for each given slice
                slice_embeddings = self._resource_manager.embeddings_in_slice(urn)
                for embedding in slice_embeddings:
                    self._resource_manager.free_embedding(urn, embedding)
            else:
                raise geni_ex.GENIv3OperationUnsupportedError('Only slice URNs can be deleted in this aggregate')
        
        # assemble return values
        return []
    
    def shutdown(self, slice_urn, client_cert, credentials):
        """Documentation see [geniv3rpc] GENIv3DelegateBase."""
        # client_urn, client_uuid, client_email = self.auth(client_cert, credentials, slice_urn, ('shutdown',))
        raise geni_ex.GENIv3GeneralError("Method not implemented")

    # Helper methods
    def _get_sliver_status_hash(self, embedding, include_allocation_status=False, include_operational_status=False, error_message=None):
        """Helper method to create the sliver_status return values of allocate and other calls."""

        if embedding is None:
            return []

        results = []

        for vertex in embedding.virt_vertices:

            result = {'geni_sliver_urn' : embedding.virt_vertices[vertex]['component_id'],#"%s:%s" % (embedding.virt_vertices[vertex]['type'], vertex),
                      'geni_expires'    : embedding.end_time,
                      'geni_allocation_status' : self.ALLOCATION_STATE_ALLOCATED}

            if embedding.provisioned:
                result['geni_allocation_status'] = self.ALLOCATION_STATE_PROVISIONED

            # this should check if (i) sliver was authorized on foam and (ii) if VM
            # is actually running
            if (include_operational_status): 
                result['geni_operational_status'] = self.OPERATIONAL_STATE_READY

            if (error_message):
                result['geni_error'] = error_message
        
            results.append(result)

        return results

    def _get_manifest_rspec(self, embedding):
    
        xmlns="http://www.geni.net/resources/rspec/3"
        xmlns_xs="http://www.w3.org/2001/XMLSchema-instance"
        xmlns_openflow="/opt/foam/schemas"
        xsi="http://www.w3.org/2001/XMLSchema-instance"
        schemaLocation="http://www.geni.net/resources/rspec/3 http://www.geni.net/resources/rspec/3/request.xsd /opt/foam/schemas /opt/foam/schemas/of-resv.xsd"
        version="1.1"
	NSMAP={None:xmlns, 'xs':xmlns_xs, 'openflow':xmlns_openflow}

        # Create the root element
        root = etree.Element('rspec', type='request', version=version, attrib={"{" + xsi + "}schemaLocation" : schemaLocation}, nsmap=NSMAP)

        # Make a new document tree
        doc = etree.ElementTree(root)

        if embedding is None:
            return doc

        # Add the subelements
        sliver = etree.SubElement(root, '{%s}sliver' % NSMAP['openflow'], nsmap=NSMAP, email=embedding.email, description=embedding.description)
        etree.SubElement(sliver, '{%s}controller' % NSMAP['openflow'], nsmap=NSMAP, url=embedding.controller, type="primary")
        etree.SubElement(sliver, '{%s}vertigo' % NSMAP['openflow'], nsmap=NSMAP, algorithm="vtplanner", ofversion="1.0")

        vertices = etree.SubElement(sliver, '{%s}vertices' % NSMAP['openflow'], nsmap=NSMAP)
        edges = etree.SubElement(sliver, '{%s}edges' % NSMAP['openflow'], nsmap=NSMAP)

        ports = {}

        # add links: <openflow:edge srcDPID="1" dstDPID="2" bw="100M"/>
        for link in embedding.virt_edges.values():

            srcDPID = embedding.virt_vertices.values()[link['src']]['dpid']
            dstDPID = embedding.virt_vertices.values()[link['dst']]['dpid']

            edge = etree.SubElement(edges, '{%s}edge' % NSMAP['openflow'], nsmap=NSMAP, srcDPID=srcDPID, dstDPID=dstDPID, bw=str(link['capacity']))
            hops = etree.SubElement(edge, '{%s}hops' % NSMAP['openflow'], nsmap=NSMAP)
            idx = 1
            for hop in link['hops']: 
                if hop[0] not in ports:
                    ports[hop[0]] = []
                if hop[2] not in ports:
                    ports[hop[2]] = []
                if hop[1] not in ports[hop[0]]:
                    ports[hop[0]].append(hop[1])
                if hop[3] not in ports[hop[2]]:
                    ports[hop[2]].append(hop[3])
                etree.SubElement(hops, '{%s}hop' % NSMAP['openflow'], nsmap=NSMAP, srcDPID=hop[0], srcPort=str(hop[1]), dstDPID=hop[2], dstPort=str(hop[3]))
                idx = idx + 1

        # add switches
        for node in embedding.virt_vertices.values():

            if node['type'] == "switch":

                nd = etree.SubElement(vertices, '{%s}vertex' % NSMAP['openflow'], 
                                      nsmap=NSMAP, 
                                      type=node['type'], 
                                      name=node['name'], 
                                      tablesize=node['tablesize'], 
                                      switchtype=node['switchtype'], 
                                      component_id=node['component_id'], 
                                      component_manager_id=node['component_manager_id'], 
                                      dpid=node['dpid'])

            else:

                nd = etree.SubElement(vertices, '{%s}vertex' % NSMAP['openflow'], 
                                      nsmap=NSMAP, 
                                      type=node['type'], 
                                      name=node['name'], 
                                      memory_mb=str(node['memory_mb']), 
                                      component_id=node['component_id'], 
                                      component_manager_id=node['component_manager_id'], 
                                      dpid=node['dpid'])

            for port in ports[node['dpid']]:
                etree.SubElement(nd, '{%s}port' % NSMAP['openflow'], nsmap=NSMAP, num=str(port))

        return doc

