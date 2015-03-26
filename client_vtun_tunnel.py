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
    
    def from_tundev_shell_ouput(self, tundev_shell_config):
        """ Set this object tunnel parameters from a string following the tundev shell output format of the command 'get_vtun_parameters'
        \param tundev_shell_config
        
        FIXME: move this into ClientVtunTunnel's constructor kwargs
        """
        raise Exception('NotYesImplemented')
    
    def to_vtund_config(self):
        """ Generate a vtund config string matching with this object attributes
        
        \return A string containing a configuration to provide to the vtund exec
        """
        config = ''
        config += 'options {\n'
        config += ' port ' + str(self.vtun_server_tcp_port) + ';\n'
        #FIXME: add vtun_connection_timeout attribute! config += ' timeout ' + str(self.vtun_connection_timeout) + ';\n'
        config += ' timeout 600;\n'
        
        config += 'ppp /usr/sbin/pppd;\n'
        config += 'ifconfig /sbin/ifconfig;\n'
        config += 'route /sbin/route;\n'
        config += 'ip /sbin/ip;\n'
        config += '}\n'
        config += '\n'
        config += self.vtun_tunnel_name + ' {\n'
        config += ' passwd ' + str(self.tunnel_key) + ';\n'
        config += ' persist no;\n'
        config += ' \n'
        config += ' up {\n'
        config += '  ifconfig "%% ' + str(self.tunnel_near_end_ip) + ' pointtopoint ' + str(self.tunnel_far_end_ip) + ' mtu 1450";\n'
        config += ' };\n'
        config += '}\n'
        return config
        return config_file  # TODO
    
    def is_valid(self): # Overload is_valid() for client tunnels... we also need a vtun_server_hostname
        """ Check if our attributes are enough to define a vtun tunnel
        Returns True if all minimum attributes are set
        """
        if not super(ClientVtunTunnel, self).is_valid():    # First ask parent's is_valid()
            return False
        if self.vtun_server_hostname is None:
            return False
        return True
        
    
    def from_tundev_shell_output(self, input):
        raise Exception('NotYetImplemented')    # FIXME: to be implemented