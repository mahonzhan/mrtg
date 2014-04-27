#!/bin/bash
dir="/usr/local/nginx"

function stop() {
  if [ -f $dir/run/perl-fcgi.pid ];then
    kill $(cat $dir/run/perl-fcgi.pid)
    rm $dir/run/perl-fcgi.pid -f
  else
    echo "perl fcgi pid file not exist"
    return 1
  fi
  rm $dir/run/perl-fcgi.sock -f
  echo "perl fcgi stopped."
}

function start() {
  sudo -u nobody /usr/local/mrtg/fcgi-bin/perl-fcgi.pl \
    -l $dir/logs/perl-fcgi.log \
    -pid $dir/run/perl-fcgi.pid \
    -S $dir/run/perl-fcgi.sock
  [ $? -eq 0 ] && echo "perl fcgi have started."
}

case $1 in
  stop)
  stop;;
  start)
  start;;
esac
