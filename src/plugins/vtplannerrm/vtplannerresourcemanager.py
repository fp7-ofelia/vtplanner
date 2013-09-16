from datetime import datetime, timedelta

import amsoil.core.pluginmanager as pm
import amsoil.core.log
import re
import json
import xmlrpclib

logger=amsoil.core.log.getLogger('vtplannerresourcemanager')

from vtplannerexceptions import *
from geni_am_api_two_client import GENI2Client

from lxml import etree
from lxml.builder import E
from lxml.etree import tostring

worker = pm.getService('worker')

VTAM_SAMPLE="""<?xml version="1.0" encoding="UTF-8"?>
<rspec>
 <network name="ocf.i2cat.vt_manager">

    <node component_manager_id="urn:publicid:IDN+ocf:i2cat:vt_manager+authority+sa" component_id="urn:publicid:IDN+ocf:i2cat:vt_manager+node+foix" exclusive="false" component_name="urn:publicid:IDN+ocf:i2cat:vt_manager+node+foix">

      <hostname>foix.ctx.i2cat.net</hostname>
      <name>foix</name>
      <operating_system_type>GNU/Linux</operating_system_type>
      <operating_system_distribution>Debian</operating_system_distribution>
      <operating_system_version>6.0</operating_system_version>
      <virtualization_technology>xen</virtualization_technology>
      <cpus_number>8</cpus_number>
      <cpu_frequency>2500</cpu_frequency>
      <memory>900</memory>
      <hdd_space_GB>5000.0</hdd_space_GB>
      <agent_url>https://84.88.40.12:9229/</agent_url>
      <service type="Range">
        <type>IP_Range</type>
        <name>Range prueba</name>
        <start_value>10.0.0.1</start_value>
        <end_value>10.0.0.100</end_value>
      </service>
      <service type="Range">
        <type>IP_Range</type>
        <name>prueba 2</name>
        <start_value>10.0.0.200</start_value>
        <end_value>10.0.0.254</end_value>
      </service>
      <service type="Range">
        <type>MAC_Range</type>
        <name>prueba</name>
        <start_value>02:03:FF:FF:FF:00</start_value>
        <end_value>02:03:FF:FF:FF:FF</end_value>
      </service>
      <service type="NetworkInterface">
        <from_server_interface_name>eth1.999</from_server_interface_name>
        <to_network_interface_id>OFSwitch001</to_network_interface_id>
        <to_network_interface_port>2</to_network_interface_port>
      </service>
      <service type="NetworkInterface">
        <from_server_interface_name>eth2</from_server_interface_name>
        <to_network_interface_id>lak</to_network_interface_id>
        <to_network_interface_port>5</to_network_interface_port>
      </service>
      <service type="NetworkInterface">
        <from_server_interface_name>eth3</from_server_interface_name>
        <to_network_interface_id>02:08:02:08:00:00:00:07</to_network_interface_id>
        <to_network_interface_port>14</to_network_interface_port>
      </service>
    </node>

 </network>

</rspec>

"""

