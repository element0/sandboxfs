import redis
import json

import fs.errors
from fs.base import FS
from fs.path import split as path_split
from fs.info import Info
from dotenv import dotenv_values



class MetaFS(FS):

    def __init__(self,
                 userhome_config_path,
                 redis_config_path="config-redis.sh"):
        super().__init__()
        config = {
            **dotenv_values(redis_config_path),
            **dotenv_values(userhome_config_path)
        }
        fsurn = f'fs:{config["USERPUBLICID"]}:{config["USERHOMENAME"]}:{config["USERFSURL"]}'

        r = redis.Redis(
                config['REDIS_CONTAINER_NAME'],
                config['REDIS_CONTAINER_PORT'],
                db=0)
        self.redis = r

        if(r.get('curino') == None):
            r.set('curino',1)

        fsnokey = r.get(fsurn)
        if(fsnokey == None):
            ino = self.getnextino()
            fsnokey = self.makefsnokey(ino)
            inokey = self.makeinokey(ino)

            r.set(fsurn,fsnokey)

            r.set(fsnokey,
                json.dumps({
                    "root":inokey,
                    "urn":fsurn,
                    "user":config['USERPUBLICID'],
                    "url":config['USERFSURL']
                })
            )
        

        self.config = config
        self.fsurn = fsurn
        self.fsnokey = fsnokey

        fsrecord = self.getrecord(fsnokey)

        rootinokey = fsrecord['root']
        self.rootinokey = rootinokey

        rootino_record = self.getrecord(rootinokey)
        if not rootino_record:
            rootino_record = {"info":{"basic":{"name":"", "is_dir":True}}}
            self.setrecord(rootinokey,rootino_record)


    def lookup(self, inokey, pathseg):
        recordstr = self.redis.get(inokey)
        if not recordstr:
            return None

        record = json.loads(recordstr)
        if "dir" in record:
            for entrykey in record["dir"]:
                entrystr = self.redis.get(entrykey)
                entry = json.loads(entrystr)
                if entry["info"]["basic"]["name"] == pathseg:
                    return entrykey
        return None

    def pathwalk(self, path):
        if path == "/" or path == "":
            return self.rootinokey
        path = path.lstrip('/')
        segs = path.split('/')
        nextinokey = self.rootinokey
        for pathseg in segs:
            nextinokey = self.lookup(nextinokey, pathseg)
            if nextinokey == None:
                return None
        return nextinokey

    def getnextino(self):
        nextino = self.redis.incr('curino') 
        return nextino

    def makerootinode(self):
        rootinokey = self.rootinokey
        record_dict = {
            "info":{"basic":{"name":"","is_dir":True}},
            "dir": [],
            "par": self.fsnokey.decode(),
        }
        self.redis.set(rootinokey, json.dumps(record_dict))
        return rootinokey


    def makefsnokey(self, num):
        return f'fs:{num}'

    def makeinokey(self,num):
        return f'ino:{num}'


    def getrecord(self, inokey):
        record_str = self.redis.get(inokey)
        if not record_str:
            return None
        return json.loads(record_str)

    def setrecord(self, inokey, record):
        if not record:
            record_str = ""
        else:
            record_str = json.dumps(record)
        self.redis.set(inokey,record_str)


    # pyfilesystem required methods

    def getinfo(self, path, namespaces=None):
        target_inokey = self.pathwalk(path)
        if not target_inokey:
            raise fs.errors.ResourceNotFound(path)
        target_record = self.getrecord(target_inokey)
        if "info" in target_record:
            info_raw = target_record["info"]
            info = Info(info_raw)
            return info
        return fs.errors.ResourceNotFound(path)

    def listdir(self, path):
        directory_inokey = self.pathwalk(path)
        directory_record = self.getrecord(directory_inokey)
        if not "dir" in directory_record:
            return None
        directory_list = directory_record["dir"]
        if len(directory_list) == 0:
            return []

        entries = [ json.loads(self.redis.get(inokey))["info"]["basic"]["name"]
                    for inokey in directory_list ]
        return entries
    
    def makedir(self, path, permissions=None, recreate=False):
        # currently ignoring 'permissions' and 'recreate'
        return self.makeinode(path,is_dir=True)

    def makeinode(self, path, is_dir=False):
        existing_inokey = self.pathwalk(path)
        if existing_inokey:
            return existing_inokey

        _dirname, _basename = path_split(path)

        parent_inokey = self.pathwalk(_dirname)
        parent_record = self.getrecord(parent_inokey)
        if not parent_record:
            parent_record = dict()
        
        new_ino = self.getnextino()
        new_inokey = self.makeinokey(new_ino)
        new_record = {"info":{"basic":{"name":_basename,"is_dir":is_dir}},"linkcount":1}
        if is_dir:
            new_record["dir"] = []
       
        if "dir" not in parent_record:
            parent_record["dir"] = list()

        parent_record["dir"].append(new_inokey)
        self.setrecord(parent_inokey,parent_record)
        self.setrecord(new_inokey,new_record)
        
        return new_inokey
    
    def openbin(self, path, mode='r', buffering=-1, **options):
        # Not implemented.
        raise fs.errors.ResourceNotFound

    def remove(self, path):
        _dirname, _basename = path_split(path)
        parent_inokey = self.pathwalk(_dirname)
        target_inokey = self.lookup(parent_inokey,_basename)

        parent_record = self.getrecord(parent_inokey)
        if not "dir" in parent_record:
            return None
        directory_list = parent_record["dir"]
        directory_list.remove(target_inokey)
        
        target_record = self.getrecord(target_inokey)
        if "linkcount" in target_record:
            linkcount = target_record["linkcount"]
            linkcount = linkcount - 1
            if linkcount == 0:
                self.redis.delete(target_inokey)
            else:
                target_record["linkcount"] = linkcount
                self.setrecord(target_inokey,target_record)

        self.setrecord(parent_inokey,parent_record)
        return True

    def removedir(self, path):
        if path == "/" or path == "":
            raise fs.errors.RemoveRootError()

        directory_inokey = self.pathwalk(path)
        if not directory_inokey:
            raise fs.errors.ResourceNotFound()

        directory_record = self.getrecord(directory_inokey)

        if "dir" in directory_record:
            if len(directory_record["dir"]) > 0:
                raise fs.errors.DirectoryNotEmpty(path)

        if not directory_record["info"]["basic"]["is_dir"]:
            raise fs.errors.DirectoryExpected()

        return self.remove(path)

    def setinfo(self, path, info_raw):
        target_inokey = self.pathwalk(path)
        if not target_inokey:
            raise fs.errors.ResourceNotFound(path)

        target_record = self.getrecord(target_inokey)
        if not target_record:
            target_record = dict()

        target_record["info"] = info_raw
        self.setrecord(target_inokey,target_record)
