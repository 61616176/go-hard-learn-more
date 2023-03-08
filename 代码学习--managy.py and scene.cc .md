# managy.py and scene.cc 

> managy.py

列表表达式： data = ",".join([x if x != '"NULL"' else eval(x) for x in [str(ele) if isinstance(ele, int) else '"%s"' % ele for ele in args]])

[str(ele) if isinstance(ele, int) else '"%s"' % ele for ele in args]类似于：
```python
for ele in args:
    if isinstance(ele,int) :  
       str(ele)  
    else :  
       '"%s"'%ele
```
runDT 
```python    
    start_plc()-->调用shell启动openplc
    读取前端传回的消息，把pcap、topo信息写入topopcapcfg.json文件
    loadPcap（）-->读取pcap问价，生成指令文件ins.json。用于之后上下位机加护
    调用shell命令启动ns3
    读取ns3运行的输出文件 scene_output.txt,生成ret记录每个包和他的ns3处理信息
    loadPacket()读取ns3运行的输出文件，交给ret最后返回给前端展示
    返回ret，因为manage.py是处理前后端交互的文件，所以返回ret相当于返回给前端。
```

> scene.cc

### 主要探讨主从节点的交互过程的实现
```c++
   1.  涉及几个类之间的关系
   以主节点启动为例
   case 5: //master
    {   
      ip = j["deviceInfo"][i]["ip"].dump(); 
      ip.erase(0,1);
      ip.erase(ip.length()-1,1);//以上只是获得ip
     
      DeviceMasterHelper master;
      master.SetAttribute("LocalAddress", Ipv4AddressValue(ip.data()));
      masterApp = master.Install (Nodes.Get (i));
      masterApp.Start(Seconds (0.0));
      std::cout << "Node " << i << " is mater, ip:" << ip <<std::endl;
    }
------
    
    applicationContainer是application的容器，可以包含多个application和一些操作
    deviceMasterHelper是帮助管理节点更容易的class
    ApplicationContainer
    DeviceMasterHelper::Install (std::string nodeName) const
    {
      Ptr<Node> node = Names::Find<Node> (nodeName);
      return ApplicationContainer (InstallPriv (node));
    }
    。。。
    
    Ptr<Application>
    DeviceMasterHelper::InstallPriv (Ptr<Node> node) const
    {
      Ptr<Application> app = m_factory.Create<DeviceMaster> ();
      node->AddApplication (app);

      return app;
    }
    master.Install (Nodes.Get (i));将返回一个applicationcontainer（app），同时node拥有一个指向DeviceMaster的app，addapplication将完成对app的初始化
------
    2.application子类deviceMaster的启动
    1)
    void 
    ApplicationContainer::Start (Time start)
    {
      for (Iterator i = Begin (); i != End (); ++i)
        {
          Ptr<Application> app = *i;
          app->SetStartTime (start);
        }
    }
    applicationContainer为每个application设置一个启动时间，当启动时间被设定后，真正的启动代码会被触发
      /**
       * \brief Application specific startup code
       *
       * The StartApplication method is called at the start time specified by Start
       * This method should be overridden by all or most application
       * subclasses.
       */
      virtual void StartApplication (void);
    --> device_Master.cc
    deviceMaster来重载
    DeviceMaster::StartApplication (void)
    {     
      NS_LOG_FUNCTION (this);
      // json文件读取
      std::ifstream ins_file("./ins.json");
      json ins_json ;
      ins_file >> ins_json;

      ///////////////Load instructions from the json file//////////////
      ///////////////从json文件中读取指令//////////////
      for(int i=0; !ins_json[i].empty();i++)
      {     
            /**
       * ins.json[i]格式：
       *{"load": "0000000000070b020013001b0000", "src": "10.1.1.2", 
       * "dst": "10.1.1.1", "ts": "2.008487s", "dport": 502, "sport": 49153}
       */ 
        std::string ipbuf = ins_json[i]["src"].get<std::string>();
        Ipv4Address src = Ipv4Address(ipbuf.data());
        if(src == localAddress)
        {
              // 写入读取到的数据并push到一个list中
          InsInfo ins;
          ins.dport = ins_json[i]["dport"].get<u_int16_t>();
          ins.sport = ins_json[i]["sport"].get<u_int16_t>();
          ins.dst = ins_json[i]["dst"].get<std::string>();
          ins.src = ins_json[i]["src"].get<std::string>();
          ins.ts = Time(ins_json[i]["ts"].get<std::string>());
          ins.load = AsciiToHex(ins_json[i]["load"].get<std::string>());
          ins_list.push_back(ins);
        }
      }
      //////////////////////////////////////////////////////////////////
      net.sendInsList(GetNode(), ins_list, MakeCallback(&DeviceMaster::HandleRead, this));
    }
    一些调用的函数、变量
    void HandleRead (Ptr<Socket> socket);
    std::vector<InsInfo> ins_list; //list of instructions to send
    NetManager net;
    Ipv4Address localAddress;
    
    startApplication功能很简单，读取ins.json中的指令（这是在managy.py中生成的），当指令原地址是节点地址时，存入ins_list，再调用netManager.sendInsList()发送指令。
    2)
    --> net-manager.cc
    * 批量向下位机发送指令
    * \param ins_list The list of instructions to send.
    * \param onReceive Callback function called when receives a reply from slaves.
    */
    void
    NetManager::sendInsList (Ptr<Node> node, std::vector<InsInfo> ins_list, Callback<void, Ptr<Socket>> onReceive)
    {
        NS_LOG_FUNCTION (this);
        for (std::vector<InsInfo>::const_iterator iter = ins_list.begin();iter != ins_list.end(); iter++){
            ...
            std::map<std::pair<std::string, uint16_t>, Ptr<Socket>>::iterator socket = socks.find(dst);
            if (socket == socks.end()){
                TypeId tid = TypeId::LookupByName("ns3::TcpSocketFactory");
                Ptr<Socket> new_sock = Socket::CreateSocket(node, tid);
                //Bind the socket
                   ...
                //Ptr<Socket> new_sock = this->openConnection(node, iter->dst, iter->dport);
                    ...
                this->scheduleSend(*iter, new_sock, iter->ts);
            }
            else{
                this->scheduleSend(*iter, socket->second, iter->ts);
            }
        }
    } 
    netManager一些变量
    std::map<std::pair<std::string, uint16_t>, Ptr<Socket>> socks;
    std::queue<std::pair<InsInfo, Ptr<Socket>>> packs;
    遍历ins_list每一个指令，查看指令目的地是否已经在netManager的socks中存在，若存在，调用scheduleSend（）；不存在，创建new_sock，绑定，病插入sock是，调用scheduleSend（）。
    关于socket的相关函数功能，先不予讨论。着重关注指令发送即scheduleSend（）。
    3)
    void
    NetManager::scheduleSend (InsInfo ins, Ptr<Socket> socket, Time ts)
    {
       ...
        packs.push(std::pair<InsInfo, Ptr<Socket>>(ins, socket));
        Simulator::Schedule (ts, &NetManager::send, this);
    }
    Simulator::Schedule（ts, &NetManager::send, this）大意计划一个规定时间ts之后执行的一个事件--send（），至于怎么完成，比如创建一个链表，把event放进去我们暂且不管。先看send（）。
    send（）首先是从pack队列中拿到队头，创建发送的packet和管道
    pack = packs.front();
    packs.pop();
    Ptr<Socket> socket = pack.second;
    InsInfo ins = pack.first;
    Ptr<Packet> packet = Create<Packet> ((uint8_t*)(ins.load.data()), ins.load.length());
    socket->Connect(InetSocketAddress(Ipv4Address(ins.dst.data()), ins.dport));
    创建好后调用
    socket->Send(packet); 
    而后获得socket本地地址和与socket链接的地址--peerAddress，判断peerAddress的类型。这其中出现基类与子类的调用关系，记录一下。
    Address localAddress;
    Address peerAddress;
    socket->GetSockName(localAddress); 
    socket->GetPeerName(peerAddress);
    if (Ipv4Address::IsMatchingType (peerAddress))
        ...
    else if (Ipv6Address::IsMatchingType (peerAddress))
        ...
        
    -->socket.h
    /**
    * \brief Get the peer address of a connected socket.
    * \param address the address this socket is connected to.
    * \returns 0 if success, -1 otherwise
    */
    virtual int GetPeerName (Address &address) const = 0;
    
    --> address.cc
    bool 
    Address::IsMatchingType (uint8_t type) const
    {       
      NS_LOG_FUNCTION (this << static_cast<uint32_t> (type));
      return m_type == type;
    }                       
    可以得知，Address是Ipv4Address、Ipv6Address的基类，子类可以调用基类的方法；socket是Ipv4RawSocketImpl、Ipv6RawSocketImpl的基类，而实际socket->GetPeerName（）是一个纯虚函数，必须被子类实现。基类可以指向子类，所以socket实际上是Ipv4RawSocketImpl、Ipv6RawSocketImpl或者其他Socket的子类之一，socket->GetPeerName（）实际上等价于（比如：）Ipv4RawSocketImpl->GetPeerName().
    4)回调函数接收下位机发回的信息
    回到net.sendInsList(GetNode(), ins_list, MakeCallback(&DeviceMaster::HandleRead, this));
    其中MakeCallback()生成一个回调函数,（本文最后有回调函数和hook函数的区别）用于处理下位机发回信息时处理。
    -->/root/ns3/ns-allinone-3.33/ns-3.33/src/applications/model 
    void
    DeviceMaster::HandleRead (Ptr<Socket> socket)
    {
      ...
      // 从socket中读取单个数据包并检索发送方地址
      while ((packet = socket->RecvFrom (from)))
      {
        // 获取套接字地址
        socket->GetSockName (local);
        // 如果地址与类型匹配
        if (InetSocketAddress::IsMatchingType (from))
        {
          // 输出时间、client、port、size、from信息
          ...
        }
        else if (Inet6SocketAddress::IsMatchingType (from))
        {
            ...
        }
        // 回调
        m_rxTrace (packet);
        m_rxTraceWithAddresses (packet, from, local);
      }
      socket->Close();
    }
    
    又有 --> device-master.h
    /// Callbacks for tracing the packet Rx events
    /// Traced Callback: received packets.
    TracedCallback<Ptr<const Packet> > m_rxTrace;
    /// Callbacks for tracing the packet Rx events, includes source and destination addresses
    TracedCallback<Ptr<const Packet>, const Address &, const Address &> m_rxTraceWithAddresses;

    TracedCallback是一个模板类
    //Forward calls to a chain of Callback.
    //This is a functor: the chain of Callbacks is invoked by calling the operator() form with the appropriate number of arguments.
    template <typename... Ts>
    class TracedCallback
    {
      public:
        TracedCallback();
        void ConnectWithoutContext(const CallbackBase& callback);
        void Connect(const CallbackBase& callback, std::string path);
        void DisconnectWithoutContext(const CallbackBase& callback);
        void Disconnect(const CallbackBase& callback, std::string path);
        void operator()(Ts... args) const;
        bool IsEmpty() const;

        // Uint32Callback appears to be the only one used at the moment.
        // Feel free to add typedef's for any other POD you need.
        typedef void (*Uint32Callback)(const uint32_t value);
      private:
        typedef std::list<Callback<void, Ts...>> CallbackList;
        CallbackList m_callbackList;
    };
    m_rxTrace和m_rxTraceWithAddresses是编译器将按照TraceCallBack<...Ts>生成的两个独立的类声明和相应两组独立的类方法。
    而
    m_rxTrace (packet);
    m_rxTraceWithAddresses (packet, from, local);
    应该是类调用重载运算符operator（）。如前文所说，开启一个回调函数链。
    5.回调函数触发的时机
    这时候我们必须深入netManager.SendInsList()这个函数了
    /**
    * 批量向下位机发送指令
    * \param ins_list The list of instructions to send.
    * \param onReceive Callback function called when receives a reply from slaves.
    */  
    void
    NetManager::sendInsList (Ptr<Node> node, std::vector<InsInfo> ins_list, Callback<void, Ptr<Socket>> onReceive)   
    {     
        ...
                Ptr<Socket> new_sock = Socket::CreateSocket(node, tid);
                //Bind the socket
                if (new_sock->Bind() == -1)
                {
                    NS_FATAL_ERROR("Failed to bind socket");
                }
                //Ptr<Socket> new_sock = this->openConnection(node, iter->dst, iter->dport);
                socks.insert(std::pair<std::pair<std::string, uint16_t>, Ptr<Socket>>(dst, new_sock));
                new_sock->SetAllowBroadcast (true);
                new_sock->SetRecvCallback (onReceive);
                this->scheduleSend(*iter, new_sock, iter->ts);
        ...
    } 
    new_sock将自身的RecvCallback类赋值为onReceive，也就是handleRead（）。
    6）ns3自己实现了回调函数的机制
    可以作为下一步了解ns3机制的任务，再次先不做讨论。
    https://www.cnblogs.com/lyszyl/p/12077916.html#:~:text=NS3-%E5%9B%9E%E8%B0%83.%20NS-3%E4%B8%AD%E7%9A%84%E5%9B%9E%E8%B0%83%E5%85%B6%E5%AE%9E%E5%B0%B1%E6%98%AFC%20%E8%AF%AD%E8%A8%80%E5%9F%BA%E6%9C%AC%E7%9A%84%E5%87%BD%E6%95%B0%E6%8C%87%E9%92%88%E7%9A%84%E5%B0%81%E8%A3%85%E7%B1%BB%E3%80%82.%20%E5%9B%9E%E8%B0%83%E5%87%BD%E6%95%B0%E6%98%AF%E5%BD%93%E7%89%B9%E5%AE%9A%E4%BA%8B%E4%BB%B6%E6%88%96%E8%80%85%E6%BB%A1%E8%B6%B3%E6%9F%90%E7%A7%8D%E6%9D%A1%E4%BB%B6%E6%97%B6,%28%E6%97%B6%E9%97%B4%E8%B6%85%E6%97%B6%29%E8%A2%AB%E8%B0%83%E7%94%A8%EF%BC%8C%E7%94%A8%E4%BA%8E%E5%AF%B9%E8%AF%A5%E4%BA%8B%E4%BB%B6%E6%88%96%E8%80%85%E6%9D%A1%E4%BB%B6%E8%BF%9B%E8%A1%8C%E5%93%8D%E5%BA%94%EF%BC%8C%E6%98%AF%E4%B8%80%E7%A7%8D%E5%8F%AF%E6%89%A9%E5%B1%95%E7%BC%96%E7%A8%8B%E7%9A%84%E5%B8%B8%E7%94%A8%E6%89%8B%E6%AE%B5%E3%80%82.%20%E5%9B%9E%E8%B0%83%E7%9A%84%E6%9C%80%E5%A4%A7%E5%A5%BD%E5%A4%84%E5%9C%A8%E4%BA%8E%E6%89%A9%E5%B1%95%E6%80%A7%E5%BC%BA%E3%80%82.%20%E4%B8%8D%E9%9C%80%E8%A6%81%E5%92%8C%E5%85%B7%E4%BD%93%E7%9A%84%E5%87%BD%E6%95%B0%E8%BF%9B%E8%A1%8C%E7%BB%91%E5%AE%9A%EF%BC%8C%E8%80%8C%E5%8F%AF%E4%BB%A5%E5%9C%A8%E5%88%9B%E5%BB%BA%E7%9A%84%E6%97%B6%E5%80%99%E5%8A%A8%E6%80%81%E5%86%B3%E5%AE%9A%E5%88%B0%E5%BA%95%E8%B0%83%E7%94%A8%E9%82%A3%E4%B8%AA%E5%87%BD%E6%95%B0%E3%80%82.%20%E4%BE%8B%E5%A6%82%EF%BC%8C%E6%AD%A4%E6%97%B6%E6%88%91%E4%BB%AC%E4%B8%8D%E6%83%B3%E5%86%8D%E8%B0%83%E7%94%A8%E5%8A%A0%E6%B3%95%EF%BC%8C%E8%80%8C%E6%83%B3%E8%B0%83%E7%94%A8%E4%B9%98%E6%B3%95%EF%BC%8C%E9%82%A3%E4%B9%88%E5%8F%AF%E4%BB%A5%E7%BB%99A%E5%AF%B9%E8%B1%A1%E5%AE%9E%E4%BE%8B%E7%BB%91%E5%AE%9A%E4%B9%98%E6%B3%95%E6%93%8D%E4%BD%9C%EF%BC%8C%E8%80%8C%E6%97%A0%E9%9C%80%E6%94%B9%E5%8F%98A%E7%B1%BB%E7%9A%84%E5%AE%9A%E4%B9%89%E3%80%82.%20NS3%E4%B8%AD%E4%BD%BF%E7%94%A8%E5%9B%9E%E8%B0%83%E6%80%9D%E6%83%B3%E6%9D%A5%E5%A4%84%E7%90%86%E5%90%84%E7%A7%8D%E5%8D%8F%E8%AE%AE%E8%B0%83%E7%94%A8%E6%88%96%E8%80%85%E8%BF%BD%E8%B8%AA%E7%B3%BB%E7%BB%9F%E3%80%82.
-----
    3.application子类deviceSlave的启动
    case 6: //slave
    {
        ip = j["deviceInfo"][i]["ip"].dump();
        ip.erase(0,1);
        ip.erase(ip.length()-1,1);
        DeviceSlaveHelper slave(Ipv4AddressValue(ip.data()));
        slaveApp = slave.Install (Nodes.Get (i));
        slaveApp.Start(Seconds (0.0));
        std::cout << "Node " << i << " is slave" <<std::endl;
    }
    这些和deviceMaster差不多，没什么好说的。知道deviceSlave::StartApplication()
    --> device-slave.cc
    /**
    * \brief Handle a packet reception.
    *
    * This function is called by lower layers.
    *
    * \param socket the socket the packet was received to.
     */
    void HandleRead (Ptr<Socket> socket);

   uint16_t m_port; //!< Port on which we listen for incoming packets.
   
   std::set<uint16_t> port_list; //list of port of services
   std::vector<Ptr<Socket>> m_socket; //!< IPv4 Sockets
   Ipv4Address localAddress;
   NetManager net;//!< net manager
    
    deviceSlave的一些函数和变量，注意到，deviceSlave比deviceMaster多了一个套接字向量m_socket
    
    StartApplication()的过程很简单：从ins.json中读指令，当指令的dst和节点的localAddress相同时
    std::set<uint16_t>::iterator p = port_list.find(dport);
    if (p == port_list.end())
        std::cout << "adding port :" << dport << std::endl;
    port_list.insert(dport);
    如果port.list没找到dport，将dport插入port_list。
    if (m_socket.size() == 0 && port_list.size() != 0)//这一步判断还不太懂没什么这么做？为什么要一个socket都没有的时候才创建？不应该socket和port数量相同吗？
    {
      for (std::set<uint16_t>::iterator i = port_list.begin(); i != port_list.end(); i++)
      {
        uint16_t port = *i;
        // std::cout<<"openning service at port :"<<port<<std::endl;
        Ptr<Socket> socket = net.startListen(GetNode(), port, MakeCallback(&DeviceSlave::ConnectionRequestCallback, this),
                                             MakeCallback(&DeviceSlave::NewConnectionCreatedCallback, this),
                                             MakeCallback(&DeviceSlave::HandleRead, this));
        m_socket.push_back(socket);
      }
      // std::cout<<"openning service complete"<<std::endl;
    }
    当没有套接字而有端口号时（也就是有接收信息需求没有服务时），遍历端口列表，为每一个port调用net.startListen()创建套接字，并压入m_socket。
    --> net-manager.cc
    // 监听结点，设置Listen、SetRecvCallback、SetAcceptCallback
    Ptr<Socket>
    NetManager::startListen (Ptr<Node> node, uint16_t port, Callback<bool, Ptr<Socket>, const Address&> onConnect,
                               Callback<void, Ptr<Socket>, const Address&> onConnectCreate, Callback<void, Ptr<Socket>> onReceive)
    {       
        NS_LOG_FUNCTION (this);
        TypeId tid = TypeId::LookupByName("ns3::TcpSocketFactory");
        Ptr<Socket> socket = Socket::CreateSocket(node, tid);
        InetSocketAddress local = InetSocketAddress(Ipv4Address::GetAny(), port);     //local address
        if (socket->Bind(local) == -1)
        {
            NS_FATAL_ERROR("Failed to bind socket");
        }                                    
        socket->Listen();
        // Notify application when new data is available to be read.
        socket->SetRecvCallback(onReceive);
        // Accept connection requests from remote hosts.
        socket->SetAcceptCallback(onConnect, onConnectCreate);                                                                                                                              
        return socket;
    }        
    startListen（）干了几件事：创建套接字，将套接字和地址绑定，开始监听，设置了两个回调函数。
    首先来说，创建socket有几个重要的信息需要知道：套接字类型--TypeID,节点，地址--local 
--
    下位机和上位机的功能不同，导致二者socket的动作也不一样。上位机处于主动地位，只需要发指令+等下位机回复。下位机就需要一直监听，接收消息，回复，执行。
    而很多动作都依赖于回调函数。
--
    -->socket.cc
    * \brief Listen for incoming connections.
   * \returns 0 on success, -1 on error (in which case errno is set).
   */
    virtual int Listen (void) = 0;
    Listen（）就是socket开始监听。
    socket->SetRecvCallback(onReceive);
    和deviceMaster差不多。
    socket->SetAcceptCallback(onConnect, onConnectCreate);
    void 
    Socket::SetAcceptCallback (
      Callback<bool, Ptr<Socket>, const Address &> connectionRequest,
      Callback<void, Ptr<Socket>, const Address&> newConnectionCreated)      
    { 
      NS_LOG_FUNCTION (this << &connectionRequest << &newConnectionCreated);
      m_connectionRequest = connectionRequest;
      m_newConnectionCreated = newConnectionCreated; 
    } 
    下位机要与上位机建立联结，需要有connectionRequest（链接请求）和newConnectionCreated（链接成功）两个回调函数。
    *****关键点：上下位机如何实现链接的？
    
```
    
> 回调函数和hook函数的区别

|回调函数|钩子函数|
|:------|:------|
|回调就是A调用B的方法的同时，传递给B的一个或一组函数指针（或者其他什么形式，只要能调用到A的方法就行），让B可以通知A函数调用的结果。一般来说，这个行为是A发起的，B负责执行，并将结果通过回调返回给A。|钩子的目的不太一样，我们实现B的钩子函数，目的是B在执行某个操作时会会调用这个钩子函数，用于执行我们自定义的一些行为。B通常是系统或者框架的某个模块，实现并注册钩子函数可以扩展系统的行为。钩子函数通常不是必须的，大多数情况不实现钩子函数也会过的好好的。|
|实际上都是一个模块调用另一个模块的方法，只不过目的不同，叫法不一样。|
    
