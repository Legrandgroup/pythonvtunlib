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
        indent_unit = '\t'
        cr_lf = '\n';
        config = ''
        config += 'options {' + cr_lf
        config += indent_unit + 'port ' + str(self.vtun_server_tcp_port) + ';' + cr_lf
        if self.restricted_iface:
            config += indent_unit + 'bindaddr { iface ' + self.restricted_iface + '; };' + cr_lf
        config += indent_unit + 'syslog daemon;' + cr_lf
        
        config += indent_unit + 'ppp /usr/sbin/pppd;' + cr_lf
        config += indent_unit + 'ifconfig /sbin/ifconfig;' + cr_lf
        config += indent_unit + 'route /sbin/route;' + cr_lf
        config += indent_unit + 'ip /sbin/ip;' + cr_lf
        config += '}' + cr_lf
        config += cr_lf
        config += self.vtun_tunnel_name + ' {' + cr_lf
        config += indent_unit + 'passwd ' + str(self.tunnel_key) + ';' + cr_lf
        config += indent_unit + 'type ' + self.tunnel_mode.get_equivalent_vtun_type() + ';' + cr_lf
        config += indent_unit + 'proto ' + self.vtun_protocol + ';' + cr_lf
        config += indent_unit + 'compress ' + self.vtun_compression + ';' + cr_lf
        config += indent_unit + 'encrypt '
        if self.vtun_encryption:
            config += 'yes'
        else:
            config += 'no'
        config += ';' + cr_lf
        config += indent_unit + 'keepalive '
        if self.vtun_keepalive:
            config += 'yes'
        else:
            config += 'no'
        config += ';' + cr_lf
        
        config += ' ' + cr_lf
        config += indent_unit + 'up {' + cr_lf
        config += indent_unit*2 + 'ifconfig "%% ' + str(self.tunnel_near_end_ip) + ' pointtopoint ' + str(self.tunnel_far_end_ip) + ' mtu 1450";' + cr_lf
        config += indent_unit + '};' + cr_lf
        config += '}' + cr_lf
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