CREDS='<?xml version="1.0"?>\n<signed-credential xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://www.planet-lab.org/resources/sfa/credential.xsd" xsi:schemaLocation="http://www.planet-lab.org/resources/sfa/ext/policy/1 http://www.planet-lab.org/resources/sfa/ext/policy/1/policy.xsd"><credential xml:id="ref0"><type>privilege</type><serial>8</serial><owner_gid>-----BEGIN CERTIFICATE-----\nMIICNDCCAZ2gAwIBAgIBAzANBgkqhkiG9w0BAQQFADAmMSQwIgYDVQQDExtnZW5p\nLy9ncG8vL2djZi5hdXRob3JpdHkuc2EwHhcNMTMwNjE4MDc1NDQ1WhcNMTgwNjE3\nMDc1NDQ1WjAkMSIwIAYDVQQDExlnZW5pLy9ncG8vL2djZi51c2VyLmFsaWNlMIGf\nMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCmS8GZ6qy4TKh7CTSKvMIAlLqCG0uG\nbZEqfLZdSqhe21c+mxQ+V3dgmCSwi6noWg2pJkkcFn1YKvIy9XUZ3IwNfE9QIVlK\n0Eh453+jqOAc9jc6KrXpPMTkicmGVpAac4X/Ao6fuZMHZ81tjVgeJ8xxYpU6Qjz0\npKjTr8D9lCR2IQIDAQABo3QwcjAMBgNVHRMBAf8EAjAAMGIGA1UdEQRbMFmGKHVy\nbjpwdWJsaWNpZDpJRE4rZ2VuaTpncG86Z2NmK3VzZXIrYWxpY2WGLXVybjp1dWlk\nOjViYzNiZWY3LTM4NDktNDEzMS1iNDczLTU2MzNiMzA1MzQ3MTANBgkqhkiG9w0B\nAQQFAAOBgQBkMVA+I6oEpU4afFY0xE3cwi93Cyt6dt/p8B2zZ9dzs5vAXx6PaGMb\n5k5+LjtoUGQ/XMOPdX0TuPhhJLOV9mYP5Xm+4dr8RYTGO3bVdnh60XHWBqZtsdOj\nIOvLkSVYqouUyyEeEPNm4dukk4BHGzisTqwrglkcYQtDWPmglxKs+A==\n-----END CERTIFICATE-----\n-----BEGIN CERTIFICATE-----\nMIICOzCCAaSgAwIBAgIBAzANBgkqhkiG9w0BAQQFADAmMSQwIgYDVQQDExtnZW5p\nLy9ncG8vL2djZi5hdXRob3JpdHkuc2EwHhcNMTMwNjE4MDc1NDQ0WhcNMTgwNjE3\nMDc1NDQ0WjAmMSQwIgYDVQQDExtnZW5pLy9ncG8vL2djZi5hdXRob3JpdHkuc2Ew\ngZ8wDQYJKoZIhvcNAQEBBQADgY0AMIGJAoGBAN2D/6XFhkK6NwYg0nF60AU380ej\n35LmzVYJuJDyh0qlusvSaJkuv3LLHtzZ/sG6ZyitwqPyiHwPL9KgsfBvqYs/5hsi\n7qzV8M6YbcOwpNAWiSqbtmnEkzbkvzG+dwWwsS37dC6rp5cj9v7k5bj+FwdgIWNy\nhN5JhC1ROJg5w89ZAgMBAAGjeTB3MA8GA1UdEwEB/wQFMAMBAf8wZAYDVR0RBF0w\nW4YqdXJuOnB1YmxpY2lkOklETitnZW5pOmdwbzpnY2YrYXV0aG9yaXR5K3Nhhi11\ncm46dXVpZDpkMDc2MWQ1OS0zNzA2LTQxMWItOTRkMy02YTUxZjZiZGI5ODUwDQYJ\nKoZIhvcNAQEEBQADgYEALQqBOipQncjxdCrsc/WZzjgjgs1htCOCi0BiwJfXE/44\naW6P/a93zpzgOkD6YXkaFLjjTJ/RZ+mVM+MIH3R4xw+8lUXMKfsj549WKa4H90N7\nQTKOBN7oVhHQOfd9E2llVzt326OtbXapnReASuKVNvzM3Dlxe4IkD1n9H91s1+M=\n-----END CERTIFICATE-----\n</owner_gid><owner_urn>urn:publicid:IDN+geni:gpo:gcf+user+alice</owner_urn><target_gid>-----BEGIN CERTIFICATE-----\nMIICNDCCAZ2gAwIBAgIBAzANBgkqhkiG9w0BAQQFADAmMSQwIgYDVQQDExtnZW5p\nLy9ncG8vL2djZi5hdXRob3JpdHkuc2EwHhcNMTMwNjE4MDc1NDQ1WhcNMTgwNjE3\nMDc1NDQ1WjAkMSIwIAYDVQQDExlnZW5pLy9ncG8vL2djZi51c2VyLmFsaWNlMIGf\nMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCmS8GZ6qy4TKh7CTSKvMIAlLqCG0uG\nbZEqfLZdSqhe21c+mxQ+V3dgmCSwi6noWg2pJkkcFn1YKvIy9XUZ3IwNfE9QIVlK\n0Eh453+jqOAc9jc6KrXpPMTkicmGVpAac4X/Ao6fuZMHZ81tjVgeJ8xxYpU6Qjz0\npKjTr8D9lCR2IQIDAQABo3QwcjAMBgNVHRMBAf8EAjAAMGIGA1UdEQRbMFmGKHVy\nbjpwdWJsaWNpZDpJRE4rZ2VuaTpncG86Z2NmK3VzZXIrYWxpY2WGLXVybjp1dWlk\nOjViYzNiZWY3LTM4NDktNDEzMS1iNDczLTU2MzNiMzA1MzQ3MTANBgkqhkiG9w0B\nAQQFAAOBgQBkMVA+I6oEpU4afFY0xE3cwi93Cyt6dt/p8B2zZ9dzs5vAXx6PaGMb\n5k5+LjtoUGQ/XMOPdX0TuPhhJLOV9mYP5Xm+4dr8RYTGO3bVdnh60XHWBqZtsdOj\nIOvLkSVYqouUyyEeEPNm4dukk4BHGzisTqwrglkcYQtDWPmglxKs+A==\n-----END CERTIFICATE-----\n-----BEGIN CERTIFICATE-----\nMIICOzCCAaSgAwIBAgIBAzANBgkqhkiG9w0BAQQFADAmMSQwIgYDVQQDExtnZW5p\nLy9ncG8vL2djZi5hdXRob3JpdHkuc2EwHhcNMTMwNjE4MDc1NDQ0WhcNMTgwNjE3\nMDc1NDQ0WjAmMSQwIgYDVQQDExtnZW5pLy9ncG8vL2djZi5hdXRob3JpdHkuc2Ew\ngZ8wDQYJKoZIhvcNAQEBBQADgY0AMIGJAoGBAN2D/6XFhkK6NwYg0nF60AU380ej\n35LmzVYJuJDyh0qlusvSaJkuv3LLHtzZ/sG6ZyitwqPyiHwPL9KgsfBvqYs/5hsi\n7qzV8M6YbcOwpNAWiSqbtmnEkzbkvzG+dwWwsS37dC6rp5cj9v7k5bj+FwdgIWNy\nhN5JhC1ROJg5w89ZAgMBAAGjeTB3MA8GA1UdEwEB/wQFMAMBAf8wZAYDVR0RBF0w\nW4YqdXJuOnB1YmxpY2lkOklETitnZW5pOmdwbzpnY2YrYXV0aG9yaXR5K3Nhhi11\ncm46dXVpZDpkMDc2MWQ1OS0zNzA2LTQxMWItOTRkMy02YTUxZjZiZGI5ODUwDQYJ\nKoZIhvcNAQEEBQADgYEALQqBOipQncjxdCrsc/WZzjgjgs1htCOCi0BiwJfXE/44\naW6P/a93zpzgOkD6YXkaFLjjTJ/RZ+mVM+MIH3R4xw+8lUXMKfsj549WKa4H90N7\nQTKOBN7oVhHQOfd9E2llVzt326OtbXapnReASuKVNvzM3Dlxe4IkD1n9H91s1+M=\n-----END CERTIFICATE-----\n</target_gid><target_urn>urn:publicid:IDN+geni:gpo:gcf+user+alice</target_urn><uuid/><expires>2013-06-25T14:41:16</expires><privileges><privilege><name>refresh</name><can_delegate>false</can_delegate></privilege><privilege><name>resolve</name><can_delegate>false</can_delegate></privilege><privilege><name>info</name><can_delegate>false</can_delegate></privilege></privileges></credential><signatures><Signature xmlns="http://www.w3.org/2000/09/xmldsig#" xml:id="Sig_ref0">\n  <SignedInfo>\n    <CanonicalizationMethod Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315"/>\n    <SignatureMethod Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1"/>\n    <Reference URI="#ref0">\n      <Transforms>\n        <Transform Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature"/>\n      </Transforms>\n      <DigestMethod Algorithm="http://www.w3.org/2000/09/xmldsig#sha1"/>\n      <DigestValue>iXeob2JH0oDIyI3K8HkAZWNjoiQ=</DigestValue>\n    </Reference>\n  </SignedInfo>\n  <SignatureValue>eTk5lAT+bjnUnb6N9iZzmUlcCmgAQ9TFoBAhUlOxTse5G70VkUZpRmpq2MSu5+tg\nJyH8kY6i8G3QRU+WkR2zU+Q/NuFLw492SymIZ3DPR2CzfjL5u7l3NBYSmlvgP8b7\n3koz3Uv7huPj/oWPwDbT5erttWgk0gMrB2qryJ6Xbso=</SignatureValue>\n  <KeyInfo>\n    <X509Data>\n<X509Certificate>MIICOzCCAaSgAwIBAgIBAzANBgkqhkiG9w0BAQQFADAmMSQwIgYDVQQDExtnZW5p\nLy9ncG8vL2djZi5hdXRob3JpdHkuc2EwHhcNMTMwNjE4MDc1NDQ0WhcNMTgwNjE3\nMDc1NDQ0WjAmMSQwIgYDVQQDExtnZW5pLy9ncG8vL2djZi5hdXRob3JpdHkuc2Ew\ngZ8wDQYJKoZIhvcNAQEBBQADgY0AMIGJAoGBAN2D/6XFhkK6NwYg0nF60AU380ej\n35LmzVYJuJDyh0qlusvSaJkuv3LLHtzZ/sG6ZyitwqPyiHwPL9KgsfBvqYs/5hsi\n7qzV8M6YbcOwpNAWiSqbtmnEkzbkvzG+dwWwsS37dC6rp5cj9v7k5bj+FwdgIWNy\nhN5JhC1ROJg5w89ZAgMBAAGjeTB3MA8GA1UdEwEB/wQFMAMBAf8wZAYDVR0RBF0w\nW4YqdXJuOnB1YmxpY2lkOklETitnZW5pOmdwbzpnY2YrYXV0aG9yaXR5K3Nhhi11\ncm46dXVpZDpkMDc2MWQ1OS0zNzA2LTQxMWItOTRkMy02YTUxZjZiZGI5ODUwDQYJ\nKoZIhvcNAQEEBQADgYEALQqBOipQncjxdCrsc/WZzjgjgs1htCOCi0BiwJfXE/44\naW6P/a93zpzgOkD6YXkaFLjjTJ/RZ+mVM+MIH3R4xw+8lUXMKfsj549WKa4H90N7\nQTKOBN7oVhHQOfd9E2llVzt326OtbXapnReASuKVNvzM3Dlxe4IkD1n9H91s1+M=</X509Certificate>\n<X509SubjectName>CN=geni//gpo//gcf.authority.sa</X509SubjectName>\n<X509IssuerSerial>\n<X509IssuerName>CN=geni//gpo//gcf.authority.sa</X509IssuerName>\n<X509SerialNumber>3</X509SerialNumber>\n</X509IssuerSerial>\n</X509Data>\n    <KeyValue>\n<RSAKeyValue>\n<Modulus>\n3YP/pcWGQro3BiDScXrQBTfzR6PfkubNVgm4kPKHSqW6y9JomS6/csse3Nn+wbpn\nKK3Co/KIfA8v0qCx8G+piz/mGyLurNXwzphtw7Ck0BaJKpu2acSTNuS/Mb53BbCx\nLft0LqunlyP2/uTluP4XB2AhY3KE3kmELVE4mDnDz1k=\n</Modulus>\n<Exponent>\nAQAB\n</Exponent>\n</RSAKeyValue>\n</KeyValue>\n  </KeyInfo>\n</Signature></signatures></signed-credential>\n'

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

