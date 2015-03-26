#!/usr/bin/python

# -*- coding: utf-8 -*-

from __future__ import print_function

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