## pyshark阅读源码

>对许多不懂的东西的集合，没有主题

-------------------------

#### @ 装饰器

装饰器是一种编程思想，实际上就是把函数看作一个对象/实例，用一个新的函数把原函数包裹起来，添加一些增强或限制。

```
def decorator(func):  
    def wrapper():  
        # 新增功能或者附加限制条件  
        # ...   
        return func()  
    return wrapper

eg.
import time

def my_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print("Function took {:.6f} seconds.".format(end_time - start_time))
        return result
    return wrapper

def my_function(x):
    time.sleep(x)
    return x

decorated_function = my_decorator(my_function)
print(decorated_function(2))
```
https://zhuanlan.zhihu.com/p/625695464#:~:text=Python%E8%A3%85%E9%A5%B0%E5%99%A8%E7%9A%84%E5%8E%9F%E7%90%86%E5%92%8C%E7%94%A8%E6%B3%95%201%201%E3%80%81%E5%9F%BA%E6%9C%AC%E6%A6%82%E5%BF%B5%20%E8%A3%85%E9%A5%B0%E5%99%A8%EF%BC%88Decorator%EF%BC%89%E6%98%AF%20Python%20%E8%AF%AD%E8%A8%80%E4%B8%AD%E7%9A%84%E4%B8%80%E4%B8%AA%E5%86%85%E7%BD%AE%E5%87%BD%E6%95%B0%EF%BC%8C%E5%AE%83%E7%9A%84%E4%BD%9C%E7%94%A8%E6%98%AF%E5%9C%A8%E4%B8%8D%E4%BF%AE%E6%94%B9%E5%8E%9F%E6%9C%89%E4%BB%A3%E7%A0%81%E7%9A%84%E6%83%85%E5%86%B5%E4%B8%8B%EF%BC%8C%E4%B8%BA%E8%A2%AB%E8%A3%85%E9%A5%B0%E7%9A%84%E5%AF%B9%E8%B1%A1%E5%A2%9E%E5%8A%A0%E6%96%B0%E7%9A%84%E5%8A%9F%E8%83%BD%E6%88%96%E8%80%85%E9%99%84%E5%8A%A0%E9%99%90%E5%88%B6%E6%9D%A1%E4%BB%B6%E3%80%82%20%E8%A3%85%E9%A5%B0%E5%99%A8%E6%9C%AC%E8%B4%A8%E4%B8%8A%E8%BF%98%E6%98%AF%E5%87%BD%E6%95%B0%EF%BC%8C%E4%BD%86%E6%98%AF%E5%AE%83%E4%BC%9A%E5%B0%86%E5%87%BD%E6%95%B0%E7%9A%84%E8%B0%83%E7%94%A8%E5%92%8C%E8%A2%AB%E8%A3%85%E9%A5%B0%E7%9A%84%E5%AF%B9%E8%B1%A1%E5%85%B3%E8%81%94%E8%B5%B7%E6%9D%A5%EF%BC%8C%E4%BB%8E%E8%80%8C%E8%BE%BE%E5%88%B0%E4%BF%AE%E6%94%B9%E6%88%96%E5%A2%9E%E5%8A%A0%E8%A2%AB%E8%A3%85%E9%A5%B0%E5%AF%B9%E8%B1%A1%E8%A1%8C%E4%B8%BA%E7%9A%84%E7%9B%AE%E7%9A%84%E3%80%82%20%E8%A3%85%E9%A5%B0%E5%99%A8%E7%9A%84%E4%B8%80%E8%88%AC%E8%AF%AD%E6%B3%95%E7%BB%93%E6%9E%84%E5%A6%82%E4%B8%8B%EF%BC%9A,%E4%BE%8B%E5%A6%82%EF%BC%8C%E4%B8%8B%E9%9D%A2%E6%98%AF%E4%B8%80%E4%B8%AA%E7%94%A8%E4%BA%8E%E8%AE%A1%E7%AE%97%E5%87%BD%E6%95%B0%E8%BF%90%E8%A1%8C%E6%97%B6%E9%97%B4%E7%9A%84%E8%A3%85%E9%A5%B0%E5%99%A8%E5%87%BD%E6%95%B0%EF%BC%8C%E5%AE%83%E7%9A%84%E7%AD%89%E6%95%88%E5%86%99%E6%B3%95%E6%98%AF%EF%BC%9A%20...%203%203%E3%80%81%E8%A2%AB%E8%A3%85%E9%A5%B0%E5%99%A8%E5%8F%82%E6%95%B0%E5%86%99%E6%B3%95%20%E8%A2%AB%E8%A3%85%E9%A5%B0%E5%87%BD%E6%95%B0%E7%9A%84%E5%8F%82%E6%95%B0%E5%8F%96%E5%86%B3%E4%BA%8E%E8%A3%85%E9%A5%B0%E5%99%A8%E5%87%BD%E6%95%B0%E7%9A%84%E5%8F%82%E6%95%B0%EF%BC%8C%E4%B8%80%E8%88%AC%E6%9D%A5%E8%AF%B4%EF%BC%8C%E8%A3%85%E9%A5%B0%E5%99%A8%E5%87%BD%E6%95%B0%E5%BA%94%E8%AF%A5%E6%8E%A5%E6%94%B6%E4%B8%80%E4%B8%AA%E5%87%BD%E6%95%B0%E4%BD%9C%E4%B8%BA%E5%8F%82%E6%95%B0%EF%BC%8C%E5%B9%B6%E8%BF%94%E5%9B%9E%E4%B8%80%E4%B8%AA%E6%96%B0%E7%9A%84%E5%87%BD%E6%95%B0%E6%88%96%E7%B1%BB%E5%AF%B9%E8%B1%A1%EF%BC%8C%E6%96%B0%E7%9A%84%E5%87%BD%E6%95%B0%E6%88%96%E7%B1%BB%E5%AF%B9%E8%B1%A1%E4%BC%9A%E6%9B%BF%E6%8D%A2%E5%8E%9F%E6%9D%A5%E7%9A%84%E5%87%BD%E6%95%B0%E6%88%96%E7%B1%BB%E5%AF%B9%E8%B1%A1%EF%BC%8C%E4%BB%8E%E8%80%8C%E8%BE%BE%E5%88%B0%E5%AF%B9%E5%8E%9F%E6%9C%89%E4%BB%A3%E7%A0%81%E5%8A%9F%E8%83%BD%E7%9A%84%E5%8A%A8%E6%80%81%E4%BF%AE%E6%94%B9%E3%80%82%20%E8%A2%AB%E8%A3%85%E9%A5%B0%E5%87%BD%E6%95%B0%E7%9A%84%E5%8F%82%E6%95%B0%E5%8F%AF%E4%BB%A5%E9%80%9A%E8%BF%87%E4%BD%BF%E7%94%A8%E5%8F%82%E6%95%B0%E8%A7%A3%E5%8C%85%E7%9A%84%E6%96%B9%E5%BC%8F%E4%BC%A0%E9%80%92%E7%BB%99%E8%A3%85%E9%A5%B0%E5%99%A8%E5%87%BD%E6%95%B0%E7%9A%84%E5%8C%85%E8%A3%85%E5%87%BD%E6%95%B0%E6%88%96%E7%B1%BB%E4%B8%AD%E3%80%82%20%E4%BB%A5%E4%B8%8B%E6%98%AF%E4%B8%80%E4%BA%9B%E5%B8%B8%E8%A7%81%E7%9A%84%E8%A2%AB%E8%A3%85%E9%A5%B0%E5%87%BD%E6%95%B0%E5%8F%82%E6%95%B0%E7%9A%84%E5%86%99%E6%B3%95%EF%BC%9A%20

