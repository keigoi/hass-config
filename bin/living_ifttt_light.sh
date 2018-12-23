#!/bin/bash
. `dirname $0`/irkit_keys
curl -i https://maker.ifttt.com/trigger/$1/with/key/$IFTTT_KEY

