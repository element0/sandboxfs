pip3 install -r target_fs/requirements.txt
addgroup -g 1001 target_fs
adduser -u 1001 -G target_fs -D target_fs
su -c "python3 socketfs_server.py" target_fs
