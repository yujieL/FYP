from twisted.internet import protocol,reactor,endpoints
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
    HTTP_STATUS_CODE=(304,404)
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
                                        oppsite=self,data=data)).addErrback(handleErr,self)
    
    def __handleSock5Auth(self,data):
        #print repr(data)
        if self.times == 1:
            self.transport.write(self.sock5Header.NO_AUTHENTICATION_REQUIRED())
            
        elif self.times == 2:
            header_length = len(data)
            host = data[5:header_length-2]
            port =struct.unpack('>H',data[header_length-2:header_length])[0] 
            #print host,"---------------",port
            client = endpoints.TCP4ClientEndpoint(reactor, host, port)
            client.connect(ProxyFactory(ProxySock5ClientProtocol, 
                                    oppsite=self,data=self.sock5Header)).addErrback(handleErr,self)
        elif self.times == 3:
            #print self.oppsite
            self.oppsite.transport.write(data)
            
class ProxyHttpClientProtocol(protocol.Protocol):
        
    def connectionMade(self):
        self.transport.write(self.factory.header)
        
    def dataReceived(self, data):
        self.oppsite.transport.write(data)
        
    def connectionLost(self, reason):        
        self.oppsite.transport.loseConnection()
        self.transport.loseConnection()

class ProxySock5ClientProtocol(protocol.Protocol):
            
    def connectionMade(self):
        curhost = self.transport.getHost()
        addr, port = curhost.host,curhost.port        
        self.oppsite.transport.write(self.factory.header.RM_REPLY_SUCCESS(addr=addr,port=port))
        
    def dataReceived(self, data):
        self.oppsite.transport.write(data)
        
    def connectionLost(self, reason):        
        self.oppsite.transport.loseConnection() 
        self.transport.loseConnection()
        
def handleErr(reason,protocol):
    print protocol.factory.addr,'refuse'
    protocol.transport.loseConnection()  

if __name__ == '__main__':    
    e = endpoints.TCP4ServerEndpoint(reactor, 1080)
    f = ProxyFactory(ProxyServerProtocol)
    e.listen(f)
    print 'Server is running at 1080'
    reactor.run()