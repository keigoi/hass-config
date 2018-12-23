#!/bin/bash
cd `dirname $0`
./dining_light_on.sh &
./living_ifttt_light.sh home_standlight_on
./living_ifttt_light.sh home_bookshelflight_on