-----------------------------------

#### f-string

python3.6 新引入的字符串表示法，在%s,format上更进一步。
1.  f-string用大括{ }表示被替换字段，其中直接填入替换内容即可。 eg. f"Hello, my name is {name}"
2.  f-string的大括号{ }可以填入表达式或调用函数，Python会求出其结果并填入返回的字符串内 eg. f"They have {2+5*2} apples"
3.  f-string中使用lambda匿名函数：可以做复杂的数值计算 eg. f"{(lambda x:x*5-2)(aa):.2f}"

--------------------------

#### self

python 传递给方法的第一个参数就是调用方法的实例对象，一般建议用self表示他——这是一种好的编程实践。
```
self represents the instance of the class. By using the “self”  we can access the attributes and methods of the class in python. It binds the attributes with the given arguments.

The reason you need to use self. is because Python does not use the @ syntax to refer to instance attributes. Python decided to do methods in a way that makes the instance to which the method belongs be passed automatically, but not received automatically: the first parameter of methods is the instance the method is called on.
```

c++类方法似乎是把对象实例隐式传递给了方法，可以通过self访问。

--------------------------------------------

#### python注释
```
def function(name:str='xiaoliu', sex:bool = 1) -> bool:
    ...
其中：后面为对参数的注释
    ->后米是对返回结果的注释
    =是给参数赋的默认值
    python对注释不做任何操作
```