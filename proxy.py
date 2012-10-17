#-*- coding=utf-8
from twisted.internet import reactor,protocol
from twisted.web import proxy,http
import logging 
from twisted.web.client import Agent

#日志初始化
ServerPort = 9000
#logger = logging.get#logger('my#logger') 
#logger.setLevel(logging.DEBUG)
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
#logger.addHandler(console)
#logger.addHandler(logging.FileHandler(filename='log.txt'))
agent = Agent(reactor)

#处理用户的请求
class MyProxyRequest(proxy.ProxyRequest):
    def process(self):
        #logger.debug(self.getAllHeaders())
        #logger.debug('uri: %s method: %s'%(self.uri,self.method))
        #logger.debug('request headers: %s'%self.requestHeaders)
        self.defer = agent.request(self.method, self.uri, headers=self.requestHeaders)
        self.defer.addCallback(handle,request=self)
        
class MyProxy(proxy.Proxy):
    requestFactory = MyProxyRequest
    
class MyProxyFactory(http.HTTPFactory):
    protocol = MyProxy

#处理去替用户请求的回应，并转发给客户端
class MyProxyResponse(http.HTTPClient):
    def __init__(self,request, response):
        self.request = request
        self.response = response
        
    def connectionLost(self, reason):
        self.request.finish()
    def dataReceived(self, data):
        #logger.debug(data)
        self.request.responseHeaders = self.response.headers
        self.request.write(data)
            
        
#处理从网页下载下来的回应
def handle(response,request):
    #logger.debug('response.headers: %s'%response.headers)
    response.deliverBody(MyProxyResponse(request,response))
    
if __name__ == '__main__':
    reactor.listenTCP(ServerPort,MyProxyFactory())
    logger.debug('server is listening at %d'%ServerPort)
    reactor.run()