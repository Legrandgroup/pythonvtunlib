#!/usr/bin/python

# -*- coding: utf-8 -*-

from __future__ import print_function

from vtun_tunnel import VtunTunnel

class ClientVtunTunnel(VtunTunnel):
    
    """ Class representing a vtun tunnel client (connecting) """
    def __init__(self, **kwargs): # See VtunTunnel.__init__ for the inherited kwargs
        """ Constructor (see VtunTunnel.__init__ for the inherited kwargs)
        \param from_server Create a vtun client configuration to connect to the ServerVtunTunnel object specified as \p from_server
        \param vtun_server_hostname The hostname or IP address of the vtun server this client will connect to. If not provided at construction, a subsequent call to set_vtun_server_hostname() will be required
        """
        arg_from_server = kwargs.get('from_server', None) # Server from which we create a client config
        if arg_from_server is None:
            super(ClientVtunTunnel, self).__init__(**kwargs)
        else:   # We are building the client config to match a server config
            if not isinstance(arg_from_server, ServerVtunTunnel):
                raise Exception('WrongFromServerObject')
            super(ClientVtunTunnel, self).__init__(mode =  arg_from_server.tunnel_mode, tunnel_ip_network = arg_from_server.tunnel_ip_network, tunnel_near_end_ip = arg_from_server.tunnel_far_end_ip, tunnel_far_end_ip = arg_from_server.tunnel_near_end_ip, vtun_server_tcp_port = arg_from_server.vtun_server_tcp_port)
            self.tunnel_key = arg_from_server.tunnel_key
        self.vtun_server_hostname = kwargs.get('vtun_server_hostname', None)  # The remote host to connect to (if provided)
        # Note: in all cases, the caller will need to provide a vtun_server_hostname (it is not part of the ServerVtunTunnel object)
    
    def set_vtun_server_hostname(self, vtun_server_hostname):
        """ Set the remote host to connect to
        
        (this is mandatory after populating ClientVtunTunnel's attribute using from_server on ClientVtunTunnel's constructor)
        
        \param vtun_server_hostname The hostname or IP address of the vtun server this client will connect to
        """
        self.vtun_server_hostname = vtun_server_hostname
    
       
    def to_vtund_config(self):
        """ Generate a vtund config string matching with this object attributes
        
        \return A string containing a configuration to provide to the vtund exec
        """
        indent_unit = '\t'
        cr_lf = '\r\n';
        config = ''
        config += 'options {' + cr_lf
        config += indent_unit + 'port ' + str(self.vtun_server_tcp_port) + ';' + cr_lf
        #FIXME: add vtun_connection_timeout attribute! config += ' timeout ' + str(self.vtun_connection_timeout) + ';\n'
        
        config += indent_unit + 'timeout 600;' + cr_lf
        
        config += indent_unit + 'ppp /usr/sbin/pppd;' + cr_lf
        config += indent_unit + 'ifconfig /sbin/ifconfig;' + cr_lf
        config += indent_unit + 'route /sbin/route;' + cr_lf
        config += indent_unit + 'ip /sbin/ip;' + cr_lf
        config += '}' + cr_lf
        config += '' + cr_lf
        config += self.vtun_tunnel_name + ' {' + cr_lf
        config += indent_unit + 'passwd ' + str(self.tunnel_key) + ';' + cr_lf
        config += indent_unit + 'persist no;' + cr_lf
        config += cr_lf
        config += indent_unit + 'up {' + cr_lf
        config += indent_unit * 2  + 'ifconfig "%% ' + str(self.tunnel_near_end_ip) + ' pointtopoint ' + str(self.tunnel_far_end_ip) + ' mtu 1450";' + cr_lf
        config += indent_unit + '};' + cr_lf
        config += '}' + cr_lf
        return config
    
    def is_valid(self): # Overload is_valid() for client tunnels... we also need a vtun_server_hostname
        """ Check if our attributes are enough to define a vtun tunnel
        Returns True if all minimum attributes are set
        """
        if not super(ClientVtunTunnel, self).is_valid():    # First ask parent's is_valid()
            return False
        if self.vtun_server_hostname is None:
            return False
        return True