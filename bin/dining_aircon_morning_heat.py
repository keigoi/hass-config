#!/usr/bin/env python
import sys
import os
import datetime
import requests
import timer_heat_payload

dirname = os.path.dirname(os.path.realpath(__file__))
with open(dirname + '/irkit_keys') as f:
    IRKIT = {k:v.strip() for k,v in [line.partition('=')[::2] for line in f]}

def send(hour):
    payload = timer_heat_payload.payload[hour-1]
    params = {'clientkey': IRKIT['IRKIT_CLIENT_KEY'],
              'deviceid': IRKIT['IRKIT_DEVICE_ID'],
              'message': payload}
    r = requests.post('https://api.getirkit.com/1/messages', data=params)
    r.raise_for_status()

def hours_to_4_oclock():
    now = datetime.datetime.now()
    hour = now.hour
    if 4 <= hour and hour <= 17:
        return None
    return (4 - now.hour) % 12

def main():
    if len(sys.argv) < 2:
        hour  = hours_to_4_oclock()
        if hour is None:
            print('do not set wakeup-heating timer during daytime')
            return
        else:
            send(hour)
    else:
        hour = sys.argv[1]
        hour = int(hour)
        send(hour)

    print('set wakeup-heating timer after %d hours' % hour)


if __name__ == '__main__':
    main()
