---
title: Decision Tree Addmission Policy
date: 2025-05-16 16:06:20
categories:
- AI
- data storage
tags:
- 决策树准入
---

# 项目介绍

[项目地址](https://github.com/lingwu-hb/otae)

## 文件结构

```
otae/
├── feature/                   # 特征提取相关文件
│   ├── second_addmission.h    # 二次准入逻辑的头文件
│   ├── second_addmission.cpp  # 二次准入逻辑的实现
│   ├── extract_features.cpp   # 特征提取的实现
│   └── extract_features.exe   # 特征提取的可执行文件
├── train/                     # 训练相关文件
│   ├── trainer.py             # 用于训练模型的脚本
│   └── dataset.py             # 用于处理数据集的脚本
├── classifier/                # 分类器相关文件
│   ├── decision_tree.h        # 决策树的头文件
│   ├── classifier_das.cpp     # DAS 分类器的实现
│   ├── classifier.h           # 分类器的头文件
│   ├── classifier.cpp         # 分类器的实现
│   └── dataset.py             # 用于处理数据集的脚本
├── process_traces.py          # 用于处理跟踪的脚本
├── data/                      # 数据目录
│   ├── web_3/                 # web_3 的数据
│   └── model/                 # 存储模型的目录
```

## 执行流程

参考 `process_traces.py` 自动化脚本，该脚本能完成所有 data 下 trace 的特征提取和模型训练功能。

### 特征提取部分

[参考代码](https://github.com/lingwu-hb/otae/blob/main/process_traces.py#L144)

```python
# 执行特征提取
extract_cmd = ["extract_features.exe" if platform.system() == "Windows" else "./extract_features", trace_filename]
result = subprocess.run(extract_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
```

调用 `extract_features.exe ` 进行特征提取，生成特征文件（feature file）和标签文件（response file）。

* 特征文件生成逻辑

> 参考 extract_features.cpp 文件

主要通过 `class IORequestParser` 类对 trace 文件进行解析，然后提取出所需要的六个特征

```c++
if (io_parser.ParseRecord()) {
    time_t ts = 0;
    do {
      // 记录请求并更新统计信息
      request_tracker.RecordRequest();
      ts = io_parser.GetTimeStamp();
      request_id = io_parser.GetRequestID();
      
      // 获取IO请求的访问时间
      if (request_time_analyzer.GetAccessTime(request_id, ts, request_last_access_time) == false) {
        request_last_access_time = ts; // 首次访问，设置为当前时间
      }
      
      // 获取IO请求访问频率
      access_freq = request_freq_analyzer.GetAccessFrequency(request_id);
      
      // 计算每分钟平均请求量
      avg_requests = request_tracker.GetRequestsPerMinute(ts);
      
      // 输出提取的特征（制表符分隔）
      // 1. 请求地址
      ofs << io_parser.addr << "\t";
      // 2. 请求大小
      ofs << io_parser.size << "\t";
      // 3. 访问时间戳
      ofs << ts << "\t";
      // 4. 重用时间（当前时间 - 上次访问时间）
      ofs << ts - request_last_access_time << "\t";
      // 5. 每分钟平均访问量
      ofs << avg_requests << "\t";
      // 6. 访问次数
      ofs << access_freq << "\n";
      
    } while (io_parser.ParseRecord());
  }
```

* 标签文件生成

> 参考 extract_features.cpp 和 second_addmission.cpp 文件

`extract_features.cpp` 中的 `generate_response_file` 函数生成所需的标签文件。

核心代码：

```c++
// 尝试解析行，格式: /dev/nvme0n1 read 28672 12288
if (iss >> device_name >> operation >> addr >> size) {
    // 使用与IORequestParser类相同的请求ID生成方式
    if(ocf_history_check_second_chance(addr, size)) {
        // 应该被准入，所以 tag = 0
        response_file << "0" << endl;
        zeros_count++;
    } else {
        response_file << "1" << endl;
        ones_count++;
    }
}
```

其中 `ocf_history_check_second_chance(addr, size)` 为二次准入接口函数，用于执行二次准入检查，具体如下：

```c++
/**
 * @brief 执行二次准入检查
 * 
 * 检查请求中所有4K块在历史记录中的命中情况，并根据命中率决定是否允许缓存。
 * 如果命中率低于阈值，则将请求的所有4K块添加到历史记录中，并返回false表示不应缓存。
 * 
 * @param req OCF请求对象
 * @return bool true表示通过二次准入检查，应该被缓存；false表示未通过，应直接PT
 */
bool ocf_history_check_second_chance(uint64_t addr, uint64_t size)
```

二次准入具体逻辑参考 `second_addmission.cpp` [注释](https://github.com/lingwu-hb/otae/blob/main/feature/second_addmission.cpp#L344)。

### 模型训练部分

[参考代码](https://github.com/lingwu-hb/otae/blob/main/process_traces.py#L197)

```python
# 执行模型训练
train_cmd = ["python", "trainer.py", "-t", trace_name]
result = subprocess.run(train_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
```

调用 `python trainer.py -t trace_name ` 进行模型训练，生成模型文件。

* 核心代码如下（trainer.py）

```python
print(f"Starting model training for trace '{trace_name}'...")
# 80% 数据用于训练，20%数据用于测试，一次性加载
X_train, y_train, X_test, y_test = trainer.LoadWebData()
# 对模型进行训练
print(f"Training data size: {X_train.shape[0]} rows, {X_train.shape[1]} features")
clf_result = trainer.Train(X_train, y_train)
# 获取最佳模型
clf = clf_result.best_estimator_
print("Best model parameters:", clf_result.best_params_)
# 将返回模型参数保存到 model目录
trainer.SaveModel(clf, model_file)
# 使用测试数据评估模型
if X_test.shape[0] > 0:
```

执行完成之后，会生成决策树模型文件，可以参考该文件后续的决策树模型示例图。

### 决策树OCF应用

主要内容参考 `classifier` 文件夹

* 决策树初始化

生成的决策树目前以文件的形式保存，需要解析模型文件，在 c++ 中生成对应的模型，从而应用。

> 参考 Classifier::Init 和 决策树模型文件结构

```c++
/**
 * 初始化分类器，加载预训练的决策树模型
 * @param modelPath 模型文件的目录路径
 * @param readyTime 每个模型的就绪时间数组，如果为0表示该模型尚未训练完成
 */
void Classifier::Init()
```

* 具体应用

OCF 中调用 `IsOneTimeAccess` 函数，用于代替二次准入的 `ocf_history_check_second_chance` 函数。根据该函数返回的布尔类型，对该请求采取是否允许其准入操作。

* IsOneTimeAccess 逻辑

`bool isOneTimeAccess = classifier.IsStreamFile(features, timeStamp, request_id);` 调用 classifier.IsStreamFile 文件判断

该文件最终调用决策树的决策函数，根据决策树的各个节点进行判断，最后得出结果。

```c++
int ResponseNode(std::vector<double> &features) {
    int p = 0;
    int predictor = predictor_[p];
    while( predictor >= 0){
      if (features[predictor] < threshold_[p]){
        p = left_[p];
      }
      else{
        p = right_[p];
      }
      predictor = predictor_[p];
    }
    return p;
  }
```



# 原 otae 代码分析

## **解析特征**

**代码中目前只是从文件中提取，并没有涉及到在线计算特征。**

### Trace 原文件示例：

```shell
TimeStamp - 时间戳，格式为 [YYYY-MM-DD HH:MM:SS]
Uin1 - 访问者用户ID（长整型）
Uin2 - 图片所有者用户ID（长整型）
ClientIp - 客户端IP地址
Url - 访问的URL
UrlParameter - URL参数
Host - 主机名
ClientType - 客户端类型（PC/PHONE/UNKNOWN）
FlowNo - 流编号
HttpLen - HTTP请求长度
BodyLen - 响应体大小（图片大小）
ProcessTime - 处理时间
Errno - 错误码
Refer - 引用页面
Resolution - 图片分辨率代码（a/b/c/l/m/o）
Spec - 图片规格代码（0/5）
UploadTime - 图片上传时间（Unix时间戳）
PhotoId - 图片唯一标识符
IsHitMemcache - 是否命中内存缓存（1/0）
IsHitTdcache - 是否命中TD缓存（1/0）
-----------
[2018-05-10 08:15:23]	1234567	7654321	192.168.1.101	/photo/view	id=12345&size=m0	photos.example.com	PC	98765	1024	512000	150	0	https://www.example.com/gallery	a	0	1525912800	photo_12345	1	0
[2018-05-10 08:16:45]	0	8765432	203.0.113.25	/photo/view	id=23456&size=b5	photos.example.com	PHONE	98766	2048	128000	120	0	https://m.example.com/gallery	b	5	1525826400	photo_23456	0	1
[2018-05-10 08:17:12]	2345678	8765432	198.51.100.75	/photo/view	id=34567&size=c0	photos.example.com	PC	98767	4096	1048576	200	0	https://www.example.com/profile	c	0	1525739200	photo_34567	1	0
[2018-05-10 08:18:30]	3456789	9876543	192.0.2.100	/photo/view	id=45678&size=l5	photos.example.com	PHONE	98768	1536	256000	180	0	https://m.example.com/feed	l	5	1525652800	photo_45678	0	0
[2018-05-10 08:19:05]	0	1357924	203.0.113.50	/photo/view	id=56789&size=m0	photos.example.com	UNKNOWN	98769	768	64000	100	0	https://www.example.com/search	m	0	1525566400	photo_56789	1	1
```



### 特征计算逻辑

extract_feature.cpp：输入上述 Trace 原文件，然后提取出特征，并保存到特征文件中。

特征计算逻辑简单使用哈希表保存历史访问，然后直接在哈希表中进行检索。

```c++
class FileAccessTimeAnalyzer{
  unordered_map<std::string, time_t> actime_map; // 文件名到上次访问时间的映射
  public:
  /**
   * 获取并更新文件的访问时间
   * @param name 文件名
   * @param now 当前时间戳
   * @param atime [输出] 上次访问时间
   * @return 如果文件之前被访问过返回true，否则返回false
   */
  bool GetAccessTime(std::string name, time_t now, time_t &atime){
    auto it = actime_map.find(name);
    bool ret = false;

    if (it != actime_map.end()){
      atime = it->second; 
      // TODO：need to update it->second @hb
      return true;
    }
    // 更新访问时间
    actime_map[name] = now; 
    
    return ret;
  }   
};
```



### 特征文件示例

extract_feature.cpp 生成特征文件示例如下所示：

```shell
照片 ID
#照片类型（photo_t枚举值）：a0=1, a5=2, b0=3...等
访问时间戳（Unix时间戳）
照片大小（字节数，来自BodyLen）
#所有者的好友数量
#所有者图片的平均浏览量
#上传时间距今（当前访问时间 - 上传时间）
文件上次访问距今（当前访问时间 - 上次访问时间）
#用户上次访问距今（当前访问时间 - 用户上次访问时间）
#客户端类型（PC=0, PHONE=1, UNKNOWN=2）
每分钟平均访问量
#是否为Web访问（Uin1是否为0，1表示是，0表示否）
#照片分辨率（ra=1, rb=2, rc=3...等）
#照片规格（s0=1, s5=2）
文件访问频率（该文件被访问的次数）
#预留特征1（当前未使用，设为0）
#预留特征2（当前未使用，设为0）
---------
photo_12345	1	1525939200	512000	157	23.5	86400	3600	7200	0	1250	1	1	1	1	0	0
photo_23456	3	1525939320	128000	42	12.1	172800	1800	3600	1	1250	0	2	2	2	0	0
photo_34567	5	1525939440	1048576	89	45.7	43200	600	1200	0	1250	1	3	1	1	0	0
photo_45678	8	1525939560	256000	63	18.2	129600	7200	14400	1	1250	0	4	2	3	0	0
photo_56789	10	1525939680	64000	28	8.5	259200	3600	7200	2	1250	1	5	1	1	0	0
```

**带 # 符号的特征表示 OCF 无法提供的特征**



## **决策树模型**

* python 对模型进行训练，训练完成将模型参数保存到 modelfile 文件中
* c++ 提取 modelfile 文件，对决策树模型进行重构，利用重构的决策树进行预测

modelfile 示例，训练过程使用 saveModel 生成类似对应文件进行保存，初始化模型时，加载该文件，利用树结构进行推理

```sh
# 类别权重（类别0和类别1的权重）
    2.5         1.0
# 节点数量
         7
# 特征索引（-1表示叶子节点）:表示每个节点使用哪个特征
         6         2         4        -1        -1        -1        -1
# 阈值：每个节点的分裂阈值
  1000.000   500.000    50.000     0.000     0.000     0.000     0.000
# 左子节点索引（-1表示无子节点）
         1         3         5        -1        -1        -1        -1
# 右子节点索引（-1表示无子节点）
         2         4         6        -1        -1        -1        -1
# 负类（非一次性访问）概率
    0.4500    0.7800    0.3200    0.9500    0.6000    0.2500    0.1500
# 正类（一次性访问）概率
    0.5500    0.2200    0.6800    0.0500    0.4000    0.7500    0.8500
```

```c++
// 通过 modelfile 文件生成决策树的部分流程
class DecisionTree{
public:
  DecisionTree(){};
  void Init(std::istream &is, int num_classes = 2){
    num_classes_ = num_classes;
    //get num of nodes
    is >> num_nodes_;
    predictor_.resize(num_nodes_);
    for (int i = 0 ; i < num_nodes_; ++i){
      is >> predictor_[i];
    }
    threshold_.resize(num_nodes_);
    for (int i = 0 ; i < num_nodes_; ++i){
      is >> threshold_[i];
    }
    left_.resize(num_nodes_);
    for (int i = 0 ; i < num_nodes_; ++i){
      is >> left_[i];
    }
    right_.resize(num_nodes_);
    for (int i = 0 ; i < num_nodes_; ++i){
      is >> right_[i];
    }
  }
```

