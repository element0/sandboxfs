if (($# < 1))
then
    echo "Usage: $0 SOME_TARGET_FS_DIR"
else
    TARGETFSDIR="$1"
fi

if (($# > 1))
then
    MODE="-it"
    CMD="/bin/sh"
else
    MODE="-d"
    unset CMD
fi

TARGETFS_DIRNAME=$(dirname $TARGETFSDIR)
TARGETFS_BASENAME=$(basename $TARGETFSDIR)

if $(test $TARGETFS_DIRNAME == ".")
then
    TARGETFS_DIRNAME="$PWD"
fi
TARGETFSDIR=$TARGETFS_DIRNAME/$TARGETFS_BASENAME

echo $TARGETFSDIR

source "container_image/config-redis.sh"

# run as root
docker run "$MODE" --rm --mount type=bind,source="$TARGETFSDIR",target=/home/sandboxfs/target_fs --mount type=bind,source=/home/raygan/dev/sandboxfs/socket,target=/home/sandboxfs/socket --mount type=bind,source=/home/raygan/dev/sandboxfs/logs,target=/home/sandboxfs/logs --network "$REDIS_CONTAINER_NET" -e TARGETFSNAME="$TARGETFS_BASENAME" sandboxfs:latest $CMD

# docker run "$MODE" -u 1001:1001 --rm --mount type=bind,source=/home/raygan/dev/sandboxfs/"$TARGETFSDIR",target=/home/sandboxfs/target_fs --mount type=bind,source=/home/raygan/dev/sandboxfs/socket,target=/home/sandboxfs/socket -e TARGETFSNAME="$TARGETFSDIR" sandboxfs:latest $CMD
