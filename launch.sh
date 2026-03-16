#~/bin/bash

echo starting

source ~/Documents/pyforpi2/myenv/bin/activate
python3 ~/Documents/pyforpi2/app2.py &
sleep 2

chromium --kiosk http://127.0.0.1:5000
wait
echo closed
