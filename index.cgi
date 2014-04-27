#!/usr/bin/perl
#######################################
# Xunlei MRTG Index Generator     
#######################################
#
# Need to read host config, 
# so cannt do with no-config host
#
#######################################
# 2014/4/26  mahongzhan@xunlei.com
#######################################

# use strict;
use FCGI;
use Config::Grammar;
use lib "/usr/lib64/mrtg2/";
use MRTG_lib "2.100016";

BEGIN {
  # Automatic OS detection ... do NOT touch
  if ( $^O =~ /^(?:(ms)?(dos|win(32|nt)?))/i ) { 
    $main::OS = 'NT';
    $main::SL = '\\';
    $main::PS = ';';
  } elsif ( $^O =~ /^NetWare$/i ) { 
    $main::OS = 'NW';
    $main::SL = '/';
    $main::PS = ';';
  } elsif ( $^O =~ /^VMS$/i ) { 
    $main::OS = 'VMS';
    $main::SL = '.';
    $main::PS = ':';
  } else {
    $main::OS = 'UNIX';
    $main::SL = '/';
    $main::PS = ':';
  }   
}

my $parser = Config::Grammar->new({
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
}); 

my $cfg;
my $index;

sub write_index_html() {
  $index .= <<ECHO;
<HTML> 
<HEAD> 
<TITLE>Server Traffic Monitor</TITLE> 
  <META HTTP-EQUIV="Refresh" CONTENT="300"> 
  <META HTTP-EQUIV="Cache-Control" content="no-cache"> 
  <META HTTP-EQUIV="Pragma" CONTENT="no-cache"> 
  <META HTTP-EQUIV="Expires" CONTENT="Sat, 07 Aug 2004 05:45:24 GMT"> 
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8"> 
  <style type="text/css">
    body {
      font-family: "Segoe UI Semibold", "Microsoft YaHei UI", Verdana,"Helvetica Neue", Helvetica, Arial, sans-serif;
      font-size: 10pt
    }
  </style>
</HEAD> 
 
<BODY bgcolor="#ffffff" text="#000000" link="#000000" vlink="#000000" alink="#000000"> 
<H1 align="center"> MRTG of switches</H1> 
<TABLE width="1024" border="1" align="center" cellspacing="1" bordercolor="#666666" bgcolor="#FFFFFF"> 
<TR><TD width="1032" valign="bottom"><TABLE WIDTH="100%" BORDER="1" CELLSPACING="0" BORDERCOLOR="#FFFFFF" BGCOLOR="#CCCCCC"><TR>
ECHO
  my %node = %{$cfg};
  my $counter;
  foreach my $node (sort keys %node) {
    $index .= "<TD WIDTH=56><A HREF=index.cgi?node=$node>$node</A></TD>\n";
    $counter++;
    $index .= <<ECHO if $counter % 30 == 0;
</TR></TABLE></TD></TR>
<TR><TD width="1032" valign="bottom"><TABLE WIDTH="100%" BORDER="1" CELLSPACING="0" BORDERCOLOR="#FFFFFF" BGCOLOR="#CCCCCC"><TR>
ECHO
  }
  $index .= "</TR></TABLE></TD></TR>\n" if $counter % 30 != 0;
  $index .= "<TABLE border=1 cellpadding=1 cellspacing=1 bgcolor=#FFFFFF align=center>\n";
  $index .= "<br/>\n";
  my $column = 0;
  foreach my $node (sort keys %node) {
    my %switches = %{$cfg->{$node}{'wan'}};
    my $location = $cfg->{$node}{'location'};
    foreach my $switch (keys %switches) {
      @interfaces = @{$cfg->{$node}{'wan'}{$switch}{'_table'}};
      foreach (@interfaces) {
        $int = $_->[0];
        $spec = $switch."_".$int;
        $index .= "<tr bgcolor=#999999>" if ($column % 2 == 0);
        $index .= <<ECHO;
<td><DIV><B>$node $location $switch $int</B></DIV>
<DIV><A HREF="$switch/$spec.html"><IMG BORDER=1 ALT="$spec Traffic Graph" SRC="$switch/$spec-day.png"></A><br>
<SMALL></SMALL></DIV>
</td>
ECHO
        $column++;
        $index .= "</tr>" if ($column % 2 == 0);
      }
    }
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
  my $location = $cfg->{$node}{'location'} or
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
<a href="index.cgi" target="_blank">[home]</a>&nbsp;&nbsp;
ECHO
  
  # write switch brief info
  foreach my $d (qw(wan lan)) {
    $index .= <<ECHO;
  <h4 align="left">
  <td width="24"><strong>$d:</strong></td>
ECHO
    my %switches = %{$cfg->{$node}{$d}};
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
  <td bordercolor="#A2A2A2" bgcolor="#FFFFCC" colspan="3" align="center"><span class="style3">$NODE $location</td>
  </tr>
ECHO
  
  # write wan switch html
  my $column = 0;
  my %switches = %{$cfg->{$node}{'wan'}};
  foreach my $switch (keys %switches) {
    @interfaces = @{$cfg->{$node}{'wan'}{$switch}{'_table'}};
    foreach (@interfaces) {
      $int = $_->[0];
      $spec = $switch."_".$int;
      $index .= "<tr>" if ($column % 3 == 0);
      $index .= <<ECHO;
  <td><DIV><B>$switch $int</B></DIV>
  <DIV><A HREF="$switch/$spec.html"><IMG BORDER=1 ALT="$spec Traffic Graph" SRC="$switch/$spec-day.png"></A><br>
  <SMALL></SMALL></DIV>
  </td>
ECHO
      $column++;
      $index .= "</tr>" if ($column % 3 == 0);
    }
  }
  
  # write host html
  sub subpath ($$) {
    my $sub = shift;
    my $out = shift;
    my @s=split /$main::SL/,$sub;
    my @o=split /$main::SL/,$out;
    pop @o;  #Last is a filename;
    for my $i (0..$#s) {    #cut common dirs
      if (defined $s[0] and
          defined $o[0] and
          $s[0] eq $o[0] ) {
            shift @s;
            shift @o;
      }
    }
    my $ret = join $main::SL,@s;
    for my $i (0..$#o) {
      $ret = "..$main::SL$ret";
    }
    $ret .= $main::SL;
    $ret = "" if ($ret eq $main::SL);
    return $ret;
  }
  my %rcfg;
  my %cfg;
  my @target;
  my @routers;
  my %files;
  my @cfgfile = glob "/usr/local/mrtg/host/$node*/mrtg*.conf /usr/local/mrtg/cnchost/$node*/mrtg*.conf";
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
    cfgcheck(\@routers, \%cfg, \%rcfg, \@target);
    $rcfg{prefixes} = {} if (!defined $rcfg{prefixes});
    my $pref = subpath($cfg{htmldir},"/usr/local/mrtg/htdocs/$node.html");
    for my $targ (@routers) {
      $rcfg{prefixes}->{$targ} = $pref
        if (! defined $rcfg{prefixes}->{$targ});
    }
  }
  my @filtered;
  foreach my $item (@routers) {
    my $regex = "eth|em|vmnic|www_cpu|655|bond";
    push @filtered, $item if $item =~ /$regex/;
  };
  my @order = @filtered;
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
