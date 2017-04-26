--------------
HA README
--------------


Purpose
--------------
The purpose of HA is to come true OSI SEVENTH LAYER high availablity between 
MasterInode and BackupInode in cluster that Keepalived (just OSI FOURTH) can
reach it. On other sides, Some problem often disturb us when we use Keepalived
on some old OS, such as Centos 6.X above, we can't special multicast ipaddr
for the special group of keepalived_inodes. etc..


Cautions
---------------
1) HA only can be running on Linux OS at current, if your OS envrionment was
   Windows OS, you must modify its interactive(builtin os) commands  first.
2) HA was programmed by python Version 2.7.2 and tested on 2.4.3 and 2.7.2 ok,
   if your python Version is above 3.x.x, maybe need to modify some functions.
3) Do not modify the sections ([...]) of the config or the config filename
4) Due to HA bases on TCP protocol, so when BackupInode recovered from Host
   down, please restart MasterInode HA process to keep connecting to BackInode.
5) DownStream Inodes means that need to establish with the tcp server which 
   bind on virual ipaddr, this config section is effience in Lan network_env,
   if clients and servers in Wlan network_env, just set "DnStr" value null.
6) If you find MasterInode can't connect to BackupInode in logfile with error
   111, Please check BackupInode's iptables rules and selinux status.
7) HA support multi_instance on single inodesvr, But you'd better copy other 
   folder of HA and keep configurations(special for AppName, port, log, NetInt)
   unique in groups of inodesvr.
8) If occurred some wried problems when excute Ha, you maybe need use dos2unix 
   (Linux) or unix2dos(Windows) to transfer the linebreak 

FILE INSTUCTIONS
----------------
Ha ----> excute program
Ha.conf ----> configure file
Ha.conf.sample -----> sample file


AppScene
----------------
Groups of MiddleWare (mostly scene), Web, Database or Monitor server.


Usage
----------------
Usage:python Ha {start|stop|status|restart|--help}


Author and Maintance
----------------
Jessica: eastmoney@shimin.com, welcome to give me some nice advices from email.
