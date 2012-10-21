#-*- coding=utf-8
from twisted.internet import reactor,protocol
from twisted.web import proxy,http,client
import logging 
from twisted.web.client import Agent

#日志初始化
ServerPort = 9000
logger = logging.getLogger('mylogger') 
logger.setLevel(logging.DEBUG)
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
logger.addHandler(console)
logger.addHandler(logging.FileHandler(filename='log.txt'))
agent = Agent(reactor)

#处理用户的请求
class MyProxyRequest(proxy.ProxyRequest):
    def process(self):
        #logger.debug(self.getAllHeaders())
        logger.debug('uri: %s \nmethod: %s'%(self.uri,self.method))
        #logger.debug('request headers: %s'%self.requestHeaders)
        self.defer = agent.request(self.method, self.uri, headers=self.requestHeaders)
        self.defer.addCallback(handle,request=self)
        self.defer.addErrback(handleErr,request=self)
        
    def connectionLost(self, reason):
        if self is not None:
            logger.debug('Remote Host have no response \n %s\n'%reason)
            self.finish()
   
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
        if isinstance(reason.value, client.ResponseDone):
            if self.request is not None:
                logger.debug('ResponseDone')
                self.request.finish()
                self.request = None
        else: print 'Some other Error'
        
    def dataReceived(self, data):
        self.request.write(data)
            

#处理从网页下载下来的回应
def handle(response,request):
    #logger.debug('response.code%d'%response.code)
    request.setResponseCode(response.code)
    request.responseHeaders = response.headers
    if response.code in (304, 404):
            request.finish()
            request = None
    else: 
        response.deliverBody(MyProxyResponse(request,response))

#处理请求失败的情况        
def handleErr(reason,request):
    #print 'handleErr%s: '%reason
    if request is not None:
        request.finish()
        request = None
    
if __name__ == '__main__':
    reactor.listenTCP(ServerPort,MyProxyFactory())
    logger.debug('server is listening at %d'%ServerPort)
    reactor.run()