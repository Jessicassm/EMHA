#-*- coding:utf-8 -*-
'''
Created on 2017-02-07
Function:HIGH AVAILIABLITY OSI's SEVEN LAYER
@author: EASTMONEY-Jessica
'''

import os,socket,select,time,sys,re,string
from ConfigParser import ConfigParser  
from __builtin__ import False

class BaseHandle(object):
    BaseName = sys.argv[0]
    TimeFmt = '%Y-%m-%d %H:%M:%S'
    NowTime = time.strftime(TimeFmt)
    sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        
    def __init__(self,status,AppName,vip,Mip,Bip,port,LogPath,LogName,NetInt,DnStr):
        self.status = status
        self.AppName = AppName
        self.vip = vip
        self.Mip = Mip
        self.Bip = Bip
        self.port = port
        self.LogPath = LogPath
        self.LogName = LogName
        self.NetInt = NetInt
        self.DnStr = DnStr
        
        #Excute HA_object process initial
        self.InitHA()
        
    @staticmethod
    def ConfKernel(value=1):
        '''
        if function argv "value" is 0 means close ReqIpBind,
        or "value" is 1 means open ReqIpBind,default value is 1
        '''
        KernelConfPath = '/etc/sysctl.conf'
        ReqIpBindConf = 'net.ipv4.ip_nonlocal_bind = %s\n' % value
        KernelFile = open(KernelConfPath,'a+r+b')
        KernelFileCont = KernelFile.readlines()
        if ReqIpBindConf not in KernelFileCont:
            KernelFile.write(ReqIpBindConf)
            KernelFile.close()
            LoadkernelCmd = 'sysctl -p > /dev/null 2>&1'
            os.system(LoadkernelCmd)      
                   
    @staticmethod
    def CheckUser(SpUid=0):
        ChkUserCmd = 'echo $UID'
        CurUserUid = os.popen(ChkUserCmd).read()
        if int(CurUserUid) != SpUid:
            print '%s User_env\033[31;1m must be root/admin\033[0m CurrentUid is %s.' \
            % (sys.argv[0],CurUserUid)
            sys.exit(110)
        else:pass
            
    def CheckProc(self):
        ChkProcPidCmd = "pidof %s" % self.AppName
        ProcPidRes = os.popen(ChkProcPidCmd).read()
        PidPat = re.compile('[0-9]+')
        if re.match(PidPat,ProcPidRes):
            return ProcPidRes
        else:
            print "Caution :%s isn't running." % self.AppName 
            return []
    
    def StartUpTcp(self):
        self.ProcPid()
        if self.status == 'Backup':
            self.ManagerVip('DownVip')
            BaseHandle.sock.bind((self.Bip,self.port))
            BaseHandle.sock.listen(5)
            inputs = [BaseHandle.sock]
            while True:
                rs,ws,es = select.select(inputs,[],[])
                log = open('%s%s_Backup.log' %(self.LogPath,self.LogName),'a+b+r')
                for r in rs:
                    if r is BaseHandle.sock:
                        c,addr = BaseHandle.sock.accept()
                        #print 'Established connection with ',addr
                        inputs.append(c)
                    else:
                        try:
                            RecvHeartData = r.recv(1024)
                            disconnected = not RecvHeartData
                        except socket.error:
                            disconnected = True
                        else:
                            log.write('%s Connnected to %s\n' % (BaseHandle.NowTime,addr))
                                                    
                        if disconnected and addr[0] == self.Mip :
                            #print r.getpeername(),'disconnected'
                            log.write('%s Disconnected to %s\n' \
                                      % (BaseHandle.NowTime,r.getpeername()))
                            inputs.remove(r)
                            self.ManagerVip('StartVip')
                            log.write('%s Rec MasterInode host had Down' \
                                          % (BaseHandle.NowTime))
                        else:
                            if 'failed' in RecvHeartData:
                                self.ManagerVip('StartVip')
                                log.write('%s Rec MasterInode process had Down' \
                                          % (BaseHandle.NowTime))
                                if not self.CheckProc():
                                    log.write('%s Critical Warnning:%s process is not \
                                    running\n' % (BaseHandle.NowTime,self.AppName))
                            elif 'ok' in RecvHeartData:
                                self.ManagerVip('DownVip')
                                log.write('%s Rec MasterInode process had recovered\n' \
                                          % (BaseHandle.NowTime))
                            else:
                                log.write('%s Rec Error data :%s\n' \
                                          % (BaseHandle.NowTime,RecvHeartData))
                                time.sleep(0.5)
                log.close()
                    
        elif self.status == 'Master':
            self.ManagerVip('StartVip')
            Flag = True
            while True:
                while Flag:
                    log = open('%s%s_Master.log' %(self.LogPath,self.LogName),'a+b+r')
                    try:
                        BaseHandle.sock.connect((self.Bip,self.port))
                    except socket.error,error1:
                        log.write("%s can't connected to Backup %s\n" \
                                  % (BaseHandle.NowTime,error1))
                        log.close()
                        time.sleep(0.5)
                    else:
                        Flag = False
                        if 'ok' in self.HeartData():
                            BaseHandle.sock.send(self.HeartData())
                        
                if 'failed' in self.HeartData():
                    log = open('%s%s_Master.log' %(self.LogPath,self.LogName),'a+b+r')
                    self.ManagerVip('DownVip')
                    try:
                        BaseHandle.sock.send(self.HeartData())
                    except socket.error,error2:
                        log.write("%s can't connected to Backup %s\n" \
                                  % (BaseHandle.NowTime,error2))
                        log.close()
                        Jump = False
                        Flag = True
                    else:
                        Jump = True
                else:
                    '''
                    If you want Keep HA between InodeSvr without restart MasterInodeSvr
                    when BackUpInodeSvr recovered from down , you can cancel annotation
                    above , but this behavior will be not friendly to BackupInodeSvr.
                    '''
                    # try:
                    #     BaseHandle.sock.send(self.HeartData())
                    # except socket.error,error111:
                    #     Flag = True
                    Jump = False
                time.sleep(0.5) 
                while Jump:
                    log = open('%s%s_Master.log' %(self.LogPath,self.LogName),'a+b+r')
                    if 'ok' in self.HeartData():
                        try:
                            BaseHandle.sock.send(self.HeartData())
                        except socket.error,error3:
                            log.write("%s can't connected to Backup %s\n" \
                                      % (BaseHandle.NowTime,error3))
                            log.close()
                            Jump = False
                            Flag = True
                        else:
                            self.ManagerVip('StartVip')
                            Jump = False
                    time.sleep(0.5)                  
        else:
            print "The values of 'status' configed error in Ha.conf, Please check it."
            sys.exit(112)
        
    def HeartData(self):
        if not self.CheckProc():
            HeartData = ' %s %s status is failed' \
            % (time.strftime(BaseHandle.TimeFmt),self.AppName)
        else:
            HeartData = ' %s %s status is ok' \
            % (time.strftime(BaseHandle.TimeFmt),self.AppName)
        return HeartData     
    
    def ManagerVip(self,action):
        NetInfo = os.popen('ifconfig').read()
        VipPat = re.compile(self.vip)
        if action == 'StartVip':
            if not re.search(VipPat,NetInfo):
                os.system('/sbin/ifconfig %s %s up' % (self.NetInt,self.vip))  
            else:
                print sys.argv[0] + ' Checking vip :%s is running.' % self.vip 
            self.ClnArpCache()
        if action == 'DownVip':
            if re.search(VipPat,NetInfo): 
                os.system('/sbin/ifconfig %s %s down' % (self.NetInt,self.vip)) 
            else:
                pass
                #print sys.argv[0] + ' Checking vip :%s had been down' % self.vip
             
    #Inform UpstreamInode or DownstreamInode update ArpCache
    def ClnArpCache(self):
        DnStrList = self.DnStr.split(';')
        for DnStr in DnStrList:
            ArpCmd = 'arping -w 3 -c 2 -I %s -s %s -U %s > /dev/null 2>&1' \
            % (self.NetInt,self.vip,DnStr)
            os.system(ArpCmd)
            
    def HA_ProcMan(self,KeyWord='*'):
        try:
            PidFile = open(r'/var/run/Ha_%s.pid' % self.AppName,'r+b') 
        except IOError,error113:
            print "/var/run/Ha_%s.pid doesn't exist,Please start %s first (%s) " \
            % (self.AppName,BaseHandle.BaseName,error113)
        else:
            Pid = PidFile.readline()
            SelfKillCmd = 'kill -9 %s > /dev/null 2>&1' % Pid
            if not Pid:
                print '%s is not running ' % BaseHandle.BaseName
            else:
                if string.lower(KeyWord) == 'stop':
                    self.ManagerVip('DownVip')
                    PidFile = open(r'/var/run/Ha._%s' % self.AppName,'w+b')
                    os.system(SelfKillCmd)
                else:
                    print '%s is running. pid:%s' % (BaseHandle.BaseName,Pid)
            PidFile.close()        
            
    def ProcPid(self):
        HaProcPid = os.getpid()
        PidFile = open(r'/var/run/Ha_%s.pid' % self.AppName,'w+b')
        PidFile.write(str(HaProcPid))
        PidFile.close()
        
    def InitHA(self):
        self.CheckUser()
        self.ConfKernel(value=1)
        if not os.path.isdir(self.LogPath):
            os.makedirs(self.LogPath)
            
    @classmethod            
    def ArgvUage(cls):
        return 'Usage:python %s {start|stop|status|restart|--help}' \
            % BaseHandle.BaseName
    
