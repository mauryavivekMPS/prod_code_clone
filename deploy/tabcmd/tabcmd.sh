#!/bin/bash
java -Xmx64m -Xss2048k -Djsse.enableSNIExtension=false -Dpid=$$ -Dlog.file=/var/log/tabcmd/tabcmd.log -Dsession.file=/var/log/tabcmd/tabcmd-session.xml -Din.progress.dir=/var/log/tabcmd -Dconsole.codepage=$LANG -Dconsole.cols=$COLUMNS -cp "$IVETL_ROOT/deploy/tabcmd/lib/*" -jar $IVETL_ROOT/deploy/tabcmd/lib/app-tabcmd-latest-jar.jar "$@"
