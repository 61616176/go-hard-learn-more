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
    loadPcap（）-->加载pcap文件生成入侵检测的json文件,可是ins.json用处在哪还不知道
    调用shell命令启动ns3
    读取ns3运行的输出文件 scene_output.txt,生成ret记录每个包和他的ns3处理信息？
                      没太看懂loadPacket在干嘛
    返回ret
```