def resolve_by_dpid(devices, dpid):
    for device in devices:
        if 'dpid' in devices[device] and devices[device]['dpid'] == dpid:
            return device
    return -1

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

class VTPlannerResourceManager(object):

    config = pm.getService("config")

    RESERVATION_TIMEOUT = config.get("vtplannerrm.max_reservation_duration") # sec in the allocated state

    EXPIRY_CHECK_INTERVAL = 10 # sec

    def __init__(self):
        super(VTPlannerResourceManager, self).__init__()
        # register callback for regular updates
        worker.addAsReccurring("vtplannerresourcemanager", "expire_embeddings", None, self.EXPIRY_CHECK_INTERVAL)

    def get_all_embeddings(self):
        embeddings = db_session.query(VTPlannerEmbedding)
        db_session.expunge_all() # detach the objects from the database session, so the user can not directly change the database
        return embeddings
  
    def import_vne_request(self, rspec):

        doc = etree.fromstring(rspec)

        # begin parsing vertices (switches and vms)
        virt_vertices = {}
        device_id = 0
        for item in doc.findall('.//{%s}vertex' % doc.nsmap['openflow']): 

            if item.get("type") == "vm":

                virt_vertices[device_id] = { 'dpid' : item.get('dpid'),
                                             'type' : 'vm', 
                                             'memory' : int(item.get('memory')),
                                             'cpu_frequency' : int(item.get('cpu_frequency')),
                                             'cpus_number' : int(item.get('cpus_number')) }
                device_id = device_id + 1

            else:

                virt_vertices[device_id] = { 'dpid' : item.get('dpid'),
                                             'type' : 'switch', 
                                             'tablesize' : item.get('tablesize'), 
                                             'switchtype' : item.get('switchtype') }
                device_id = device_id + 1

        if len(virt_vertices) == 0:
            raise geni_ex.GENIv3BadArgsError("RSpec does not contain any vertex")

        # begin parsing edges (virtual links)
        virt_edges = {}
        link_id = 0
        for item in doc.findall('.//{%s}edge' % doc.nsmap['openflow']):
            virt_edges[link_id] = { 'src' : item.get('srcDPID'), 
                                    'dst' : item.get('dstDPID'), 
                                    'capacity' : decode_edge_bw(item.get('bw')) }

            virt_edges[link_id]['src'] = resolve_by_dpid(virt_vertices, item.get('srcDPID'))
            virt_edges[link_id]['dst'] = resolve_by_dpid(virt_vertices, item.get('dstDPID'))
            link_id = link_id + 1

        if len(virt_edges) == 0:
            raise geni_ex.GENIv3BadArgsError("RSpec does not contain any edge")

	controller = doc.find('.//{%s}controller' % doc.nsmap['openflow']).get("url")
	email = doc.find('.//{%s}sliver' % doc.nsmap['openflow']).get("email")
	description = doc.find('.//{%s}sliver' % doc.nsmap['openflow']).get("description")

	packets = []
	for packet in doc.findall('.//{%s}packet' % doc.nsmap['openflow']):
            children = []
            for child in packet.getchildren():
                children.append([ etree.QName(child).localname, child.get('value') ] )
            packets.append(children)

        return ( virt_vertices, virt_edges, controller, email, description, packets )

    def import_substrate(self, resources, vtam_resources):

        vtam_doc = etree.fromstring(vtam_resources)
        doc = etree.fromstring(resources)

        # list substrate devices
        sub_devices = {}
        device_id = 0
        for item in doc.findall('.//{%s}datapath' % doc.nsmap['openflow']):
            sub_devices[device_id] = { 'dpid' : item.get('dpid'), 
                                       'type' : 'switch', 
                                       'ports' : {},
                                       'component_id' : item.get('component_id'),
                                       'component_manager_id' : item.get('component_manager_id') }
            for port in item.findall('.//{%s}port' % doc.nsmap['openflow']): 
                sub_devices[device_id]['ports'][int(port.get("num"))] = hex(int(port.get("features"),16))
            if len(sub_devices[device_id]['ports']) == 0:
                del sub_devices[device_id]
            else:
                device_id = device_id + 1

        if len(sub_devices) == 0:
            raise Exception("Unable to load devices")

        # list substrate links
        sub_links = {}
        link_id = 0
        for item in doc.findall('.//{%s}link' % doc.nsmap['openflow']): 

            if resolve_by_dpid(sub_devices, item.get('dstDPID')) == -1 or resolve_by_dpid(sub_devices, item.get('srcDPID')) == -1:
                continue

            sub_links[link_id] = { 'srcDPID' : item.get('srcDPID'),
                     'srcPort' : int(item.get('srcPort')),
                     'dstDPID' : item.get('dstDPID'),
                     'dstPort' : int(item.get('dstPort')),
                     'dst' : resolve_by_dpid(sub_devices, item.get('dstDPID')),
                     'src' : resolve_by_dpid(sub_devices, item.get('srcDPID')),
                     'capacity' : 100 }

            src = sub_links[link_id]['src']
            srcPort = sub_links[link_id]['srcPort']
            features = sub_devices[src]['ports'][srcPort]
            sub_links[link_id]['capacity'] = decode_port_speed(features)

            link_id = link_id + 1

        if len(sub_links) == 0:
            raise Exception("Unable to load links")

        # list substrate vm servers - links
        for node in vtam_doc.findall('.//node'):

            component_manager_id = node.get("component_manager_id")
            component_id = node.get("component_id")
            component_name = node.get("component_name")

            try:
                cpu_frequency = int(node.findall('.//cpu_frequency')[0].text)
            except:
                cpu_frequency = 2500

            try:
                cpus_number = int(node.findall('.//cpus_number')[0].text)
            except:
                cpus_number = 8

            try:
                memory = int(node.findall('.//memory')[0].text)
            except:
                memory = 16384

            sub_devices[device_id] = { 'dpid' : component_id, 
                                       'component_id' : component_id, 
                                       'component_manager_id' : component_manager_id,
                                       'component_name' : component_name,
                                       'type' : 'vm', 
                                       'cpu_frequency' : cpu_frequency,
                                       'cpus_number' : cpus_number,
                                       'memory' : memory }

            for iface in node.findall('.//service'):

                if iface.get('type') == "NetworkInterface":

                    to_network_interface_id = iface.findall('.//to_network_interface_id')
                    to_network_interface_port = iface.findall('.//to_network_interface_port')
                    from_server_interface_name = iface.findall('.//from_server_interface_name')

                    if len(to_network_interface_id) == 0 or len(to_network_interface_port) == 0 or len(from_server_interface_name) == 0:
                        continue

                    if resolve_by_dpid(sub_devices, to_network_interface_id[0].text) == -1:
                        continue

                    sub_links[link_id] = { 'srcDPID' : sub_devices[device_id]['dpid'],
                                           'srcPort' : from_server_interface_name[0].text,
                                           'dstDPID' : to_network_interface_id[0].text,
                                           'dstPort' : int(to_network_interface_port[0].text),
                                           'src' : device_id,
                                           'dst' : resolve_by_dpid(sub_devices, to_network_interface_id[0].text),
                                           'capacity' : 10000 }

                    link_id = link_id + 1

            device_id = device_id + 1

        return ( sub_devices, sub_links )

    def provision(self, slice_urn, embedding):
        
	xmlns="http://www.geni.net/resources/rspec/3"
        xmlns_xs="http://www.w3.org/2001/XMLSchema-instance"
        xmlns_openflow="/opt/foam/schemas"
        xsi="http://www.w3.org/2001/XMLSchema-instance"
        schemaLocation="http://www.geni.net/resources/rspec/3 http://www.geni.net/resources/rspec/3/request.xsd /opt/foam/schemas /opt/foam/schemas/of-resv.xsd"
	NSMAP={None:xmlns, 'xs':xmlns_xs, 'openflow':xmlns_openflow}

        # Create the root element
        root = etree.Element('rspec', type='request', attrib={"{" + xsi + "}schemaLocation" : schemaLocation}, nsmap=NSMAP)

        # Make a new document tree
        doc = etree.ElementTree(root)

        # Add the subelements
        sliver = etree.SubElement(root, '{%s}sliver' % NSMAP['openflow'], nsmap=NSMAP, email=embedding.email, description=embedding.description)
        etree.SubElement(sliver, '{%s}controller' % NSMAP['openflow'], nsmap=NSMAP, url=embedding.controller, type="primary")
        mygrp = etree.SubElement(sliver, '{%s}group' % NSMAP['openflow'], nsmap=NSMAP, name='mygrp')

        ports = {}

        # add links
        for link in embedding.virt_edges.values():

            start_id = 0
            end_id = None

            if embedding.virt_vertices[link['src']]['type'] == 'vm':
                end_id = None

            if embedding.virt_vertices[link['dst']]['type'] == 'vm':
                start_id = 1

            vlink = etree.SubElement(sliver, '{%s}vlink' % NSMAP['openflow'], nsmap=NSMAP)
            etree.SubElement(vlink, '{%s}use-group' % NSMAP['openflow'], nsmap=NSMAP, name="mygrp")
            hops = etree.SubElement(vlink, '{%s}hops' % NSMAP['openflow'], nsmap=NSMAP)
            idx = 1
            for hop in link['hops'][start_id:end_id]: 
                if hop[0] not in ports:
                    ports[hop[0]] = []
                if hop[2] not in ports:
                    ports[hop[2]] = []
                if hop[1] not in ports[hop[0]]:
                    ports[hop[0]].append(hop[1])
                if hop[3] not in ports[hop[2]]:
                    ports[hop[2]].append(hop[3])
                lnk = "%s/%s-%s/%s" % tuple(hop)
                etree.SubElement(hops, '{%s}hop' % NSMAP['openflow'], nsmap=NSMAP, index=str(idx), link=lnk)
                idx = idx + 1

        # add switches
        for node_id in embedding.virt_vertices:
 
            node = embedding.virt_vertices[node_id]

            if node['type'] == 'vm':

                for link in embedding.virt_edges.values():

                    if link['src'] == node_id:
                        from_server_interface_name=link['hops'][-1][3]
                        to_network_interface_id=link['hops'][-1][0]
                        to_network_interface_port=str(link['hops'][-1][1])

                    if link['dst'] == node_id:
                        from_server_interface_name=link['hops'][0][1]
                        to_network_interface_id=link['hops'][0][2]
                        to_network_interface_port=str(link['hops'][0][3])

                nd = etree.SubElement(mygrp, 
                                      '{%s}vm' % NSMAP['openflow'], 
                                      nsmap=NSMAP, 
                                      from_server_interface_name=from_server_interface_name,
                                      to_network_interface_id=to_network_interface_id,
                                      to_network_interface_port=to_network_interface_port,
                                      cpus_number=str(node['cpus_number']),
                                      cpu_frequency=str(node['cpu_frequency']),
                                      memory=str(node['memory']),
                                      component_id=node['component_id'], 
                                      component_manager_id=node['component_manager_id'], 
                                      component_name=node['component_name'])

            if node['type'] == 'switch':

                nd = etree.SubElement(mygrp, 
                                      '{%s}datapath' % NSMAP['openflow'], 
                                      nsmap=NSMAP, 
                                      component_id=node['component_id'], 
                                      component_manager_id=node['component_manager_id'], 
                                      dpid=node['dpid'])

                for port in ports[node['dpid']]:
                    etree.SubElement(nd, '{%s}port' % NSMAP['openflow'], nsmap=NSMAP, num=str(port))

        # flowspace zone
        match = etree.SubElement(sliver, '{%s}match' % NSMAP['openflow'], nsmap=NSMAP)

	for packet in embedding.packets:
             pkt = etree.SubElement(match, '{%s}packet' % NSMAP['openflow'], nsmap=NSMAP)
             for elm in packet:
                 etree.SubElement(pkt, '{%s}%s' % (NSMAP['openflow'], elm[0] ), nsmap=NSMAP, value=elm[1])

        etree.SubElement(match, '{%s}use-group' % NSMAP['openflow'], nsmap=NSMAP, name='mygrp')

        print tostring(doc, pretty_print=True, xml_declaration=True, encoding='UTF-8')

        raise Exception

	# send request
        import os
        local_path = "/root/.gcf"
        key_path = os.path.join(local_path, "alice-key.pem") 
        cert_path = os.path.join(local_path, "alice-cert.pem")
    
        # instanciate the client
        client = GENI2Client('127.0.0.1', 3626, key_path, cert_path)

        # make request
	print CREDS_CREATE % slice_urn
        print client.createSliver(slice_urn, [ CREDS_CREATE % slice_urn ], tostring(doc))

    def reserve_embedding(self, rspec, slice_name, owner_uuid, owner_email=None, end_time=None):

        embedding = db_session.query(VTPlannerEmbedding).filter(VTPlannerEmbedding.slice_name == slice_name).first()
        if embedding != None:
            raise VTPlannerEmbeddingAlreadyDefined(slice_name, embedding.end_time)

	# load vne request
        ( virt_vertices, virt_edges, controller, email, description, packets ) = self.import_vne_request(rspec)

	# load substrate nodes and links
        import os
        local_path = "/root/.gcf"
        key_path = os.path.join(local_path, "alice-key.pem") 
        cert_path = os.path.join(local_path, "alice-cert.pem")
    
        # instanciate the client
        client = GENI2Client(self.config.get("vtplannerrm.foam_host"), self.config.get("vtplannerrm.foam_port"), key_path, cert_path)

        # make request to foam
        resources = client.listResources([CREDS], None, True, False)

        # make request to vt-am
        creds = (self.config.get("vtplannerrm.vtam_username"),
                 self.config.get("vtplannerrm.vtam_password"),
                 self.config.get("vtplannerrm.vtam_host"), 
                 self.config.get("vtplannerrm.vtam_port"))

        #import xmlrpclib
        #s = xmlrpclib.Server("https://openflow:openflow@172.16.0.124:8445/xmlrpc/plugin", verbose=True)
        #s.listResources("remoteHashValue","projectUUID","sliceUUID")
        #s.listResourcesAndNodes()

        s = xmlrpclib.Server("https://%s:%s@%s:%s/xmlrpc/plugin" % creds)
        vtam_resources = s.ListResourcesAndNodes()

	( sub_devices, sub_links ) = self.import_substrate(resources['value'], vtam_resources)

        # compute embedding
        params = { 'mcr' : pm.getService('config').get('vtplannerrm.mcr'), 'alpha' : 0.5 }
        from vtplanner import compute_embedding
        success = compute_embedding(sub_devices, sub_links, virt_vertices, virt_edges, params)

        if success:

            embedding = VTPlannerEmbedding(virt_vertices=virt_vertices, virt_edges=virt_edges, slice_name=slice_name, owner_uuid=owner_uuid, owner_email=owner_email,controller=controller,email=email,description=description,packets=packets,provisioned=False)

            embedding.set_end_time_with_max(end_time, self.RESERVATION_TIMEOUT)
            db_session.add(embedding)
            db_session.commit()
            db_session.expunge_all() # detach the objects from the database session, so the user can not directly change the database

	    db_session.query(VTPlannerEmbedding).all()

            return embedding

        else:

            return None

    def extend_embedding(self, embedding, end_time=None):
        embedding = db_session.query(VTPlannerEmbedding).filter(VTPlannerEmbedding.slice_name == embedding.slice_name).first()
        embedding.set_end_time_with_max(end_time, self.RESERVATION_TIMEOUT)
        db_session.commit()
        db_session.expunge_all() # detach the objects from the database session, so the user can not directly change the database
        return embedding
    
    def embeddings_in_slice(self, slice_name):
        embeddings = db_session.query(VTPlannerEmbedding).filter(VTPlannerEmbedding.slice_name == slice_name).all()
        db_session.expunge_all() # detach the objects from the database session, so the user can not directly change the database
        return embeddings

    def free_embedding(self, embedding):
        embedding = db_session.query(VTPlannerEmbedding).filter(VTPlannerEmbedding.slice_name == embedding.slice_name).first()
        db_session.delete(embedding)
        db_session.commit()
        return None

    @worker.outsideprocess
    def expire_embeddings(self, params):
        logger.info("Cleaning expired embeddings...")
        embeddings = db_session.query(VTPlannerEmbedding).filter(VTPlannerEmbedding.end_time < datetime.utcnow()).all()
        for embedding in embeddings:
            self.free_embedding(embedding)
        return

    def _decode_edge_bw(self, bw):
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

