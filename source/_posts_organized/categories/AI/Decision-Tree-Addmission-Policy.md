---
title: Decision Tree Addmission Policy
date: 2025-05-16 16:06:20
categories:
- [AI]
- [data storage]
tags:
- 决策树准入

---

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.6%2B-blue)](https://www.python.org/)
[![C++](https://img.shields.io/badge/C%2B%2B-11%2B-blue)](https://isocpp.org/)

# OTAE: Decision Tree Based Cache Admission Policy

## 📋 Overview

[项目地址](https://github.com/lingwu-hb/otae)
OTAE (Optimized Tree-based Admission Engine) is an intelligent cache admission policy that uses decision trees to predict whether a cache block should be admitted to the cache. It aims to improve cache efficiency by learning from historical access patterns and making smart admission decisions.

## 🗂️ Project Structure

```
otae/
├── feature/                   # Feature extraction
│   ├── second_addmission.h    # Secondary admission logic header
│   ├── second_addmission.cpp  # Secondary admission implementation
│   ├── extract_features.cpp   # Feature extraction implementation
│   └── extract_features.exe   # Feature extraction executable
├── train/                     # Model training
│   ├── trainer.py            # Model training script
│   └── dataset.py            # Dataset processing script
├── classifier/               # Classifier implementation
│   ├── decision_tree.h      # Decision tree header
│   ├── classifier_das.cpp   # DAS classifier implementation
│   ├── classifier.h         # Classifier header
│   └── classifier.cpp       # Classifier implementation
├── process_traces.py        # Trace processing automation script
├── data/                    # Data directory
│   ├── web_3/              # Web trace data
│   └── model/              # Trained model storage
└── doc/                    # Documentation
```

## 🔄 Workflow

### 1. Feature Extraction

The feature extraction process is automated through `process_traces.py`. It extracts seven key features from the trace files:

```python
# Feature extraction command
extract_cmd = ["extract_features.exe" if platform.system() == "Windows" else "./extract_features", trace_filename]
```

#### Extracted Features:

1. Request address - The starting address of the IO request
2. Request size - The size of the IO request in bytes
3. Access timestamp - The time when the request was made
4. Reuse time - Time since last access (in microseconds)
5. Average requests per minute - Current request rate
6. Access frequency - Number of times this address has been accessed
7. Time decay weight - Exponential decay factor based on reuse time: `exp(-λ * reuse_time_s)`

The time decay weight is calculated using the following formula:

```cpp
float lambda = 0.05;  // Decay rate parameter
float e_lambda_reuse_time = exp(-lambda * reuse_time_s);
```

This weight gives higher importance to recent accesses and gradually reduces the influence of older accesses.

### 2. Tag Generation

The tag generation process uses the secondary admission policy implemented in `second_addmission.cpp`. Here's how it works:

```cpp
bool ocf_history_check_second_chance(uint64_t addr, uint64_t size) {
    // Calculate page-aligned addresses
    uint64_t start_addr = PAGE_ALIGN_DOWN(addr);
    uint64_t end_addr = PAGE_ALIGN_DOWN(addr + size - 1);
    uint64_t total_pages = PAGES_IN_REQ(start_addr, end_addr);
    uint64_t hit_pages = 0;

    // Check hit rate in history
    for (uint64_t curr_addr = start_addr; curr_addr <= end_addr; curr_addr += PAGE_SIZE) {
        if (ocf_history_hash_find(curr_addr)) {
            hit_pages++;
        }
    }
    
    // If hit rate is below threshold, add to history and return false
    if ((float)hit_pages / total_pages < HISTORY_HIT_RATIO_THRESHOLD) {
        // Add all pages to history
        for (uint64_t curr_addr = start_addr; curr_addr <= end_addr; curr_addr += PAGE_SIZE) {
            ocf_history_hash_add_addr(curr_addr);
        }
        return false;  // Tag as 1 (one-time access)
    }

    return true;  // Tag as 0 (should be cached)
}
```

The process uses a hash table with LRU (Least Recently Used) eviction policy to maintain access history. Key components:

1. **History Management**:
   - Uses a hash table to store access history
   - Implements LRU eviction when history exceeds capacity
   - Dynamically resizes based on load factor

2. **Hit Rate Calculation**:
   - Calculates hit rate for all 4K pages in the request
   - Uses `HISTORY_HIT_RATIO_THRESHOLD` to determine caching decision
   - Tags requests as 1 (one-time) or 0 (should be cached)

### 3. Model Training

The training process uses scikit-learn's DecisionTreeClassifier with the following implementation:

```python
def Train(self, X, y):
    # Define parameter grid for optimization
    param = {
        'class_weight': [{0:2,1:1}, {0:2.5,1:1}, {0:1.5, 1:1}],
        'max_leaf_nodes': [30, 50, 70, 100],
        'max_depth': [4, 6, 8]
    }

    # Create F-beta scorer with dynamic beta based on cache capacity
    fscore = make_scorer(fbeta_score, beta=self.Beta(self.cap), pos_label=1)
    
    # Initialize and train the model
    clf = GridSearchCV(
        DecisionTreeClassifier(criterion='entropy'),
        param_grid=param,
        scoring=fscore,
        cv=5,
        refit=True
    )
    clf.fit(X, y)
    return clf
```

Key aspects of the training process:

1. **Data Preparation**:
   - 80% training, 20% testing split
   - Feature normalization and preprocessing
   - Handling class imbalance through class weights

2. **Model Optimization**:
   - Grid search for optimal parameters
   - Cross-validation to prevent overfitting
   - Dynamic beta parameter based on cache capacity

3. **Model Evaluation**:
   - F-beta score as primary metric
   - Recall and precision trade-off
   - Feature importance analysis

### 4. Model Application

The trained model is applied in OCF through the following implementation:

```cpp
class DecisionTree {
public:
    int ResponseNode(std::vector<double> &features) {
        int p = 0;
        int predictor = predictor_[p];
        while(predictor >= 0) {
            if (features[predictor] < threshold_[p]) {
                p = left_[p];
            } else {
                p = right_[p];
            }
            predictor = predictor_[p];
        }
        return p;
    }
};
```

The application process includes:

1. **Model Initialization**:
   - Load model parameters from file
   - Initialize decision tree structure
   - Set up feature preprocessing

2. **Feature Extraction**:
   - Extract real-time features from requests
   - Apply time decay weighting
   - Normalize features if needed

3. **Prediction**:
   - Traverse decision tree
   - Apply thresholds at each node
   - Return final prediction

4. **Cache Decision**:
   - Use prediction to determine admission
   - Update history if needed
   - Apply caching policy

## 🚀 Future Improvements

### 1. Space-based Feature Enhancement

| Feature               | Calculation                                  | Purpose                       |
| --------------------- | -------------------------------------------- | ----------------------------- |
| Offset Heat Bucket    | Bucket `addr` by 1MB, count access frequency | Identify hot/cold regions     |
| Spatial Jump Distance | `abs(current_addr - last_addr) / size`       | Detect random access patterns |
| Alignment Feature     | `addr % 4096`                                | Identify unaligned accesses   |

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
