#!/usr/bin/python

# -*- coding: utf-8 -*-

from __future__ import print_function

import ipaddr

class TunnelMode(object):
    def __init__(self, mode):
        """ Constructor
        \param mode A string representing the tunnel mode. Supported values are L2, L3 and L3_multi
        """
        self.set_mode(mode)
    
    def set_mode(self, mode):
        """ Set the tunnel mode
        \param mode The mode to use on this tunnel. Supported values are L2, L3 and L3_multi
        """
        if mode == 'L2' or mode == 'L3' or mode == 'L3_multi':
            self._mode = mode
        else:
            raise Exception('InvalidTunnelMode:' + str(mode))
    
    def get_mode(self):
        return self._mode
        
    def get_equivalent_vtun_type(self):
        """ Get the vtun type for this mode object
        
        \return A vtun type (as used in vtund configuration) as a string
        """
        if self._mode == 'L2':
            return 'tap'
        if self._mode == 'L3' or self._mode == 'L3_multi':
            return 'tun'
        else:
            raise Exception('InvalidTunnelMode:' + str(self._mode))
        
        
    def __str__(self):
        return self.get_mode()

class VtunTunnel(object):
    """ Class representing a vtun tunnel """
    
    def __init__(self, **kwargs):
        """ Constructor for VtunTunnel class.
        
        \param tundev_shell_config A string directly coming from the devshell command 'get_vtun_parameters', that will allow to set all the attributes of this object. Warning if tundev_shell_config is provided, no other argument below is allowed (or a 'SimultaneousConfigAndAgumentsNotAllowed' exception will be raised)
        \param mode A string or a TunnelMode object representing the tunnel mode. Supported values are L2, L3 and L3_multi
        \param tunnel_ip_network A string or an ipaddr.IPv4Network object containing the IP network range in use within the tunnel
        \param tunnel_near_end_ip A string or an ipaddr.IPv4Address object containing our IP address inside the tunnel (near end of the tunnel)
        \param tunnel_far_end_ip A string or an ipaddr.IPv4Address object containing  the IP address of the peer inside the tunnel (far end of the tunnel)
        \param vtun_server_tcp_port (optional, can be set to None if unknown) a string or an int describing the outer TCP port of the process handling the tunnel
        """
        self._vtun_pid = None    # The PID of the slave vtun process handling this tunnel
        self._vtun_process = None    # The python process object handling this tunnel
        
        self.vtun_tunnel_name = None
        arg_mode = kwargs.get('mode', None) # Type of tunnel (L2, L3 or L3_multi)
        arg_tunnel_ip_network = kwargs.get('tunnel_ip_network', None) # IP network (range) for the addressing within the tunnel
        arg_tunnel_near_end_ip = kwargs.get('tunnel_near_end_ip', None) # IP address of the near end of the tunnel (internal to the tunnel)
        arg_tunnel_far_end_ip = kwargs.get('tunnel_far_end_ip', None) # IP address of the far end of the tunnel (internal to the tunnel)
        arg_vtun_server_tcp_port = kwargs.get('vtun_server_tcp_port', None)   # TCP port on which to connect on the tunnel server machine

        arg_tundev_shell_config = kwargs.get('tundev_shell_config', None)  # Check if there is a tundev_shell_config argument
        if arg_tundev_shell_config:    # If so, we will generate set our attributes according to the config
            if not (arg_tunnel_ip_network is None and arg_tunnel_near_end_ip is None and arg_tunnel_far_end_ip is None and vtun_server_tcp_port is None):    # We also have a specific argument
                raise Exception('SimultaneousConfigAndAgumentsNotAllowed') 
            else:
                self.set_characteristics_from_string(arg_tundev_shell_config)
        else:
            self.set_characteristics(str(arg_mode), arg_tunnel_ip_network, arg_tunnel_near_end_ip, arg_tunnel_far_end_ip, arg_vtun_server_tcp_port)

    def set_characteristics(self, mode, tunnel_ip_network, tunnel_near_end_ip, tunnel_far_end_ip, vtun_server_tcp_port):
        """ Set this object tunnel parameters
        
        \param mode A string or a TunnelMode object reprensenting the tunnel mode. Supported values are L2, L3 and L3_multi
        \param tunnel_ip_network A string containing the IP network range in use within the tunnel
        \param tunnel_near_end_ip A string containing our IP address inside the tunnel (near end of the tunnel)
        \param tunnel_far_end_ip A string containing  the IP address of the peer inside the tunnel (far end of the tunnel)
        \param vtun_server_tcp_port (optional, can be set to None if unknown) a string or an int describing the outer TCP port of the process handling the tunnel
        """
        if mode is None:
            raise Exception('TunnelModeCannotBeNone')
        
        self.tunnel_mode = TunnelMode(str(mode))
        self.tunnel_ip_network = ipaddr.IPv4Network(str(tunnel_ip_network))
        self.tunnel_near_end_ip = ipaddr.IPv4Address(str(tunnel_near_end_ip))
        self.tunnel_far_end_ip = ipaddr.IPv4Address(str(tunnel_far_end_ip))
        
        if vtun_server_tcp_port is None:
            self.vtun_server_tcp_port = None   # Undefined TCP ports are allowed, but we will need to specify the port before starting the tunnel!
        else:
            try:
                tcp_port = int(vtun_server_tcp_port)
            except ValueError:
                raise Exception('InvalidTcpPort:' + str(tcp_port))
            
            if tcp_port > 0 and tcp_port <= 65535:
                self.vtun_server_tcp_port = tcp_port
            else:
                raise Exception('InvalidTcpPort:' + str(tcp_port))

    def set_shared_secret(self, key):
        """ Set the shared secret for the tunnel
        
        \param key A string containing the shared secret for the tunnel
        """
        self.tunnel_key = key
    
    def set_tunnel_name(self, name):
        """ Set the vtun tunnel name
        
        \param name A string containing the name of the tunnel
        """
        self.vtun_tunnel_name = name
    
    def is_valid(self):
        """ Check if our attributes are sufficiently filled-in to define for a vtund process to be run
        
        Note: this method can be overloaded by ClientVtunTunnel and ServerVtunTunnel
        
        \return True if all minimum attributes are set
        """
        if self.tunnel_mode is None:
            return False
        if self.tunnel_ip_network is None:
            return False
        if self.tunnel_near_end_ip is None:
            return False
        if self.tunnel_far_end_ip is None:
            return False
        if self.tunnel_key is None:
            return False
        if self.vtun_tunnel_name is None:
            return False
        # Note: vtun_server_tcp_port is not stricly required to define a valid the tunnel (but it will be to start it)
        return True
    
    def to_vtund_config(self):
        """ Generate a vtund config matching with the state of this object and return it as a string
        """
        pass    # 'virtual' method
    
    def start(self):
        """ Start the vtund exec (generic for server or client)
        """
        if not (self._vtun_pid is None and self._vtun_process is None):    # There is already a slave vtun process running
            raise Exception('VtundAlreadyRunning')
        vtund_config = self.to_vtund_config()
        print('Debug: will use the following vtund config:')
        print(vtund_config)
        # Save into a file
        # Run the process on the file
        #raise Exception('NotYetImplemented')
    
    def stop(self):
        """ Start the vtund exec (generic for server or client)
        """
        # Check PID and subprocess
        # Kill them, remove the temporary config file
        print('Debug: will stop vtun')
        #raise Exception('NotYetImplemented')

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
        config += ' timeout ' + str(self.vtun_connection_timeout) + ';\n'
        
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

