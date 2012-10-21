#-*- coding=utf-8

#下一步：尝试发送arg过去看能不能播放

from twisted.internet import reactor,protocol
from twisted.web import proxy,http,client
import logging 
from twisted.web.client import Agent
from twisted.web.iweb import IBodyProducer
from zope.interface import implements
import urllib

#日志初始化
ServerPort = 9000
logger = logging.getLogger('mylogger') 
logger.setLevel(logging.DEBUG)
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
logger.addHandler(console)
logger.addHandler(logging.FileHandler(filename='log.txt'))
agent = Agent(reactor)


class MyProxyRequest(proxy.ProxyRequest):
    '''处理用户的请求'''
    def process(self):
        '''如果是POST的方法, 则将post里面的数据传到PostBodyProducer发送'''
        if self.method == 'POST':
            logger.debug('uri: %s \nmethod: %s\n'%(self.uri,self.method)) 
            logger.debug('request headers: %s\n'%self.requestHeaders)
            print self.requestHeaders.getRawHeaders("content-type")
            self.defer = agent.request(self.method, self.uri, headers=self.requestHeaders,bodyProducer=PostBodyProducer(self))
            
        else:
            self.defer = agent.request(self.method, self.uri, headers=self.requestHeaders)
            self.defer.addCallback(handle,request=self)
            self.defer.addErrback(handleErr,request=self)
        
    def connectionLost(self, reason):
        '''长时间请求未响应就关闭当前请求'''
        if self is not None:
            logger.debug('Remote Host have no response \n %s\n'%reason)
            self.finish()
   
class MyProxy(proxy.Proxy):
    requestFactory = MyProxyRequest
    
class MyProxyFactory(http.HTTPFactory):
    protocol = MyProxy
    
class PostBodyProducer(object):
    implements(IBodyProducer)
    def __init__(self,request):
        print '__init__'
        self.request = request
        self.body = urllib.urlencode(request.args)
        self.length = len(self.body)
        
    def startProducing(self, consumer):
        consumer.write(self.body)
        
    def stopProducing(self):
        print 'stopProducing' 
        self.request.defer.addCallback(handle,request=self.request)
        self.request.defer.addErrback(handleErr,request=self.request)

#
class MyProxyResponse(http.HTTPClient):
    '''处理去替用户请求的回应，并转发给客户端'''
    def __init__(self,request, response):
        self.request = request
        self.response = response
        
    def connectionLost(self, reason):
        if isinstance(reason.value, client.ResponseDone):
            if self.request is not None:
                #logger.debug('ResponseDone')
                self.request.finish()
                self.request = None
        else: print 'Some other Error'
        
    def dataReceived(self, data):
        if self.request.method == 'POST':
            print 'POST DATA'
        self.request.write(data)
            

def handle(response,request):
    '''处理从网页下载下来的回应'''
    if request.method == 'POST':
        print 'POST DATA'    
        logger.debug('response.code%d\n'%response.code)
    request.setResponseCode(response.code)
    request.responseHeaders = response.headers
    if response.code in (304, 404):
            request.finish()
            request = None
    else: 
        response.deliverBody(MyProxyResponse(request,response))

def handleErr(reason,request):
    '''处理请求失败的情况'''
    print 'handleErr:\n%s\n'%reason
    if request is not None:
        request.finish()
        request = None
    
if __name__ == '__main__':
    reactor.listenTCP(ServerPort,MyProxyFactory())
    logger.debug('server is listening at %d'%ServerPort)
    reactor.run()