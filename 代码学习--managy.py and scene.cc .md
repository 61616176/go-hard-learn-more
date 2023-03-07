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
    1.  涉及几个类之间的关系
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
    
    startApplication功能很简单，读取ins.json中的指令（这是在managy.py中生成的），存入ins_list，再调用netManager.sendInsList()发送指令。
    
    * 批量向下位机发送指令
    * \param ins_list The list of instructions to send.
    * \param onReceive Callback function called when receives a reply from slaves.
    */
    void
    NetManager::sendInsList (Ptr<Node> node, std::vector<InsInfo> ins_list, Callback<void, Ptr<Socket>> onReceive)
    {
        NS_LOG_FUNCTION (this);
        for (std::vector<InsInfo>::const_iterator iter = ins_list.begin();iter != ins_list.end(); iter++){
            std::pair<std::string, uint16_t> dst;
            dst.first = iter->dst;
            dst.second = iter->dport;

            std::map<std::pair<std::string, uint16_t>, Ptr<Socket>>::iterator socket = socks.find(dst);
            if (socket == socks.end()){
                TypeId tid = TypeId::LookupByName("ns3::TcpSocketFactory");
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
            }
            else{
                this->scheduleSend(*iter, socket->second, iter->ts);
            }
        }
    } 

    
-----
    3.application子类deviceSlave的启动
```
