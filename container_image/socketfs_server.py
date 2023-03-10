#!/bin/python

# import docker
from fs import open_fs
from fs.errors import ResourceNotFound
import json
import logging

import socket
import sys
import os
import ipaddress




#sys.path.append(r'./lib')
#import cosmos

# ---- CONFIG ----
# from dotenv import dotenv_values
# config = dotenv_values('../cburn.local/conf_userhome.sh')


# ---- GLOBALS ----
sys.path.append("/home/sandboxfs/target_fs")
from metafs import MetaFS
from metafs_proxy import MetaFSProxy
from target_fs import target_fs as target_fs_origin

metafs = MetaFS("/home/sandboxfs/target_fs/config-target-metafs.sh")
target_fs = MetaFSProxy(target_fs_origin, metafs)



SOCKETNAME=os.environ['TARGETFSNAME']

SERVER_ADDRESS = f'./socket/{SOCKETNAME}.sock'
LOG_ADDRESS = f'./logs/{SOCKETNAME}.log'

logging.basicConfig(filename=LOG_ADDRESS,
                    encoding='utf-8',
                    level=logging.DEBUG,
                    format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p'
                   )

open_files = dict()
NEXT_FD = 1

# Docker session
# client = docker.from_env()


# ---- OPEN FILES ----

def get_open_file_fd():
    global NEXT_FD
    res = NEXT_FD
    NEXT_FD += 1
    return res
    


# ---- MAIN LOOP ----

def main():
    try:
        os.unlink(SERVER_ADDRESS)
    except OSError:
        if os.path.exists(SERVER_ADDRESS):
            raise
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind(SERVER_ADDRESS)

    # Start server
    sock.listen(1)
    while True:
        connection, client_address = sock.accept()
        try:
            while True:
                query = connection.recv(256)
                if query:
                    cleaned = query.decode().strip()

                    rq = json.loads(cleaned)

                    for verb in rq:
                        logging.debug(f"verb: {verb}")
                        argv = rq[verb]
                        res = "OK"
                        for arg in argv:
                            logging.debug(f"arg: {arg}")

                        if verb == "ls":
                            res = json.dumps(target_fs.listdir(arg))

                        if verb == "getinfo":
                            res = json.dumps(
                                target_fs.getinfo(*argv).raw
                            )

                        if verb == "openbin":
                            fd = get_open_file_fd()
                            open_files[fd] = target_fs.openbin(
                                *argv
                            )
                            res = f"{fd}"

                        if verb == "close":
                            fd = int(argv[0])
                            open_files[fd].close()
                            open_files.pop(fd)

                        if verb == "readline":
                            fd = int(argv[0])
                            res = open_files[fd].readline()

                        if verb == "writelines":
                            fd = int(argv[0])
                            lines = [ l.encode() for l in argv[1] ]
                            open_files[fd].writelines(lines)

                        if verb == "setinfo":
                            target_fs.setinfo(*argv)

                        if verb == "mkdir":
                            target_fs.makedir(*argv)

                        if verb == "rm":
                            target_fs.remove(*argv)

                        if verb == "rmdir":
                            target_fs.removedir(*argv)

                        logging.debug(res)
                        if type(res) == bytes:
                            connection.send(res)
                        else:
                            connection.send(res.encode()+'\n'.encode())
                else:
                    break
        finally:
            connection.close()

if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        logging.exception(err)


# EOF
