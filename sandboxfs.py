import socket
import sys
from fs.base import FS
from fs.path import basename
import json
import os
from time import sleep
import logging


MAXBUFSIZE=8192

logging.basicConfig(filename="logs/sandboxfs_instances.log",
                    level=logging.DEBUG
                    )
#, encoding='utf-8',level=logging.DEBUG)
                    #format='%(asctime)s %(message)s')
                    #datefmt='%m/%d/%Y %I:%M:%S %p')


class SandboxFS(FS):

    def __init__(self,targetfsdir,socketdir):
        
        target_fs_name = basename(targetfsdir)
        sockaddr = f"{socketdir}/{target_fs_name}.sock"

        self.target_fs_name = target_fs_name
        
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(3)

        if not os.path.exists(sockaddr):
            os.system(f"/bin/bash bin/start_container.sh {targetfsdir}")
            while not os.path.exists(sockaddr):
                sleep(1)

            while True:
                try:
                    self.sock.connect(sockaddr)
                    break
                except:
                    sleep(1)
        else:
            try:
                self.sock.connect(sockaddr)
            except ConnectionRefusedError as err:
                os.system(f"/bin/bash bin/start_container.sh {targetfsdir}")
                while True:
                    try:
                        self.sock.connect(sockaddr)
                        break
                    except:
                        sleep(1)
        super().__init__()

    def close(self):
        self.sock.close()

    def send_rq(self, rq):
        logging.debug(f'{self.target_fs_name}:request: {rq}')
        self.sock.sendall(rq.encode())

        res = self.sock.recv(MAXBUFSIZE)
        logging.debug(f'{self.target_fs_name}:result: {res}')


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

    

