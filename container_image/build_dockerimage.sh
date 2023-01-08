git clone git@github.com:element0/metafs
cp metafs/metafs.py .
cp metafs/metafs_proxy.py .
cp metafs/config-redis.sh .
docker build -t sandboxfs .
