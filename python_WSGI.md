## WSGI web server gateway interface

> 一种标准，用于协调服务器端和python程序端的交互，适用于python
>
> **服务器程序怎么把接受到的请求传递给 python 呢，怎么在网络的数据流和 python 的结构体之间转换呢？**这就是 wsgi 做的事情：一套关于程序端和服务器端的规范，或者说统一的接口。

所以这里大概存在了两个角色：服务器程序、python程序，如果复杂一点还会有中间件程序。

服务器程序需要定义两个要素：start_response(用于python程序调用吗，生成response)，environ(环境信息)
'''
    application 即为python程序。python程序可以是函数、也可以是可被调用的类或实例。
    1. environ 和 start_response 由 http server 提供并实现
    2. environ 变量是包含了环境信息的字典
    3. Application 内部在返回前调用 start_response
    4. start_response也是一个 callable，接受两个必须的参数，status（HTTP状态）和 response_headers（响应消息的头）
    5. 可调用对象要返回一个值，这个值是可迭代的。
'''

简单流程为：客户端向服务端发送消息，服务器调用appliction，传递environ和start_response;appliction生成报文所需信息后，调用start_response，开始返回报文。

复杂情况下，会存在中间层。

'''
    有些程序可能处于服务器端和程序端两者之间：对于服务器程序，它就是应用程序；而对于应用程序，它就是服务器程序。这就是中间层 middleware。middleware 对服务器程序和应用是透明的，它像一个代理/管道一样，把接收到的请求进行一些处理，然后往后传递，一直传递到客户端程序，最后把程序的客户端处理的结果再返回。

    middleware 做了两件事情：
        被服务器程序（有可能是其他 middleware）调用，返回结果回去
        调用应用程序（有可能是其他 middleware），把参数传递过去
'''

中间层即可以充当服务器（对application到服务器的方向），也可以充当application(从服务器到application的方向)。

从方向1，它得能够被调用，传递参数--> 以装饰器的形式被application调用
从方向二，需要能够调用程序。     

----------------------------

参考：https://cizixs.com/2014/11/08/understand-wsgi/