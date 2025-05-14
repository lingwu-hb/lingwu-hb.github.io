---
title: algorithm notebook
date: 2025-04-02 17:19:19
categories:
- Leetcode
tags:
- algorithm
---



# 算法笔记

## 数据结构类 tip

### string 类常用方法

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



### vector 

去掉 vector 中的某一个位置的元素。

`vec.erase(vec::iterator)`

### 线段树模板

```c++
class SegmentTree {
    // 数组实现线段树，下标从 1 开始
public:
    vector<int> _tree;
    SegmentTree(vector<int>& nums, int n) { 
        _tree.resize(4*(n+1)); 
        build(nums, 1, n, 1);
    }
    void maintain(int root) {
        _tree[root] = _tree[2*root] + _tree[2*root+1];
    }
    // 这里的 [l, r] 表示当前 root 对应的节点所维护的范围
    void build(vector<int>& nums, int l, int r, long long root) {  // 改为 long long
        if(l == r) {
            _tree[root] = nums[l-1];
            return;
        }
        int mid = l + (r - l)/2;
        build(nums, l, mid, 2*root);
        build(nums, mid+1, r, 2*root+1);
        maintain(root);
    }
    // 单点更新 + 区间查询
    int query(int l, int r, long long root, int ql, int qr) {  // root 改为 long long
        if(ql <= l && r <= qr) {
            return _tree[root];
        }
        int mid = l + (r - l) /2;
        if(qr <= mid) {
            return query(l, mid, 2*root, ql, qr);
        } else if(ql > mid) {
            return query(mid+1, r, 2*root+1, ql, qr);
        } else {
            return query(l, mid, 2*root, ql, mid) + query(mid+1, r, 2*root+1, mid+1, qr);
        }
    }
    void update(int l, int r, long long root, int idx, int val) {  // root 改为 long long
        if(l == r) {
            _tree[root] = val;
            return;
        }
        int mid = l + (r - l) /2;
        if(idx <= mid) {
            update(l, mid, 2*root, idx, val);
        } else {
            update(mid+1, r, 2*root+1, idx, val);
        }
        maintain(root);
    }
};
```

本质上就是树的后序遍历步骤，首先**处理递归边界**，然后考虑**处理左右节点**，最后考虑**退栈的维护工作**，整体分为三步走流程！

### c++ 自定义优先队列

```c++
struct cmp {
    bool operator()(const Node& a, const Node& b) {
        return a.priority > b.priority; // 按优先级升序排列
    }
}
priority_queue pq(Node, vector<Node>, cmp); // 固定用这种格式进行操作即可
```







## 算法类 tip

### 二分查找常用函数

！！！二分查找需要数组有序，如果无序，可以考虑使用线段树。

`lower_bound`

- **功能**：返回一个迭代器，指向第一个不小于目标值的元素。
- **返回值**：迭代器，如果未找到，则返回 `end()`。

```cpp
auto it = std::lower_bound(vec.begin(), vec.end(), target);
    if (it != vec.end()) {
        std::cout << "第一个不小于 " << target << " 的元素是: " << *it << std::endl;
    } else {
        std::cout << "未找到不小于 " << target << " 的元素" << std::endl;
    }
```

`upper_bound`

* 功能：返回一个迭代器，指向第一个大于目标值的元素。

`binary_search`

* 功能：检查有序序列中是否存在某个值。
* 返回值：返回一个布尔值，表示是否找到目标值。
