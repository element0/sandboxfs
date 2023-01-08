#!/bin/python3

from sandboxfs import SandboxFS
from time import sleep

fs_confdir_a = "osfs_sample-a"
fs_confdir_b = "osfs_sample-b"
socket_dir = "socket"

a = SandboxFS(fs_confdir_a, socket_dir)
print(a.listdir('/'))

b = SandboxFS(fs_confdir_b, socket_dir)
print(b.listdir('/'))

# once more
"""
for i in range(1,100):
    a.listdir('/')
    b.listdir('/')
"""
