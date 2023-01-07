#!/bin/python3

from sandboxfs import SandboxFS
from time import sleep

a = SandboxFS("osfs_sample", "socket")
print(a.listdir('/'))

b = SandboxFS("/home/raygan/raygan-sshfs-private", "socket")
print(b.listdir('/'))

sleep(1)

# once more

print(a.listdir('/'))
print(b.listdir('/'))
