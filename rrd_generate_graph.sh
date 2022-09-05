rrdtool graph /home/pi/test.png -a PNG \
--end now \
--start end-3600s \
--width 800 \
--height 400 \
--right-axis 0.1:0 \
DEF:AGT=/media/USB/gasypi.rrd:AGT:AVERAGE \
DEF:O2=/media/USB/gasypi.rrd:O2:AVERAGE \
CDEF:O20=O2,10,* \
LINE1:AGT#0000FF:"AGT\l" \
LINE1:O20#00FF00:"O2\l"