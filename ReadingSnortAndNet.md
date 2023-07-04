## 嗅探 混杂（promiscuous vs. non-promiscuous）

嗅探器 可以获取网络上流经的数据包。 用集线器hub组建的网络是基于共享的原理的， 局域网内所有的计算机都接收相同的数据包， 而网卡构造了硬件的“过滤器“ 通过识别MAC地址过滤掉和自己无关的信息， 嗅探程序只需关闭这个过滤器， 将网卡设置为“混杂模式“就可以进行嗅探 用交换机switch组建的网络是基于“交换“原理的 ，交换机不是把数据包发到所有的端口上， 而是发到目的网卡所在的端口。

```
A note about promiscuous vs. non-promiscuous sniffing: The two techniques are very different in style. In standard, non-promiscuous sniffing, a host is sniffing only traffic that is directly related to it. Only traffic to, from, or routed through the host will be picked up by the sniffer. Promiscuous mode, on the other hand, sniffs all traffic on the wire. In a non-switched environment, this could be all network traffic. The obvious advantage to this is that it provides more packets for sniffing, which may or may not be helpful depending on the reason you are sniffing the network. However, there are regressions. Promiscuous mode sniffing is detectable; a host can test with strong reliability to determine if another host is doing promiscuous sniffing. Second, it only works in a non-switched environment (such as a hub, or a switch that is being ARP flooded). Third, on high traffic networks, the host can become quite taxed for system resources.
```

