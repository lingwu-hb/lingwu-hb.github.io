---
title: algorithm notebook
date: 2025-04-02 17:19:19
categories:
- Leetcode
tags:
- algorithm
---



# 算法笔记



## c++ string 类常用方法

```c++
#include <iostream>
#include <string>
using namespace std;
int main(){
    //字符数组转字符串
    char a[100];
    string s5(a);
    cout<<s5<<endl; //输出World!

    //8、字符串的子串
    s1 = "hello World!";
    s2 = s1.substr(2,5);
    cout<<s2<<endl; //输出 llo W 从下标2开始 截取5个字符
    s2 = s1.substr(3);
    cout<<s2<<endl; //输出 llo W 从下标3开始 截取3到末尾的所有字符

    //9、查找字符串的子串
    int n = s1.find("World");
    cout<<n<<endl; //输出6 即从下标6开始就是这个匹配的字符
    cout<<s1.find("o")<<endl; //输出4 从前往后查找输出最先匹配到的下标
    cout<<s1.rfind("o")<<endl; //输出7 从后往前查找输出最先匹配到的下标
    cout<<s1.find("oo")<<endl; //返回值为 string::npos

    //10、替换字符串
    s1 = "hello World!";
    s1.replace(0,5,"fuck");
    cout<<s1<<endl; //输出fuck World!
    //指定替换 例如将World! 中的orl 替换成ORL
    n = s1.find("orl");
    s1.replace(n,3,"ORL");
    cout<<s1<<endl; //输出fuck WORLd!

    //11、删除子串
    s1.erase(n,3); //n表示位置 3表示删除三个字符
    cout<<s1<<endl; //输出fuck Wd!

    //12、添加子串
    s1.insert(5,"aaa");//5表示位置 "aaa"表示增加的字符串
    cout<<s1<<endl; //输出fuck aaaWd!

    //13、STL 操作string
    string s("afgc1bed3");
    string::iterator p = find(s.begin(), s.end(), 'c');
    if (p!= s.end())
        cout << p - s.begin() << endl;  //输出3 相当于c的指针-头指针
    sort(s.begin(), s.end()); //字符串排序
    cout << s << endl;  //输出 13abcdefg
    //其余STL操作就不演示了，基本上都是支持的
    
    return 0;
}
```

