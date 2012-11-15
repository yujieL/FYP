#!/usr/bin/env python
#coding:utf-8
# Author:  yujie
# Purpose: Sock5
# Created: 2012/11/14
    
import socket,struct

class Sock5Header(object):
    '''
    1st
         Client Requset                     Server Response
    +----+----------+----------+            +----+--------+
    |VER | NMETHODS | METHODS |             |VER | METHOD |
    +----+----------+----------+            +----+--------+
    | 1 |    1     | 1 to 255 |             | 1 |    1    |
    +----+----------+----------+            +----+--------+
    
    2nd    
                    Client Request
    +----+-----+-------+------+----------+----------+
    |VER | CMD |  RSV  | ATYP | DST.ADDR | DST.PORT |
    +----+-----+-------+------+----------+----------+
    | 1 |   1  | X'00' | 1    | Variable |    2     |
    +----+-----+-------+------+----------+----------+
    
                    Server Response
    +----+-----+-------+------+----------+----------+
    |VER | REP |  RSV  | ATYP | BND.ADDR | BND.PORT |
    +----+-----+-------+------+----------+----------+
    | 1  |  1  | X'00' |  1   | Variable |    2     |
    +----+-----+-------+------+----------+----------+
    '''    
    #VER
    VER = '\x05'
    #METHOD
    METHOD_AUTHMECH_ANON = '\x00'
    METHOD_AUTHMECH_USERPASS = '\x02'
    METHOD_AUTHMECH_INVALID = '\xFF'
    #ATYP
    ATYP_IPV4 = '\x01'
    ATYP_DOMAINNAME = '\x03'
    ATYP_IPV6 = '\x04'
    #CMD
    CMD_CONNECT = '\x01'
    CMD_BIND = '\x02'
    CMD_UDPASSOC = '\x03'
    #REP
    REPLY_SUCCESS = '\x00'
    REPLY_GENERAL_FAILUR = '\x01'
    REPLY_CONN_NOT_ALLOWED = '\x02'
    REPLY_NETWORK_UNREACHABLE = '\x03'
    REPLY_HOST_UNREACHABLE = '\x04'
    REPLY_CONN_REFUSED = '\x05'
    REPLY_TTL_EXPIRED = '\x06'
    REPLY_CMD_NOT_SUPPORTED = '\x07'
    REPLY_ADDR_NOT_SUPPORTED = '\x08'    
    #DEFAULT
    DEFAULT = '\x00'
    
    def NO_AUTHENTICATION_REQUIRED(self):
        return self.VER+self.METHOD_AUTHMECH_ANON
    
    def RM_REPLY_SUCCESS(self,atyp=1,addr='127.0.0.1',port=80):
        '@atyp 1: ipv4; 2: domain name; 3: ipv6'
        if atyp is 1:
            return self.__RM_REPLY_SUCCESS_IP4(addr, port)
        
    def __RM_REPLY_SUCCESS_IP4(self,addr,port):
        return (
                self.VER
                +self.REPLY_SUCCESS 
                +self.DEFAULT
                +self.ATYP_IPV4
                +socket.inet_aton(addr)
                +struct.pack(">H", port)
               )
    
if __name__ == '__main__':
    print repr(Sock5Header().RM_REPLY_SUCCESS())