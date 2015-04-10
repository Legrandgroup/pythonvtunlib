#!/usr/bin/python

# -*- coding: utf-8 -*-

from __future__ import print_function

import ipaddr
import re
import subprocess

from tunnel_mode import TunnelMode

class VtunTunnel(object):
    """ Class representing a vtun tunnel """
    
    VTUND_EXEC = 'vtund'
    
    def __init__(self, **kwargs):
        """ Constructor for VtunTunnel class.
        
        \param vtund_exec (optional) The exec name for the vtund utility (it is recommended to provide an absolute PATH here)
        \param vtund_use_sudo (optional) A boolean indicating whether the vtund_exec needs to be run via sudo to get root access (False by default)
        \param tundev_shell_config A string directly coming from the devshell command 'get_vtun_parameters', that will allow to set all the attributes of this object. Warning if tundev_shell_config is provided, no other argument below is allowed (or a 'SimultaneousConfigAndAgumentsNotAllowed' exception will be raised)
        \param mode A string or a TunnelMode object representing the tunnel mode. Supported values are L2, L3 and L3_multi
        \param tunnel_ip_network A string or an ipaddr.IPv4Network object containing the IP network range in use within the tunnel
        \param tunnel_near_end_ip A string or an ipaddr.IPv4Address object containing our IP address inside the tunnel (near end of the tunnel)
        \param tunnel_far_end_ip A string or an ipaddr.IPv4Address object containing  the IP address of the peer inside the tunnel (far end of the tunnel)
        \param vtun_server_tcp_port (optional, can be set to None if unknown) a string or an int describing the outer TCP port of the process handling the tunnel
        \param vtun_tunnel_name A string containing the name of the vtun tunnel.
        \param vtun_shared_secret A string containing the password for the vtun session. 
        """
        self._vtun_pid = None    # The PID of the slave vtun process handling this tunnel
        self._vtun_process = None    # The python process object handling this tunnel
        
        arg_vtund_exec = kwargs.get('vtund_exec', None)
        if arg_vtund_exec is None:
            self.vtund_exec = VtunTunnel.VTUND_EXEC
        else:
            self.vtund_exec = arg_vtund_exec
        
        self.vtund_use_sudo = kwargs.get('vtund_use_sudo', False)  # Do we use sudo to run subprocess vtund?
        
        arg_vtun_tunnel_name = kwargs.get('vtun_tunnel_name', None)
        if arg_vtun_tunnel_name is None:
            raise Exception('TunnelNameMustBeProvided')
        else:
            self.set_tunnel_name(arg_vtun_tunnel_name)
        arg_vtun_shared_secret = kwargs.get('vtun_shared_secret', None)
        if arg_vtun_shared_secret is None:
            raise Exception('TunnelSharedSecretMustBeProvided')
        else:
            self.set_shared_secret(arg_vtun_shared_secret)
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
        elif mode is 'L3_multi':
            raise Exception('TunnelModeL3_MultiNotSupportedYet')
        
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
        if re.compile(r'^[0-9]+$').search(str(key)):
            raise Exception('SessionSharedSecretCannotBeOnlyDigits')
        self.vtun_shared_secret = key
    
    def get_shared_secret(self):
        """ Get the shared secret for the tunnel
        
        \return A string containing the shared secret for the tunnel
        """
        return self.vtun_shared_secret
    
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
        if self.vtun_shared_secret is None:
            return False
        if self.vtun_tunnel_name is None:
            return False
        # Note: vtun_server_tcp_port is not stricly required to define a valid the tunnel (but it will be to start it)
        return True
    
    def to_vtund_config(self, up_additionnal_commands = None, down_additionnal_commands = None):
        """ Generate a vtund config matching with the state of this object and return it as a string
        \param up_additionnal_commands A list of commands to add to the up {} section of the configuration file
        \param down_additionnal_commands A list of commands to add to the down {} section of the configuration file
        """
        pass    # 'virtual' method
    
    def start(self):
        """ Start the vtund exec (generic for server or client)
        """
        pass #Virtual
    
    def stop(self):
        """ Start the vtund exec (generic for server or client)
        """
        pass #Virtual

    def get_child_of(self, pid):
        p = subprocess.Popen('pgrep -P %d'%pid,stdout=subprocess.PIPE,shell=True)
        children_pid  = [x for x in p.communicate()[0].split("\n") if x and x != str(p.pid)]
        p.wait()
        return children_pid


