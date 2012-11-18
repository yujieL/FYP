#coding:utf-8
# Author:  yujie
# Purpose: FYP
# Created: 2012/11/18


from twisted.internet import protocol,reactor,endpoints,ssl
import re,struct,socks5,socket

class ProxyFactory(protocol.Factory):
    
    addr = None
    def __init__(self,PROTOCOL,oppsite=None,**kwarg):
        '''
        @PROTOCOL A Class type of twisted.internet.protocol.Protocol,indicated self protocol
        @oppsite indicated remote protocol
        '''
        self.ProtocolClass = PROTOCOL
        self.oppsite = oppsite
        if kwarg.has_key('data'): self.header = kwarg['data']
        
    def buildProtocol(self, addr):
        self.protocol = self.ProtocolClass()
        self.protocol.factory = self
        self.protocol.oppsite = self.oppsite
        if self.oppsite is not None: self.oppsite.oppsite = self.protocol       
        return self.protocol
    
class ProxyServerProtocol(protocol.Protocol):
    TYPES = ('HTTP','SOCK5')
    proxyType = ''
    times = 0
    sock5Header = None
    
    def dataReceived(self, data):        
        self.times += 1
        if self.times is 1:
            self.proxyType = self.TYPES[0] if len(data) >30 else self.TYPES[1]
            
        if self.proxyType == 'HTTP':
            self.__handleHttpRequest(data)
            
        elif self.proxyType == 'SOCK5':
            self.sock5Header = socks5.Sock5Header()
            self.__handleSock5Auth(data)
            
    def connectionLost(self, reason):
        self.times = 0
        self.transport.loseConnection()
        
    def setOppsite(self,protocol):
        self.oppsite = protocol
        
    def __handleHttpRequest(self,data):
        headers = dict(re.findall(r"(?P<name>.*?): (?P<value>.*?)\r\n", data))
        if headers.has_key('Host'):
            client = endpoints.TCP4ClientEndpoint(reactor, headers['Host'], 80)
            client.connect(ProxyFactory(ProxyHttpClientProtocol,
                                       oppsite=self,data=data)).addErrback(handleHttpErr,self)
        else: self.transport.loseConnection()
        
    def __handleSock5Auth(self,data):
        if self.times == 1:
            self.transport.write(self.sock5Header.NO_AUTHENTICATION_REQUIRED())
            
        elif self.times == 2:
            header_length = len(data)
            host = data[5:header_length-2]
            port =struct.unpack('>H',data[header_length-2:header_length])[0] 
            client = endpoints.TCP4ClientEndpoint(reactor, host, port)
            client.connect(ProxyFactory(ProxySock5ClientProtocol, 
                                oppsite=self,data=self.sock5Header)).addErrback(handleSock5Err,self)
        elif self.times >= 3:
            self.oppsite.transport.write(data)
            
class ProxyHttpClientProtocol(protocol.Protocol):
        
    def connectionMade(self):
        self.transport.write(self.factory.header)
        
    def dataReceived(self, data):
        self.oppsite.transport.write(data)
        
    def connectionLost(self, reason):        
        self.transport.loseConnection()

class ProxySock5ClientProtocol(protocol.Protocol):
            
    def connectionMade(self):
        curhost = self.transport.getHost()
        addr, port = curhost.host,curhost.port
        #('192.168.162.95', 5204)   '\x05\x00\x00\x01\xc0\xa8\xa2_\x14T'
        #print 'Reply:',repr(self.factory.header.RM_REPLY_SUCCESS(addr='192.168.162.95',port=5204))
        self.oppsite.transport.write(self.factory.header.RM_REPLY_SUCCESS(addr=addr,port=port))
        
    def dataReceived(self, data):
        self.oppsite.transport.write(data)
        
    def connectionLost(self, reason):        
        self.transport.loseConnection() 
        
def handleHttpErr(reason,protocol):
    print 'Server refuse Http'
    protocol.transport.loseConnection() 
    
def handleSock5Err(reason,protocol):
    print 'Server refuse Sock5'
    #protocol.transport.write()
    protocol.transport.loseConnection()
    
if __name__ == '__main__':    
    
    PORT = 9000
    e = endpoints.TCP4ServerEndpoint(reactor, PORT)
    f = ProxyFactory(ProxyServerProtocol)
    e.listen(f)
    print 'Server is running at', PORT
    reactor.run()