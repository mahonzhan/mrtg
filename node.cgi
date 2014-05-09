#!/usr/bin/perl
#######################################
# Xunlei MRTG Index Generator     
#######################################
#
# 2014/4/26  create it
# 2014/5/5   improve performance
# 2014/5/8   modify host sort 
#######################################

# use strict;
use FCGI;
use Config::Grammar;
use lib "/usr/lib64/mrtg2/";
use MRTG_lib "2.100016";

my $parser = Config::Grammar->new({
  _sections => ['/\S+/'],
  '/\S+/' => {
    _sections => ['/\S+/'],
    '/\S+/' => {
      _doc => "idc node name",
      _example => "t01",
      _vars => ['location'],
      _sections => ['/\S+/'],
      '/\S+/' => {
        _doc => "net type, wan or lan?",
        _example => "wan",
        _sections => ['/\S+/'],
        '/\S+/' => {
          _table => {
            _doc => "interface",
            _example => "t01sw01",
          }   
        }   
      }   
    }
  }
}); 

my $cfg;
my $index;

sub write_index_html() {
  $index .= <<ECHO;
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<HTML> 
<HEAD> 
  <TITLE>Server Traffic Monitor</TITLE> 
  <META HTTP-EQUIV="CONTENT-TYPE" CONTENT="TEXT/HTML; CHARSET=UTF-8" >
  <META HTTP-EQUIV="Refresh" CONTENT="300"> 
  <META HTTP-EQUIV="Cache-Control" content="no-cache"> 
  <META HTTP-EQUIV="Pragma" CONTENT="no-cache"> 
  <META HTTP-EQUIV="Expires" CONTENT="Wed, 23 Apr 2014 14:48:19 GMT" >

  <style type="text/css">
    h1 { text-align:center }
    body {
      font-family: "Segoe UI Semibold", "Microsoft YaHei UI", Verdana,"Helvetica Neue", Helvetica, Arial, sans-serif;
      font-size: 10pt
    }
    th {
      font-family: Verdana;
      font-weight:bold;
    }
  </style>
</HEAD> 
 
<BODY bgcolor="#ffffff" text="#000000" link="#000000" vlink="#000000" alink="#000000"> 
<H1 align="center"> MRTG of switches</H1> 
<TABLE width="1024" border="1" align="center" cellspacing="1" bordercolor="#666666" bgcolor="#FFFFFF">
ECHO
  my %line = %{$cfg};

  # list idc nodes
  foreach my $line (sort keys %line) {
    my %node = %{$cfg->{$line}};
    my $counter;
    $index .= <<ECHO;
<TR><TD width="1032" valign="bottom"><TABLE border="1" cellspacing="0" bordercolor="#FFFFFF" bgcolor="#CCCCCC">
<TR><TH><a href="#$line">$line</a></TH>
ECHO
    foreach my $node (sort keys %node) {
      my $NODE = uc($node);
      $index .= "<TD WIDTH=56><DIV><A HREF=node.cgi?node=$node>$NODE</A></DIV></TD>\n";
      $counter++;
      $index .= <<ECHO if $counter % 25 == 0;
</TR><TH></TH>
ECHO
    }
    $index .= "</TR></TABLE></TD></TR>\n";
  }
  $index .= <<STATIC;
<TR><TD><TABLE border="1" cellspacing="0" bordercolor="#FFFFFF" bgcolor="#CCCCCC">
<TR><TH>STATIC</TH>
<TD WIDTH=56><A HREF=office.html>OFFICE</A></TD>
<TD WIDTH=56><A HREF=game.html>game</A></TD>
<TD WIDTH=56><A HREF=hub.html>hub</A></TD>
<TD WIDTH=56><A HREF=cc>cc</A></TD>
<TD WIDTH=56><A HREF=lixiancdn.html>lixian+vipcdn</A></TD>
<TD WIDTH=56><A HREF=http://t07001.sandai.net:8081/smokeping/>Smokeping</A></TD>
<TD WIDTH=56><A HREF=http://t07001.sandai.net:8080/check_speed>IDC Speed</A></TD>
<TD WIDTH=56><A HREF=allflow.html>all flow</A></TD>
<TD WIDTH=56><A HREF=http://t07001.sandai.net:8081/mrtg/>index history</A></TD>
</TR></TABLE></TD></TR>
STATIC
  $index .= "</TABLE><BR/>\n";

  # list switches
  $index .= "<TABLE border=1 cellpadding=1 cellspacing=1 bgcolor=#FFFFFF align=center>\n";
  foreach my $line (sort keys %line) {
    my $column = 0;
    my %node = %{$cfg->{$line}};
    $index .= <<ECHO;
<table border=1 cellpadding=1 cellspacing=1 bgcolor="#FFFFFF" align="center"><tr><td colspan="2" bgcolor="#FFCC00"><a name="$line">$line</a></td>
</tr>
ECHO
    foreach my $node (sort keys %node) {
      my %switches = %{$cfg->{$line}{$node}{'wan'}};
      my $location = $cfg->{$line}{$node}{'location'};
      foreach my $switch (keys %switches) {
        @interfaces = @{$cfg->{$line}{$node}{'wan'}{$switch}{'_table'}};
        foreach (@interfaces) {
          $int = $_->[0];
          $post = $_->[1];
          $spec = $switch."_".$int;
          $index .= "<tr bgcolor=#999999>" if ($column % 2 == 0);
          $index .= <<ECHO;
<td><DIV><B>$node $location $switch $int $post</B></DIV>
<DIV><A HREF="$switch/$spec.html"><IMG BORDER=1 ALT="$spec Traffic Graph" SRC="$switch/$spec-day.png"></A><br>
<SMALL></SMALL></DIV>
</td>
ECHO
          $column++;
          $index .= "</tr>" if ($column % 2 == 0);
        }
      }
    }
    $index .= "</TABLE>";
  }
  $index .= <<ECHO;
</TABLE>
</BODY>
</HTML>
ECHO
  return $index;
}


