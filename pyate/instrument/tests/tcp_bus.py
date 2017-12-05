# -*- coding: utf-8 -*-
"""
Created on Mon Dec  4 16:47:50 2017

@author: kyleh
"""

from socket import socket, timeout, AF_INET, SOCK_STREAM, IPPROTO_TCP

bus = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)
bus.settimeout(5)
bus.connect(('172.29.92.133', 1234))
