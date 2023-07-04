# 这是一个学习cmake的记录，主要记录cmake的几个语法、规则

> 以使用为准，不求大而全

cmake允许大小写的模式，所以我就统一用小写，只有cmake固定的地方用大写

函数：

project{vierable} #定义项目名称，也是之后运行的项目名称

cmake_minimum_required(VERSION 3.16.3) #cmake版本

add_executable(programTest main.cc) #形成运行文件，如果有多个源代码在一个文件夹里，也可以一起编译形成一个执行文件

比如：add_executable(programTest main.cc test1.cc test2.cc)

add_subdirectory(source_dir [binary_dir] [EXCLUDE_FROM_ALL]) #source_dir指定subdirectory的路径，一般来说加上binary_dir 参数更稳当
```
hello-world/
├── CMakeLists.txt
├── main.c
├── test
│   ├── CMakeLists.txt
│   └── main.c
├── hello
│   ├── CMakeLists.txt
│   ├── hello.c
│   └── hello.h
└── world
    ├── CMakeLists.txt
    ├── world.c
    └── world.h
```

当使用库函数的时候项目结构就如上所示，此时就不是main.cc,hello.c,world.c一起编译成一个可执行文件。而是库函数编译成一个动态链接库文件（Linux：.so;windows:.dll)，main.c生成执行文件，然后再cmakelists里链接。

https://zhuanlan.zhihu.com/p/85980099

link_libraries([item1 [item2 [...]]]
               [[debug|optimized|general] <item>] ...)

#将库链接到稍后添加的所有目标。用于add_executable()之前

target_link_libraries(<target> ... <item>... ...)
target_link_libraries(<target>
                      <PRIVATE|PUBLIC|INTERFACE> <item>...
                     [<PRIVATE|PUBLIC|INTERFACE> <item>...]...)

#指定链接给定目标和/或其依赖项时要使用的库或标志。将传播链接库目标的使用要求。目标依赖项的使用要求会影响其自身源的编译。用于add_executable()之后

https://blog.csdn.net/whl0071/article/details/123876364