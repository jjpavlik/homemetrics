#!/bin/bash

function start {
  source bin/activate
  source credentials.conf
  exec python pusher.py -f 30
}

function stop {
  echo "Stopping pusher.py"
}

function status {
  echo "Checking status"
}

cd /opt/homemetrics

case "$1" in
  start)
      start
      ;;
  stop)
      stop
      ;;
  status)
      status
      ;;
  restart)
      stop
      start
      ;;
  *)
      echo "Usage: $0 {start|stop|restart|status}"
      exit 1
esac