# ----------------------------------------------------
# ------------------ database stuff ------------------
# ----------------------------------------------------
from sqlalchemy import Column, Integer, String, DateTime, PickleType, Boolean, create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import exists

import amsoil.core.pluginmanager as pm
import amsoil.core.log
logger=amsoil.core.log.getLogger('worker')

from amsoil.config import expand_amsoil_path

# initialize sqlalchemy
VTPLANNERDB_PATH = expand_amsoil_path(pm.getService('config').get('vtplannerrm.dbpath'))
VTPLANNERDB_ENGINE = "sqlite:///%s" % (VTPLANNERDB_PATH,)

db_engine = create_engine(VTPLANNERDB_ENGINE, pool_recycle=6000) # please see the wiki for more info
db_session_factory = sessionmaker(autoflush=True, bind=db_engine, expire_on_commit=False) # the class which can create sessions (factory pattern)
db_session = scoped_session(db_session_factory) # still a session creator, but it will create _one_ session per thread and delegate all method calls to it
Base = declarative_base() # get the base class for the ORM, which includes the metadata object (collection of table descriptions)

# We should limit the session's scope (lifetime) to one request. Yet, here we have a different solution.
# In order to avoid side effects (from someone changing a database object), we expunge_all() objects when we hand out objects to other classes.
# So, we can leave the session as it is, because there are no objects in it anyway.

class VTPlannerEmbedding(Base):

    """Please see the Database wiki page."""

    __tablename__ = 'embeddings'

    id = Column(Integer, primary_key=True)
    controller = Column(String(255))
    email = Column(String(255))
    description = Column(String(255))
    virt_vertices = Column(PickleType)
    virt_edges = Column(PickleType)
    slice_name = Column(String(255))
    owner_uuid = Column(String(100)) # could also be limited to 37, 42 or 46
    owner_email = Column(String(255)) # could also be limited to 254
    packets = Column(PickleType)
    end_time = Column(DateTime)
    provisioned = Column(Boolean)

    def set_end_time_with_max(self, end_time, max_duration):
        """If {end_time} is none, the current time+{max_duration} is assumed."""
        max_end_time = datetime.utcnow() + timedelta(0, max_duration)
        if end_time == None:
            end_time = max_end_time

        self.end_time = end_time

    @property
    def available(self):
        return not bool(self.slice_name)

Base.metadata.create_all(db_engine) # create the tables if they are not there yet