#Initial ConfigFile      
InitConfig = ConfigParser()
InitConfig.read('Ha.conf')
status = InitConfig.get('InodeSvr role in Cluster <Master | Backup>','status')
AppName = InitConfig.get('High availablity object ProcessName','AppName')
vip = InitConfig.get('Virual ip address for HA','vip')  
Mip = InitConfig.get('Master InnodeSvr physical Ip Address','Mip')
Bip = InitConfig.get('Backup InnodeSvr physical Ip Address','Bip')
port = int(InitConfig.get('HA Listenning Port <must be Int_Type>','port'))
LogPath = InitConfig.get("HA LogFile's absolute path",'LogPath')
LogName = InitConfig.get("HA LogFile's name",'LogName')
NetInt = InitConfig.get("NetworkInterface's name which binds vip",'NetInt')
DnStr = InitConfig.get('DownStream InodeSvr Ip Address','DnStr')

#print [status,AppName,vip,Mip,Bip,port,LogPath,LogName,NetInt,DnStr]
def Index():
    if __name__ == '__main__':
        VssIdcStock = BaseHandle(
            status,AppName,vip,Mip,Bip,port,LogPath,LogName,NetInt,DnStr
            )
        if string.lower(sys.argv[1]) == 'start':
            VssIdcStock.StartUpTcp()
        elif string.lower(sys.argv[1]) == 'stop':
            VssIdcStock.HA_ProcMan('stop')
        elif string.lower(sys.argv[1]) == 'status':
            VssIdcStock.HA_ProcMan()
        elif string.lower(sys.argv[1]) == 'restart':
            VssIdcStock.HA_ProcMan('stop')
            VssIdcStock.StartUpTcp()    
        elif string.lower(sys.argv[1]) == '--help' or '-help' or 'help' or ".*":
            print BaseHandle.ArgvUage()

Index()
        


    
    
