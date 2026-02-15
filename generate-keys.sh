#!/bin/sh
cd /keys
/usr/bin/avbroot key generate-key -o avb.key
/usr/bin/avbroot key generate-key -o ota.key
/usr/bin/avbroot key encode-avb -k avb.key -o avb_pkmd.bin
/usr/bin/avbroot key generate-cert -k ota.key -o ota.crt
