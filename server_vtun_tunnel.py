#!/usr/bin/python

# -*- coding: utf-8 -*-

from __future__ import print_function

from vtun_tunnel import VtunTunnel

import subprocess
import os
import signal
import socket
import time 

vtun_pid_file = '/usr/local/var/run/vtund.pid'

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
        config += indent_unit + 'passwd ' + str(self.vtun_shared_secret) + ';' + cr_lf
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
        config += indent_unit*2 + 'ifconfig "%% ' + str(self.tunnel_near_end_ip) + ' pointopoint ' + str(self.tunnel_far_end_ip) + ' mtu 1450";' + cr_lf
        config += indent_unit + '};' + cr_lf
        config += '}' + cr_lf
        return config
        
    def start(self):
        """ Start a vtun server process to handle the service represented by this object
        """
        if not (self._vtun_pid is None and self._vtun_process is None):    # There is already a slave vtun process running
            raise Exception('VtundAlreadyRunning')
    
        #Step 1: save configuration file
        vtund_config = self.to_vtund_config()
        try:
            f = open('/tmp/vtund-%s-server.conf'%self.vtun_tunnel_name, 'w')
            f.write(vtund_config)
            f.close()
        except:
            raise Exception('ConfigurationFileWritingIssue')
        #Step 2: Runs vtun and saves the pid and process
        proc = subprocess.Popen(["vtund", "-f", "/tmp/vtund-%s-server.conf"%str(self.vtun_tunnel_name), "-s"], shell=False)
        
        pid = None
        if os.path.isfile(vtun_pid_file):
            os.remove(vtun_pid_file)
            while not os.path.isfile(vtun_pid_file):
                time.sleep(0.2)
                continue
        pid_file = open(vtun_pid_file, "r")
        pid = pid_file.read(10)
        pid_file.close()
        self._vtun_pid = pid
        #TODO: Add a watch to detect when the tunnel goes down
        
        type =  None
        if self.vtun_protocol =='tcp':
            type = socket.SOCK_STREAM
        elif self.vtun_protocol =='udp':
            type = socket.SOCK_DGRAM
        else:
            raise Exception('UnsupportedProtocol')
        
        success = False
        while not success:
            try:
                s = socket.socket(socket.AF_INET, type)
                s.connect(('localhost', int(self.vtun_server_tcp_port))) #Connect is blocking therefore it while wait until connect is successful
                s.close()
                success = True                
            except socket.error, exc:
                time.sleep(0.2)
                continue 
            
    def stop(self):
        """ Stop the vtun server process handled by this object
        """
        #print('Stopping vtun server with tunnel name ' + str(self.vtun_tunnel_name) + '\n')
        if self._vtun_pid is None:    # There is not a slave vtun process running
            raise Exception('VtundNotRunning')
        else:
            children = self.get_child_of(int(self._vtun_pid))
            success = True
            if len(children) > 0:
                for child in children:
                    try:
                        os.kill(int(child), signal.SIGTERM)
                        #print(child + ' Killed')
                    except OSError:
                        try:
                            os.kill(int(child), signal.SIGKILL)
                            #print(child + ' Killed')
                        except OSError:
                            #print(child + 'is not  Killed')
                            success = False
                
            
            try:
                os.kill(int(self._vtun_pid), signal.SIGTERM)
                #print(self._vtun_pid + ' Killed')
            except OSError:
                try:
                    os.kill(int(self._vtun_pid), signal.SIGKILL)
                    #print(self._vtun_pid + ' Killed')
                except OSError:
                    #print(self._vtun_pid + ' is not Killed')
                    success = False
            if success:
                self._vtun_pid = None
                self._vtun_process = None
            else:
                raise Exception('OneOfProcessesCouldNotBeKilled')