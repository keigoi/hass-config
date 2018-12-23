#!/bin/bash
cd `dirname $0`
./dining_aircon_morning_heat.py &
./dining_light_off.sh &
./living_ifttt_light.sh home_standlight_off
