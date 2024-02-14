#!/bin/bash
date >~/data/broute.tmp
#echo  "<br>" >>~/data/km50c.tmp
~/test/bp35a1-E3.py >>~/data/broute.tmp
if [ $(wc -l < ~/data/broute.tmp) -eq "2" ]; then
   cp ~/data/broute.tmp ~/data/broute.txt
fi
   scp ~/data/broute.txt  mrtg@xxx.jp:~/pi/hrhome/data
