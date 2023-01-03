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

docker run "$MODE" -u 1001:1001 --rm --mount type=bind,source=/home/raygan/dev/sandboxfs/"$TARGETFSDIR",target=/home/sandboxfs/target_fs --mount type=bind,source=/home/raygan/dev/sandboxfs/socket,target=/home/sandboxfs/socket -e TARGETFSNAME="$TARGETFSDIR" sandboxfs:latest $CMD
