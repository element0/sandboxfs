import socket
import sys
from fs.base import FS
from fs.path import basename
import json
import os
from time import sleep


MAXBUFSIZE=8192


class SandboxFS(FS):
    def __init__(self,targetfsdir,socketdir):
        os.system(f"/bin/bash bin/start_container.sh {targetfsdir}")
        sleep(3)

        target_fs_name = basename(targetfsdir)
        sockaddr = f"{socketdir}/{target_fs_name}.sock"

        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            self.sock.connect(sockaddr)
        except:
            print(f"SocketFS::__init__ can't connect to socket {sockaddr}")
        super().__init__()

    def close(self):
        self.sock.close()

    def send_rq(self, rq):
        print(rq)
        self.sock.sendall(rq.encode())

        res = self.sock.recv(MAXBUFSIZE)
        print(res)

        return res

    def getinfo(self, path, namespaces=None):
        rq = '{"getinfo":["' + path + '",' + json.dumps(namespaces) +']}'
        res = self.send_rq(rq)
        return json.loads(res.decode())

    def listdir(self, path):
        rq = '{"ls":["' + path + '"]}'
        res = self.send_rq(rq)
        return json.loads(res.decode())

    def makedir(self, path, permissions=None, recreate=False):
        rq = '{"mkdir":["' + path + '"]}'
        res = self.send_rq(rq)


    def openbin(self, path, mode="r"):
        pass

    def remove(self, path):
        pass

    def removedir(self, path):
        pass

    def setinfo(self, raw):
        pass

    

