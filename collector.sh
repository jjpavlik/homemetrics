#!/bin/bash

function start {
  source bin/activate
  source credentials.conf
  if [ -e debug ]; then
    exec python collector.py --openweather --debug
  else
    exec python collector.py --openweather    
  fi
}

function stop {
  echo "Stopping collector.py"
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
