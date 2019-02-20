#!/bin/bash

function start {
  source /opt/homemetrics/bin/activate
  exec python collector.py --openweather
}

function stop {

}

function status {

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
