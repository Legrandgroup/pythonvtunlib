#!/usr/bin/python

# -*- coding: utf-8 -*-

from __future__ import print_function

from vtun_tunnel import VtunTunnel
import server_vtun_tunnel

import subprocess

import threading

import os

class ClientVtunTunnel(VtunTunnel):
    
    """ Class representing a vtun tunnel client (connecting) """
    def __init__(self, **kwargs): # See VtunTunnel.__init__ for the inherited kwargs
        """ Constructor (see VtunTunnel.__init__ for the inherited kwargs)
        \param from_server Create a vtun client configuration to connect to the ServerVtunTunnel object specified as \p from_server
        \param vtun_server_hostname The hostname or IP address of the vtun server this client will connect to. If not provided at construction, a subsequent call to set_vtun_server_hostname() will be required
        \param vtun_connection_timeout The timeout limit from the client to connect.
        """
        arg_from_server = kwargs.get('from_server', None) # Server from which we create a client config
        if arg_from_server is None:
            super(ClientVtunTunnel, self).__init__(**kwargs)
        else:   # We are building the client config to match a server config
            if not isinstance(arg_from_server, server_vtun_tunnel.ServerVtunTunnel):
                raise Exception('WrongFromServerObject')
            super(ClientVtunTunnel, self).__init__(vtund_exec = arg_from_server.vtund_exec, mode = arg_from_server.tunnel_mode, tunnel_ip_network = arg_from_server.tunnel_ip_network, tunnel_near_end_ip = arg_from_server.tunnel_far_end_ip, tunnel_far_end_ip = arg_from_server.tunnel_near_end_ip, vtun_server_tcp_port = arg_from_server.vtun_server_tcp_port, vtun_tunnel_name = arg_from_server.vtun_tunnel_name, vtun_shared_secret = arg_from_server.vtun_shared_secret)
        self.vtun_server_hostname = kwargs.get('vtun_server_hostname', None)  # The remote host to connect to (if provided)
        # Note: in all cases, the caller will need to provide a vtun_server_hostname (it is not part of the ServerVtunTunnel object)
        self.vtun_connection_timeout = kwargs.get('vtun_connection_timeout', 300) # 5Min for default client timeout. Purely arbitary choosen value here. Might change in the future.
        self._vtund_output_buf = None    # Attribute containing the console output of the child process
        self._vtund_output_watcher_thread = None    # A thread to watch the console output and store it inside  self._vtund_output_buf above
        self._vtun_process = None
        self._vtun_pid = None
        self.vtund_exit_value = None
    
    def set_vtun_server_hostname(self, vtun_server_hostname):
        """ Set the remote host to connect to
        
        (this is mandatory after populating ClientVtunTunnel's attribute using from_server on ClientVtunTunnel's constructor)
        
        \param vtun_server_hostname The hostname or IP address of the vtun server this client will connect to
        """
        self.vtun_server_hostname = vtun_server_hostname
    
       
    def to_vtund_config(self, up_additionnal_commands = None, down_additionnal_commands = None, device_name = None):
        """ Generate a vtund config string matching with this object attributes
        \param up_additionnal_commands A list of commands to add to the up {} section of the configuration file
        \param down_additionnal_commands A list of commands to add to the down {} section of the configuration file
        \param device_name The name to give to the tunnel network interface
        \return A string containing a configuration to provide to the vtund exec
        """
        indent_unit = '\t'
        cr_lf = '\n';
        config = ''
        config += 'options {' + cr_lf
        config += indent_unit + 'port ' + str(self.vtun_server_tcp_port) + ';' + cr_lf
        config += indent_unit + 'timeout ' + str(self.vtun_connection_timeout) + ';' + cr_lf        
        config += indent_unit + 'ppp /usr/sbin/pppd;' + cr_lf
        config += indent_unit + 'ifconfig /sbin/ifconfig;' + cr_lf
        config += indent_unit + 'route /sbin/route;' + cr_lf
        config += indent_unit + 'ip /sbin/ip;' + cr_lf
        config += '}' + cr_lf
        config += cr_lf
        config += self.vtun_tunnel_name + ' {' + cr_lf
        if not device_name is None:
            config += indent_unit + 'device ' + str(device_name) + ';' + cr_lf
        config += indent_unit + 'passwd ' + str(self.vtun_shared_secret) + ';' + cr_lf
        config += indent_unit + 'persist no;' + cr_lf
        config += cr_lf
        config += indent_unit + 'up {' + cr_lf
        config += indent_unit * 2  + 'ifconfig "%% ' + str(self.tunnel_near_end_ip) + ' pointopoint ' + str(self.tunnel_far_end_ip) + ' mtu 1450";' + cr_lf
        if not up_additionnal_commands is None:
            for command in up_additionnal_commands:
                if command[0] == '/':
                    config += indent_unit*2 + 'program ' + str(command) + ';' + cr_lf
                else:
                    raise Exception('NotAFullPathCommand')
        config += indent_unit + '};' + cr_lf
        config += indent_unit + 'down {' + cr_lf
        if not down_additionnal_commands is None:
            for command in down_additionnal_commands:
                if command[0] == '/':
                    config += indent_unit*2 + 'program ' + str(command) + ';' + cr_lf
                else:
                    raise Exception('NotAFullPathCommand')
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
    
    def start(self):
        """ Start the vtund exec
        """
        if not (self._vtun_pid is None and self._vtun_process is None):    # There is already a slave vtun process running
            raise Exception('VtundAlreadyRunning')
        
        if self.vtun_server_hostname is None:	# No vtun server has been defined
                raise Exception('TunnelServerHostnameMustBeProvided')
        
        if not self.is_valid():
                raise Exception('InvalidTunnelConfiguration')
        
        #Step 1: save configuration file
        vtund_config = self.to_vtund_config()
        vtund_config_filename = '/tmp/vtund-' + str(self.vtun_tunnel_name) + '-client.conf'
        try:
            f = open(vtund_config_filename, 'w')
            f.write(vtund_config)
            f.close()
        except:
            raise Exception('ConfigurationFileWritingIssue')
        
        #Step 2: Runs vtun and saves the pid and process
        vtund_cmd = []
        if self.vtund_use_sudo:
                vtund_cmd = ['sudo']
        vtund_cmd += [self.vtund_exec, '-n', '-f', vtund_config_filename, str(self.vtun_tunnel_name), str(self.vtun_server_hostname)]
        proc = subprocess.Popen(vtund_cmd, shell=False, stdin=open(os.devnull, "r"), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self._vtun_process = proc
        self._vtun_pid = proc.pid
        self._vtund_output_buf = ''
        self._vtun_process_exit_expected = threading.Event()
        self.vtund_exit_value = None
        self._vtund_output_watcher_thread = threading.Thread(target = self._vtund_output_watcher)
        self._vtund_output_watcher_thread.setDaemon(True) # _vtundd_output_watcher should be forced to terminate when main program exits
        self._vtund_output_watcher_thread.start()
    
    def _checkPid(self, pid):
        """ Check For the existence of a UNIX PID
        """
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        else:
            return True
            
    def stop(self):
        if self._vtun_pid is None or self._vtun_process is None:
            raise Exception('VtundNotRunning')
        else:
            self._vtun_process_exit_expected.set()  # We are killing the subprocess, so expect it to exit
            if self.vtund_use_sudo:
                pid = self._vtun_pid
                if not self._vtun_pid is None and pid != 1:
                    args = ['sudo', 'kill', '-SIGINT', str(pid)] # Send Ctrl+C to slave DHCP client process
                    subprocess.call(args, stdout=open(os.devnull, 'wb'), stderr=subprocess.STDOUT)
                    while self._checkPid(pid): # Loop if slave process is still running
                        time.sleep(0.1)
                        timeout -= 0.1
                        if timeout <= 0: # We have reached timeout... send a SIGKILL to the slave process to force termination
                            args = ['sudo', 'kill', '-SIGKILL', str(pid)] # Send Ctrl+C to slave DHCP client process
                            subprocess.call(args, stdout=open(os.devnull, 'wb'), stderr=subprocess.STDOUT)
                            break
            else:
                self._vtun_process.terminate()
            self._vtun_process.wait()
            self._vtun_pid = None
            self._vtun_process = None
    
    def _vtund_output_watcher(self):
        """ Watch the output of the vtund subprocess and store it in a buffer
        """
        if self._vtund_output_buf or self._vtun_process is None:
            raise Exception('SubprocessOutputNotReady')
        
        try:
            while True:
                new_output = self._vtun_process.stdout.read(1)
                if new_output == '':
                    poll_result = self._vtun_process.poll()
                    if poll_result is None:   # Process actually died
                        self.vtund_exit_value = poll_result    # Store exit value
                        if self._vtun_process_exit_expected.is_set():   # We have been informed that the subprocess would exit, so this is expected
                            del self._vtun_process_exit_expected    # Remove this event from attributes
                            self._vtun_pid = None   # Forget about slave... it is not running anymore
                            self._vtun_process = None
                            break   # No need to continue parsing output, process has exitted
                        else:   # Subprocess died unexpectedly
                            raise Exception('SubprocessDiedUnexpectedly')
                    else:   # Got eof but process is still alive
                        raise Exception('GotEofFromSubprocess')
                else:
                    self._vtund_output_buf += new_output    # Continue building output buffer
        except AttributeError:    # AttributeError NoneType exceptions happen when our objects were deleted (subprocessed was killed) while in the loop
            pass    # Just discard and exit the thread
        
    def get_output(self):
        """ Get the console output (stdout and stderr) from the child vtund process
        
        \return A string containing the full output (or None if we could not get the output)
        """
        return self._vtund_output_buf
