#!/bin/sh
/home/semrep/public_mm/bin/skrmedpostctl start
/home/semrep/public_mm/bin/wsdserverctl start
python test.py
/home/semrep/public_mm/bin/skrmedpostctl stop 
/home/semrep/public_mm/bin/wsdserverctl stop
