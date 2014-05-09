#!/bin/bash
dir="/usr/local/mrtg/manage"
if pgrep perl-fcgi.pl;then
    echo "perl-fcgi ok"
else
    rm /usr/local/nginx/run/perl-fcgi.pid -f
    $dir/manager.sh start
fi