sub write_idc_html($) {
  my $node = shift;
  my $NODE = uc($node);
  my %line = %{$cfg};
  my $net;
  foreach my $line (sort keys %line) {
    my %conf_node = %{$cfg->{$line}};
    if(exists $conf_node{$node}) {
        $net = $line;
        last;
    }
  }
  my $location = $cfg->{$net}{$node}{'location'} or
    return "<h1>ERROR: idc node does not exist</h1>\n";
  
  $index = <<ECHO;
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<HTML>
<HEAD>
  <TITLE>MRTG of Servers in $NODE</TITLE>
  <META HTTP-EQUIV="CONTENT-TYPE" CONTENT="TEXT/HTML; CHARSET=UTF-8" >
  <META NAME="Command-Line" CONTENT="&lt;suppressed&gt;" >
  <META HTTP-EQUIV="Refresh" CONTENT="300" >
  <META HTTP-EQUIV="Cache-Control" content="no-cache" >
  <META HTTP-EQUIV="Pragma" CONTENT="no-cache" >
  <META HTTP-EQUIV="Expires" CONTENT="Wed, 23 Apr 2014 14:48:19 GMT" >
  
  <style type="text/css">
    h1 { text-align:center }
    tr { background-color: #999999 }
    body {
      font-family: "Segoe UI Semibold", "Microsoft YaHei UI", Verdana,"Helvetica Neue", Helvetica, Arial, sans-serif;
      font-size: 10pt
    }
  </style>
</HEAD>

<BODY bgcolor="#ffffff" text="#000000" link="#000000" vlink="#000000" alink="#000000">

<H1>MRTG of Servers in $NODE</H1>
<h4 align="left">
<a href="node.cgi" target="_blank">[home]</a>&nbsp;&nbsp;
ECHO
  
  # write switch brief info
  foreach my $d (qw(wan lan)) {
    $index .= <<ECHO;
  <h4 align="left">
  <td width="24"><strong>$d:</strong></td>
ECHO
    my %switches = %{$cfg->{$net}{$node}{$d}};
    foreach my $switch (keys %switches) {
      $index .= <<ECHO;
  <a href="/mrtg/$switch" target="_blank">[$switch]</a>&nbsp;
ECHO
    }
    $index .= "</h4>";
  }
  
  # write idc brief info
  $index .= <<ECHO;
  <TABLE BORDER=1 CELLPADDING=0 CELLSPACING=1>
  <tr bgcolor="#FFFFCC">
  <td bordercolor="#A2A2A2" bgcolor="#FFFFCC" colspan="3" align="center">$NODE $location</td>
  </tr>
ECHO
  
  # write wan switch html
  my $column = 0;
  my %switches = %{$cfg->{$net}{$node}{'wan'}};
  foreach my $switch (keys %switches) {
    @interfaces = @{$cfg->{$net}{$node}{'wan'}{$switch}{'_table'}};
    foreach (@interfaces) {
      $int = $_->[0];
      $post = $_->[1];
      $spec = $switch."_".$int;
      $index .= "<tr>" if ($column % 3 == 0);
      $index .= <<ECHO;
  <td><DIV><B>$switch $int $post</B></DIV>
  <DIV><A HREF="$switch/$spec.html"><IMG BORDER=1 ALT="$spec Traffic Graph" SRC="$switch/$spec-day.png"></A><br>
  <SMALL></SMALL></DIV>
  </td>
ECHO
      $column++;
      $index .= "</tr>" if ($column % 3 == 0);
    }
  }
  
  # write host html
  my %rcfg;
  my %cfg;
  my @target;
  my @routers;
  my %files;
  my @cfgfile = glob "/usr/local/mrtg/host/$node*/mrtg*.conf
                      /usr/local/mrtg/cnchost/$node*/mrtg*.conf
                      /usr/local/mrtg/otherhost/$node*/mrtg*.conf";
  foreach $cfgfile (@cfgfile) {
    next if not ($cfgfile =~ m/$node\d+/);
    readcfg($cfgfile,\@routers,\%cfg,\%rcfg);
      #return "<h1>mrtg cfg read error</h1>\n";
    for my $targ (@routers) {
      if ( !defined $rcfg{host}{$targ} and
           !($rcfg{target}{$targ} =~ m/(?<!\\)[ \`]/) ) {
        $rcfg{target}{$targ} =~ m/.*[^\\]@([^:]*)/;
        $rcfg{host}{$targ} = $1 if (defined $1);
      }
    }
    # much overhead
    #cfgcheck(\@routers, \%cfg, \%rcfg, \@target);
    #$rcfg{prefixes} = {} if (!defined $rcfg{prefixes});
    #my $pref = subpath($cfg{htmldir},"/usr/local/mrtg/htdocs/$node.html");
    #for my $targ (@routers) {
    #  $rcfg{prefixes}->{$targ} = $pref
    #    if (! defined $rcfg{prefixes}->{$targ});
    #}

  }
  for my $targ (@routers) {
    @part = split(/\./, $targ);
    $pref = $part[0]."/";
    $rcfg{prefixes}->{$targ} = $pref
      if (! defined $rcfg{prefixes}->{$targ});
  }
  my @filtered;
  foreach my $item (@routers) {
    my $regex = "eth|em|vmnic|www_cpu|bond|_\\d+";
    push @filtered, $item if $item =~ /$regex/;
  };
  my @order = 
    sort {
      $a =~ m[$node(\d+)];
      my $aval = $1;
      $b =~ m[$node(\d+)];
      my $bval = $1;
      $aval <=> $bval;
    } @filtered;
  my $hostcolumn = 0;
  my $first = $order[0];
  my $host = $rcfg{host}{$first};
  foreach my $item (@order) {
    my $newhost = $rcfg{host}{$item} || 'unspecified host';
    if (!($host eq $newhost)) {
      $index .= "</tr>\n";
      $host = $newhost;
      $hostcolumn = 0;
    }
    my $prefix = $rcfg{prefixes}->{$item};
    my $section;
    if ($rcfg{pagetop}{$item} =~ m[<h1[^>+]*>(.+?)</h1]i) {
      $section = $1;
    } else {
      return "<h1>ERROR: no H1 line pagetop property in $item section</h1>\n";
    }
    $index .= "<tr>\n" if ($hostcolumn == 0);
    $index .= "<td>";
    $index .= "<DIV><B>$section</B></DIV>\n";
    $index .= "<DIV><A HREF=\"".$prefix.$item.".html\">";
    $index .= "<IMG BORDER=1 ALT=\"$item Traffic Graph\" "."SRC=\"".$prefix.$item."-day.png\">";
    $index .= "</A>";
    $index .= "<BR>";
    $index .= "<SMALL></SMALL></DIV>";
    $index .= "\n</td>";
    $hostcolumn++;
  }
  
  # write html tail
  $index .= <<ECHO;
  </TABLE>
  
  </BODY>
  </HTML>
ECHO
  return $index;
}


# Response loop
while (FCGI::accept >= 0) {
  print "Content-type: text/html\r\n\r\n";
  my $qs = $ENV{'QUERY_STRING'};
  my %in;
  $cfg = $parser->parse('/usr/local/mrtg/conf/idc.conf') or
    return "<h1>ERROR: $parser->{err}</h1>\n";
  if (length($qs) > 0) {
    my @pairs = split(/&/, $qs);
    foreach my $pair (@pairs) {
      ($name, $value) = split(/=/, $pair);
      $value =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C", hex($1))/eg;
      $in{$name} = $value;
    }
    if ($in{'node'} && scalar @pairs == 1) {
      print &write_idc_html($in{'node'});
    } else {
      print "param error";
    }
  } else {
    print &write_index_html();
  }
}
