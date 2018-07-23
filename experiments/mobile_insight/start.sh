docker run -it --rm  --device=/dev/ttyUSB0 -v \
 `pwd`/monitor-all.py:/work/monitor-all.py:ro  -v \
 `pwd`/monitor-rrc-nas.py:/work/monitor-rrc-nas.py:ro -v `pwd`/mi-out/:/work \
 -w /work  aliparic/mi1  python monitor-rrc-nas.py /dev/ttyUSB0 9600 \

