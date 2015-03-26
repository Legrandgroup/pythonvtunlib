#!/usr/bin/python

# -*- coding: utf-8 -*-

from __future__ import print_function

from vtun_tunnel import VtunTunnel

class ServerVtunTunnel(VtunTunnel):
    """ Class representing a vtun tunnel service (listening) """
    
    def __init__(self, **kwargs): # See VtunTunnel.__init__ for the inherited kwargs
        super(ServerVtunTunnel, self).__init__(**kwargs)
        self.restricted_iface = None
        self.vtun_protocol = kwargs.get('vtun_protocol', 'tcp')  # valid values are tcp or udp
        self.vtun_compression = kwargs.get('vtun_compression', 'lzo:9') # See vtun documentation for valid values
        self.vtun_encryption = kwargs.get('vtun_encryption', False) 
        self.vtun_keepalive = kwargs.get('vtun_keepalive', True)

    def restrict_server_to_iface(self, iface):
        """ Restrict the server to run only on specified interface(s)
        
        \param iface The network interface (as a string) on on the server should listen
        """
        self.restricted_iface = iface
    
    #~ def is_valid(self): # Overload is_valid() for server tunnels...
        #~ """ Check if our attributes are enough to define a vtun tunnel server
        #~ Returns True if all minimum attributes are set
        #~ """
        #~ if not super(ServerVtunTunnel, self).is_valid():    # First ask parent's is_valid()
            #~ return False
        #~ return True

    def to_vtund_config(self):
        """ Generate a vtund config string matching with this object attributes
        
        \return A string containing a configuration to provide to the vtund exec
        """
        config = ''
        config += 'options {\n'
        config += ' port ' + str(self.vtun_server_tcp_port) + ';\n'
        if self.restricted_iface:
            config += ' bindaddr { iface ' + self.restricted_iface + '; };\n'
        config += 'syslog daemon;\n'
        
        config += 'ppp /usr/sbin/pppd;\n'
        config += 'ifconfig /sbin/ifconfig;\n'
        config += 'route /sbin/route;\n'
        config += 'ip /sbin/ip;\n'
        config += '}\n'
        config += '\n'
        config += self.vtun_tunnel_name + ' {\n'
        config += ' passwd ' + str(self.tunnel_key) + ';\n'
        config += ' type ' + self.tunnel_mode.get_equivalent_vtun_type() + ';\n'
        config += ' proto ' + self.vtun_protocol + ';\n'
        config += ' compress ' + self.vtun_compression + ';\n'
        config += ' encrypt '
        if self.vtun_encryption:
            config += 'yes'
        else:
            config += 'no'
        config += ';\n'
        config += ' keepalive '
        if self.vtun_keepalive:
            config += 'yes'
        else:
            config += 'no'
        config += ';\n'
        
        config += ' \n'
        config += ' up {\n'
        config += '  ifconfig "%% ' + str(self.tunnel_near_end_ip) + ' pointtopoint ' + str(self.tunnel_far_end_ip) + ' mtu 1450";\n'
        config += ' };\n'
        config += '}\n'
        return config
        
        def start(self):
            """ Start a vtun server process to handle the service represented by this object
            """
            print('Starting vtun server with tunnel name ' + str(self.vtun_tunnel_name) + ' (doing nothing)!')
            print('Config file for vtund would be "' + self.to_vtund_config() + '"')
        
        def stop(self):
            """ Stop the vtun server process handled by this object
            """
            print('Stopping vtun server with tunnel name ' + str(self.vtun_tunnel_name) + ' (doing nothing)!')