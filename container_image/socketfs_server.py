#!./bin/python

# import docker
from fs import open_fs
from fs.errors import ResourceNotFound
import json

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
from target_fs import target_fs

SOCKETNAME=os.environ['TARGETFSNAME']

SERVER_ADDRESS = f'./socket/{SOCKETNAME}.sock'

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
                        print(f"verb: {verb}")
                        argv = rq[verb]
                        res = "OK"
                        for arg in argv:
                            print(f"arg: {arg}")

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

                        print(res)
                        if type(res) == bytes:
                            connection.send(res)
                        else:
                            connection.send(res.encode())
                            connection.send('\n'.encode())
                else:
                    break
        finally:
            connection.close()

if __name__ == "__main__":
    main()


# EOF
