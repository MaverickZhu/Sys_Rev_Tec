# AI功能性能指标设计

## 1. 概述

本文档定义了政府文档系统AI功能的性能指标体系，包括响应时间、准确性、可用性、资源利用率等关键指标，为系统监控、优化和SLA制定提供依据。

## 2. 指标分类体系

### 2.1 指标层次结构

```
AI性能指标体系
├── 核心业务指标
│   ├── 搜索性能指标
│   ├── 文档处理指标
│   └── 智能分析指标
├── 技术性能指标
│   ├── 响应时间指标
│   ├── 吞吐量指标
│   └── 资源利用率指标
├── 质量指标
│   ├── 准确性指标
│   ├── 可靠性指标
│   └── 用户满意度指标
└── 运维指标
    ├── 可用性指标
    ├── 错误率指标
    └── 容量指标
```

### 2.2 指标优先级

| 优先级 | 指标类型 | 重要性 | 监控频率 |
|--------|----------|--------|----------|
| P0 | 系统可用性 | 极高 | 实时 |
| P1 | 核心功能响应时间 | 高 | 实时 |
| P2 | 搜索准确性 | 高 | 每小时 |
| P3 | 资源利用率 | 中 | 每5分钟 |
| P4 | 用户满意度 | 中 | 每日 |

## 3. 核心业务指标

### 3.1 搜索性能指标

#### 3.1.1 响应时间指标

```yaml
搜索响应时间:
  指标名称: search_response_time
  描述: 从接收搜索请求到返回结果的时间
  单位: 毫秒(ms)
  目标值:
    语义搜索: ≤ 500ms (P95)
    关键词搜索: ≤ 200ms (P95)
    混合搜索: ≤ 800ms (P95)
    智能问答: ≤ 2000ms (P95)
  告警阈值:
    警告: > 目标值的150%
    严重: > 目标值的200%
  监控维度:
    - 搜索类型
    - 查询复杂度
    - 结果数量
    - 用户部门
```

#### 3.1.2 搜索准确性指标

```yaml
搜索准确性:
  指标名称: search_accuracy
  描述: 搜索结果的相关性和准确性
  单位: 百分比(%)
  计算方法:
    - 相关性评分: 基于用户点击和反馈
    - NDCG@10: 归一化折损累积增益
    - MRR: 平均倒数排名
  目标值:
    语义搜索相关性: ≥ 85%
    关键词搜索精确率: ≥ 90%
    问答准确性: ≥ 80%
  评估方法:
    - 人工标注样本评估
    - 用户反馈统计
    - A/B测试对比
```

#### 3.1.3 搜索覆盖率指标

```yaml
搜索覆盖率:
  指标名称: search_coverage
  描述: 搜索能够找到相关文档的比例
  单位: 百分比(%)
  计算公式: (找到相关文档的查询数 / 总查询数) × 100%
  目标值: ≥ 95%
  监控维度:
    - 文档类型
    - 查询类型
    - 时间范围
```

### 3.2 文档处理指标

#### 3.2.1 文档处理速度

```yaml
文档处理速度:
  指标名称: document_processing_speed
  描述: 文档从上传到完成向量化的处理速度
  单位: 文档数/小时
  目标值:
    PDF文档: ≥ 100文档/小时
    Word文档: ≥ 150文档/小时
    图片文档: ≥ 50文档/小时
  监控维度:
    - 文档类型
    - 文档大小
    - 处理复杂度
```

#### 3.2.2 OCR准确率

```yaml
OCR准确率:
  指标名称: ocr_accuracy
  描述: OCR文字识别的准确性
  单位: 百分比(%)
  计算方法:
    - 字符级准确率
    - 词级准确率
    - 行级准确率
  目标值:
    印刷体文档: ≥ 98%
    手写体文档: ≥ 85%
    低质量扫描: ≥ 80%
  评估样本: 每月随机抽取100个文档
```

#### 3.2.3 向量化质量

```yaml
向量化质量:
  指标名称: vectorization_quality
  描述: 文档向量化的质量和一致性
  评估指标:
    - 向量相似度分布
    - 聚类质量评分
    - 语义保持度
  目标值:
    相似文档向量相似度: ≥ 0.8
    不同文档向量相似度: ≤ 0.3
    语义保持度: ≥ 90%
```

### 3.3 智能分析指标

#### 3.3.1 分析准确性

```yaml
智能分析准确性:
  指标名称: analysis_accuracy
  描述: AI分析结果的准确性
  分析类型:
    文档分类准确率: ≥ 95%
    关键信息提取准确率: ≥ 90%
    情感分析准确率: ≥ 85%
    摘要质量评分: ≥ 4.0/5.0
  评估方法:
    - 专家评审
    - 对比验证
    - 用户反馈
```

#### 3.3.2 分析完整性

```yaml
分析完整性:
  指标名称: analysis_completeness
  描述: 分析结果的完整性和覆盖度
  单位: 百分比(%)
  计算方法:
    - 关键要素识别完整度
    - 分析维度覆盖度
    - 结论逻辑完整性
  目标值: ≥ 90%
```

## 4. 技术性能指标

### 4.1 系统响应时间

#### 4.1.1 API响应时间分布

```yaml
API响应时间:
  指标名称: api_response_time
  统计维度:
    P50: 50%请求的响应时间
    P90: 90%请求的响应时间
    P95: 95%请求的响应时间
    P99: 99%请求的响应时间
  目标值:
    文档上传API:
      P95: ≤ 1000ms
      P99: ≤ 2000ms
    搜索API:
      P95: ≤ 500ms
      P99: ≤ 1000ms
    分析API:
      P95: ≤ 3000ms
      P99: ≤ 5000ms
```

#### 4.1.2 数据库查询性能

```yaml
数据库查询性能:
  指标名称: db_query_performance
  监控指标:
    向量搜索查询时间:
      P95: ≤ 100ms
      P99: ≤ 200ms
    全文搜索查询时间:
      P95: ≤ 50ms
      P99: ≤ 100ms
    复杂聚合查询时间:
      P95: ≤ 500ms
      P99: ≤ 1000ms
  慢查询阈值: > 1000ms
```

### 4.2 吞吐量指标

#### 4.2.1 请求处理能力

```yaml
请求处理能力:
  指标名称: request_throughput
  单位: 请求数/秒(RPS)
  目标值:
    搜索请求: ≥ 100 RPS
    文档上传: ≥ 10 RPS
    分析请求: ≥ 20 RPS
  峰值处理能力:
    搜索请求: ≥ 500 RPS
    文档上传: ≥ 50 RPS
  监控维度:
    - 请求类型
    - 时间段
    - 用户并发数
```

#### 4.2.2 数据处理吞吐量

```yaml
数据处理吞吐量:
  指标名称: data_processing_throughput
  文档处理:
    单位: 文档数/小时
    目标值: ≥ 1000文档/小时
  向量化处理:
    单位: 向量数/秒
    目标值: ≥ 50向量/秒
  批量分析:
    单位: 批次/小时
    目标值: ≥ 100批次/小时
```

### 4.3 资源利用率

#### 4.3.1 计算资源利用率

```yaml
计算资源利用率:
  CPU利用率:
    正常范围: 30% - 70%
    告警阈值: > 80%
    严重告警: > 90%
  内存利用率:
    正常范围: 40% - 75%
    告警阈值: > 85%
    严重告警: > 95%
  GPU利用率(如适用):
    正常范围: 50% - 80%
    告警阈值: > 90%
  监控频率: 每分钟
```

#### 4.3.2 存储资源利用率

```yaml
存储资源利用率:
  磁盘使用率:
    正常范围: < 70%
    告警阈值: > 80%
    严重告警: > 90%
  数据库存储:
    向量数据增长率: 监控每日增长
    索引大小比例: < 30%
  缓存命中率:
    Redis缓存: ≥ 80%
    应用缓存: ≥ 70%
```

#### 4.3.3 网络资源利用率

```yaml
网络资源利用率:
  带宽利用率:
    正常范围: < 60%
    告警阈值: > 80%
  网络延迟:
    内网延迟: < 5ms
    外网API调用: < 100ms
  连接数:
    数据库连接池: 监控使用率
    HTTP连接: 监控并发数
```

## 5. 质量指标

### 5.1 准确性指标

#### 5.1.1 搜索结果准确性

```yaml
搜索结果准确性:
  相关性评分:
    计算方法: 用户点击率 + 停留时间 + 反馈评分
    目标值: ≥ 4.0/5.0
    评估周期: 每周
  
  精确率(Precision):
    计算公式: 相关结果数 / 返回结果总数
    目标值: ≥ 85%
  
  召回率(Recall):
    计算公式: 相关结果数 / 相关文档总数
    目标值: ≥ 80%
  
  F1分数:
    计算公式: 2 × (精确率 × 召回率) / (精确率 + 召回率)
    目标值: ≥ 82%
```

#### 5.1.2 AI分析准确性

```yaml
AI分析准确性:
  文档分类:
    多分类准确率: ≥ 95%
    混淆矩阵分析: 每月评估
  
  实体识别:
    命名实体识别准确率: ≥ 90%
    关键信息提取准确率: ≥ 88%
  
  文本摘要:
    ROUGE-L分数: ≥ 0.6
    人工评估分数: ≥ 4.0/5.0
  
  情感分析:
    情感分类准确率: ≥ 85%
    情感强度预测误差: ≤ 0.2
```

### 5.2 可靠性指标

#### 5.2.1 系统稳定性

```yaml
系统稳定性:
  平均故障间隔时间(MTBF):
    目标值: ≥ 720小时(30天)
    计算周期: 季度
  
  平均修复时间(MTTR):
    目标值: ≤ 30分钟
    包含: 检测时间 + 响应时间 + 修复时间
  
  系统可用性:
    目标值: ≥ 99.9%
    计算公式: (总时间 - 故障时间) / 总时间
    统计周期: 月度
```

#### 5.2.2 数据一致性

```yaml
数据一致性:
  向量数据一致性:
    检查频率: 每日
    一致性比例: ≥ 99.9%
  
  搜索索引一致性:
    检查频率: 每小时
    同步延迟: ≤ 5分钟
  
  缓存数据一致性:
    检查频率: 实时
    不一致率: ≤ 0.1%
```

### 5.3 用户满意度指标

#### 5.3.1 用户体验指标

```yaml
用户体验指标:
  用户满意度评分:
    收集方式: 应用内评分 + 定期调研
    目标值: ≥ 4.2/5.0
    评估周期: 月度
  
  任务完成率:
    搜索任务完成率: ≥ 90%
    文档处理任务完成率: ≥ 95%
  
  用户留存率:
    日活跃用户留存: ≥ 80%
    周活跃用户留存: ≥ 70%
    月活跃用户留存: ≥ 60%
```

#### 5.3.2 功能使用情况

```yaml
功能使用情况:
  功能使用率:
    搜索功能: 监控使用频次
    分析功能: 监控使用深度
    导出功能: 监控使用场景
  
  用户行为分析:
    平均会话时长: 监控趋势
    页面跳出率: ≤ 30%
    功能转化率: ≥ 60%
```

## 6. 运维指标

### 6.1 可用性指标

#### 6.1.1 服务可用性

```yaml
服务可用性:
  整体系统可用性:
    SLA目标: 99.9%
    计算方式: 基于健康检查
    监控频率: 每30秒
  
  核心服务可用性:
    搜索服务: 99.95%
    文档处理服务: 99.9%
    AI分析服务: 99.8%
  
  依赖服务可用性:
    数据库服务: 99.95%
    缓存服务: 99.9%
    Ollama服务: 99.8%
```

#### 6.1.2 健康检查指标

```yaml
健康检查指标:
  健康检查响应时间:
    目标值: ≤ 100ms
    告警阈值: > 500ms
  
  健康检查成功率:
    目标值: ≥ 99.9%
    统计周期: 小时
  
  服务依赖检查:
    数据库连接: 实时监控
    外部API可用性: 每分钟检查
    文件系统状态: 每5分钟检查
```

### 6.2 错误率指标

#### 6.2.1 系统错误率

```yaml
系统错误率:
  HTTP错误率:
    4xx错误率: ≤ 5%
    5xx错误率: ≤ 1%
    超时错误率: ≤ 0.5%
  
  业务错误率:
    搜索失败率: ≤ 1%
    文档处理失败率: ≤ 2%
    AI分析失败率: ≤ 3%
  
  数据错误率:
    数据损坏率: ≤ 0.01%
    数据丢失率: ≤ 0.001%
```

#### 6.2.2 错误分类统计

```yaml
错误分类统计:
  按错误类型:
    - 网络错误
    - 数据库错误
    - AI模型错误
    - 业务逻辑错误
  
  按严重程度:
    - 致命错误(Critical)
    - 严重错误(Major)
    - 一般错误(Minor)
    - 警告(Warning)
  
  错误趋势分析:
    - 错误增长率
    - 错误分布变化
    - 错误修复效率
```

### 6.3 容量指标

#### 6.3.1 存储容量

```yaml
存储容量:
  文档存储:
    当前使用量: 监控实时值
    增长率: 每月统计
    预计满容时间: 基于趋势预测
  
  向量数据存储:
    向量数量: 实时监控
    存储大小: 每日统计
    索引大小: 每日统计
  
  日志存储:
    日志大小: 每日统计
    保留策略: 30天滚动
    压缩比例: 监控压缩效果
```

#### 6.3.2 处理能力容量

```yaml
处理能力容量:
  并发处理能力:
    最大并发用户数: 压测验证
    最大并发请求数: 实时监控
    队列处理能力: 监控队列长度
  
  数据处理容量:
    文档处理队列: 监控积压情况
    向量化处理能力: 每小时统计
    分析任务处理能力: 每小时统计
```

## 7. 监控实现

### 7.1 指标收集架构

```yaml
监控架构:
  数据收集层:
    - 应用指标: Prometheus + 自定义指标
    - 系统指标: Node Exporter
    - 数据库指标: PostgreSQL Exporter
    - 业务指标: 自定义收集器
  
  数据存储层:
    - 时序数据: Prometheus + InfluxDB
    - 日志数据: ELK Stack
    - 业务数据: PostgreSQL
  
  可视化层:
    - 实时监控: Grafana
    - 业务报表: 自定义Dashboard
    - 告警通知: AlertManager
```

### 7.2 指标收集实现

```python
# app/monitoring/metrics_collector.py
from prometheus_client import Counter, Histogram, Gauge, Summary
from typing import Dict, Any
import time
import asyncio
from functools import wraps

class AIMetricsCollector:
    def __init__(self):
        # 搜索性能指标
        self.search_requests_total = Counter(
            'search_requests_total',
            'Total search requests',
            ['search_type', 'status']
        )
        
        self.search_duration = Histogram(
            'search_duration_seconds',
            'Search request duration',
            ['search_type'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
        )
        
        self.search_accuracy = Gauge(
            'search_accuracy_score',
            'Search accuracy score',
            ['search_type']
        )
        
        # 文档处理指标
        self.document_processing_total = Counter(
            'document_processing_total',
            'Total documents processed',
            ['doc_type', 'status']
        )
        
        self.document_processing_duration = Histogram(
            'document_processing_duration_seconds',
            'Document processing duration',
            ['doc_type'],
            buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 300.0]
        )
        
        # AI分析指标
        self.ai_analysis_requests = Counter(
            'ai_analysis_requests_total',
            'Total AI analysis requests',
            ['analysis_type', 'status']
        )
        
        self.ai_analysis_accuracy = Gauge(
            'ai_analysis_accuracy_score',
            'AI analysis accuracy score',
            ['analysis_type']
        )
        
        # 系统资源指标
        self.cpu_usage = Gauge(
            'cpu_usage_percent',
            'CPU usage percentage'
        )
        
        self.memory_usage = Gauge(
            'memory_usage_percent',
            'Memory usage percentage'
        )
        
        self.active_connections = Gauge(
            'active_connections_total',
            'Active database connections'
        )
    
    def record_search_request(self, search_type: str, duration: float, status: str):
        """记录搜索请求指标"""
        self.search_requests_total.labels(
            search_type=search_type, 
            status=status
        ).inc()
        
        self.search_duration.labels(
            search_type=search_type
        ).observe(duration)
    
    def update_search_accuracy(self, search_type: str, accuracy: float):
        """更新搜索准确性指标"""
        self.search_accuracy.labels(
            search_type=search_type
        ).set(accuracy)
    
    def record_document_processing(self, doc_type: str, duration: float, status: str):
        """记录文档处理指标"""
        self.document_processing_total.labels(
            doc_type=doc_type,
            status=status
        ).inc()
        
        self.document_processing_duration.labels(
            doc_type=doc_type
        ).observe(duration)
    
    def record_ai_analysis(self, analysis_type: str, status: str):
        """记录AI分析指标"""
        self.ai_analysis_requests.labels(
            analysis_type=analysis_type,
            status=status
        ).inc()
    
    def update_system_metrics(self, cpu_percent: float, memory_percent: float, connections: int):
        """更新系统资源指标"""
        self.cpu_usage.set(cpu_percent)
        self.memory_usage.set(memory_percent)
        self.active_connections.set(connections)

# 全局指标收集器实例
metrics_collector = AIMetricsCollector()

# 装饰器：自动记录函数执行指标
def monitor_performance(metric_type: str, labels: Dict[str, str] = None):
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                
                if metric_type == "search":
                    search_type = labels.get("search_type", "unknown")
                    metrics_collector.record_search_request(
                        search_type, duration, status
                    )
                elif metric_type == "document":
                    doc_type = labels.get("doc_type", "unknown")
                    metrics_collector.record_document_processing(
                        doc_type, duration, status
                    )
                elif metric_type == "analysis":
                    analysis_type = labels.get("analysis_type", "unknown")
                    metrics_collector.record_ai_analysis(
                        analysis_type, status
                    )
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                # 同步版本的指标记录逻辑
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator
```

### 7.3 业务指标计算

```python
# app/monitoring/business_metrics.py
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import asyncio

class BusinessMetricsCalculator:
    def __init__(self, db: Session):
        self.db = db
    
    async def calculate_search_accuracy(self, time_range: int = 24) -> Dict[str, float]:
        """计算搜索准确性指标"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=time_range)
        
        # 查询搜索历史和用户反馈
        query = text("""
            SELECT 
                sh.search_type,
                AVG(CASE 
                    WHEN sf.rating IS NOT NULL THEN sf.rating
                    WHEN sh.click_count > 0 THEN 4.0
                    ELSE 2.0
                END) as avg_rating,
                COUNT(*) as total_searches
            FROM search_history sh
            LEFT JOIN search_feedback sf ON sh.id = sf.search_id
            WHERE sh.created_at BETWEEN :start_time AND :end_time
            GROUP BY sh.search_type
        """)
        
        results = self.db.execute(query, {
            "start_time": start_time,
            "end_time": end_time
        }).fetchall()
        
        accuracy_scores = {}
        for search_type, avg_rating, total_searches in results:
            # 将评分转换为准确性百分比
            accuracy_scores[search_type] = (avg_rating / 5.0) * 100
        
        return accuracy_scores
    
    async def calculate_processing_metrics(self) -> Dict[str, Any]:
        """计算文档处理指标"""
        # 计算处理速度
        query = text("""
            SELECT 
                document_type,
                COUNT(*) as processed_count,
                AVG(EXTRACT(EPOCH FROM (updated_at - created_at))) as avg_processing_time
            FROM documents
            WHERE status = 'processed'
            AND created_at >= NOW() - INTERVAL '24 hours'
            GROUP BY document_type
        """)
        
        results = self.db.execute(query).fetchall()
        
        processing_metrics = {}
        for doc_type, count, avg_time in results:
            processing_metrics[doc_type] = {
                "processed_count": count,
                "avg_processing_time": avg_time,
                "processing_speed": count / 24 if count > 0 else 0  # 文档/小时
            }
        
        return processing_metrics
    
    async def calculate_system_health(self) -> Dict[str, Any]:
        """计算系统健康指标"""
        # 计算错误率
        error_query = text("""
            SELECT 
                COUNT(CASE WHEN status_code >= 400 THEN 1 END) as error_count,
                COUNT(*) as total_requests
            FROM api_logs
            WHERE created_at >= NOW() - INTERVAL '1 hour'
        """)
        
        error_result = self.db.execute(error_query).fetchone()
        error_rate = (error_result[0] / error_result[1] * 100) if error_result[1] > 0 else 0
        
        # 计算平均响应时间
        response_time_query = text("""
            SELECT 
                endpoint,
                AVG(response_time_ms) as avg_response_time,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time_ms) as p95_response_time
            FROM api_logs
            WHERE created_at >= NOW() - INTERVAL '1 hour'
            GROUP BY endpoint
        """)
        
        response_times = {}
        for endpoint, avg_time, p95_time in self.db.execute(response_time_query).fetchall():
            response_times[endpoint] = {
                "avg_response_time": avg_time,
                "p95_response_time": p95_time
            }
        
        return {
            "error_rate": error_rate,
            "response_times": response_times
        }
    
    async def generate_daily_report(self) -> Dict[str, Any]:
        """生成每日指标报告"""
        search_accuracy = await self.calculate_search_accuracy(24)
        processing_metrics = await self.calculate_processing_metrics()
        system_health = await self.calculate_system_health()
        
        return {
            "date": datetime.now().date().isoformat(),
            "search_accuracy": search_accuracy,
            "processing_metrics": processing_metrics,
            "system_health": system_health,
            "summary": {
                "overall_health": "good" if system_health["error_rate"] < 5 else "warning",
                "avg_search_accuracy": sum(search_accuracy.values()) / len(search_accuracy) if search_accuracy else 0,
                "total_documents_processed": sum(m["processed_count"] for m in processing_metrics.values())
            }
        }
```

### 7.4 告警规则配置

```yaml
# monitoring/alert_rules.yml
groups:
  - name: ai_system_alerts
    rules:
      # 搜索性能告警
      - alert: SearchResponseTimeHigh
        expr: histogram_quantile(0.95, search_duration_seconds) > 2.0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "搜索响应时间过高"
          description: "95%的搜索请求响应时间超过2秒"
      
      - alert: SearchErrorRateHigh
        expr: rate(search_requests_total{status="error"}[5m]) / rate(search_requests_total[5m]) > 0.05
        for: 3m
        labels:
          severity: critical
        annotations:
          summary: "搜索错误率过高"
          description: "搜索错误率超过5%"
      
      # 系统资源告警
      - alert: HighCPUUsage
        expr: cpu_usage_percent > 80
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "CPU使用率过高"
          description: "CPU使用率持续超过80%"
      
      - alert: HighMemoryUsage
        expr: memory_usage_percent > 85
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "内存使用率过高"
          description: "内存使用率超过85%"
      
      # 业务指标告警
      - alert: SearchAccuracyLow
        expr: search_accuracy_score < 80
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: "搜索准确性下降"
          description: "搜索准确性低于80%"
      
      - alert: DocumentProcessingBacklog
        expr: document_processing_queue_size > 1000
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "文档处理积压"
          description: "文档处理队列积压超过1000个文档"
```

## 8. 性能基准测试

### 8.1 基准测试场景

```yaml
基准测试场景:
  搜索性能测试:
    场景1: 单用户搜索
      - 并发用户: 1
      - 搜索类型: 语义搜索
      - 查询复杂度: 简单
      - 期望响应时间: < 300ms
    
    场景2: 多用户并发搜索
      - 并发用户: 50
      - 搜索类型: 混合搜索
      - 查询复杂度: 中等
      - 期望响应时间: < 800ms
    
    场景3: 高负载搜索
      - 并发用户: 200
      - 搜索类型: 各种类型
      - 查询复杂度: 复杂
      - 期望响应时间: < 2000ms
  
  文档处理测试:
    场景1: 批量文档上传
      - 文档数量: 100
      - 文档大小: 1-5MB
      - 期望处理时间: < 10分钟
    
    场景2: 大文档处理
      - 文档数量: 10
      - 文档大小: 10-50MB
      - 期望处理时间: < 30分钟
  
  系统压力测试:
    场景1: 混合负载测试
      - 搜索请求: 100 RPS
      - 文档上传: 10 RPS
      - 分析请求: 20 RPS
      - 持续时间: 1小时
```

### 8.2 性能测试脚本

```python
# tests/performance/load_test.py
import asyncio
import aiohttp
import time
import random
from typing import List, Dict
import json

class PerformanceTestRunner:
    def __init__(self, base_url: str, auth_token: str):
        self.base_url = base_url
        self.auth_token = auth_token
        self.results = []
    
    async def run_search_load_test(
        self, 
        concurrent_users: int, 
        duration_seconds: int
    ) -> Dict[str, float]:
        """运行搜索负载测试"""
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        # 测试查询列表
        test_queries = [
            "政府采购法规",
            "招标投标流程",
            "财政预算管理",
            "公务员管理条例",
            "行政审批制度"
        ]
        
        async def user_session(session: aiohttp.ClientSession, user_id: int):
            request_count = 0
            error_count = 0
            total_response_time = 0
            
            while time.time() < end_time:
                query = random.choice(test_queries)
                search_type = random.choice(["semantic", "keyword", "hybrid"])
                
                request_start = time.time()
                try:
                    async with session.post(
                        f"{self.base_url}/api/v1/search/{search_type}",
                        json={"query": query, "limit": 10},
                        headers={"Authorization": f"Bearer {self.auth_token}"}
                    ) as response:
                        await response.json()
                        
                        if response.status == 200:
                            request_count += 1
                        else:
                            error_count += 1
                        
                        response_time = time.time() - request_start
                        total_response_time += response_time
                        
                except Exception as e:
                    error_count += 1
                
                # 随机等待时间，模拟真实用户行为
                await asyncio.sleep(random.uniform(1, 5))
            
            return {
                "user_id": user_id,
                "request_count": request_count,
                "error_count": error_count,
                "avg_response_time": total_response_time / request_count if request_count > 0 else 0
            }
        
        # 创建并发用户会话
        async with aiohttp.ClientSession() as session:
            tasks = [
                user_session(session, i) 
                for i in range(concurrent_users)
            ]
            
            user_results = await asyncio.gather(*tasks)
        
        # 汇总结果
        total_requests = sum(r["request_count"] for r in user_results)
        total_errors = sum(r["error_count"] for r in user_results)
        avg_response_times = [r["avg_response_time"] for r in user_results if r["avg_response_time"] > 0]
        
        return {
            "concurrent_users": concurrent_users,
            "duration_seconds": duration_seconds,
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate": total_errors / (total_requests + total_errors) if (total_requests + total_errors) > 0 else 0,
            "requests_per_second": total_requests / duration_seconds,
            "avg_response_time": sum(avg_response_times) / len(avg_response_times) if avg_response_times else 0,
            "max_response_time": max(avg_response_times) if avg_response_times else 0,
            "min_response_time": min(avg_response_times) if avg_response_times else 0
        }
    
    async def run_document_processing_test(
        self, 
        document_count: int, 
        document_size_mb: float
    ) -> Dict[str, float]:
        """运行文档处理性能测试"""
        # 生成测试文档
        test_documents = self._generate_test_documents(document_count, document_size_mb)
        
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for doc in test_documents:
                task = self._upload_document(session, doc)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        
        successful_uploads = sum(1 for r in results if not isinstance(r, Exception))
        failed_uploads = len(results) - successful_uploads
        
        return {
            "document_count": document_count,
            "successful_uploads": successful_uploads,
            "failed_uploads": failed_uploads,
            "total_time_seconds": end_time - start_time,
            "documents_per_second": successful_uploads / (end_time - start_time),
            "success_rate": successful_uploads / document_count
        }
    
    def _generate_test_documents(self, count: int, size_mb: float) -> List[Dict]:
        """生成测试文档"""
        documents = []
        content_size = int(size_mb * 1024 * 1024 / 2)  # 假设每个字符2字节
        
        for i in range(count):
            content = "测试文档内容 " * (content_size // 10)
            documents.append({
                "title": f"测试文档_{i+1}",
                "content": content,
                "document_type": "测试",
                "department": "测试部门"
            })
        
        return documents
    
    async def _upload_document(self, session: aiohttp.ClientSession, document: Dict):
        """上传单个文档"""
        try:
            async with session.post(
                f"{self.base_url}/api/v1/documents/upload",
                json=document,
                headers={"Authorization": f"Bearer {self.auth_token}"}
            ) as response:
                return await response.json()
        except Exception as e:
            raise e

# 运行性能测试
async def main():
    test_runner = PerformanceTestRunner(
        base_url="http://localhost:8000",
        auth_token="your_test_token"
    )
    
    # 搜索负载测试
    print("运行搜索负载测试...")
    search_results = await test_runner.run_search_load_test(
        concurrent_users=50,
        duration_seconds=300  # 5分钟
    )
    print(f"搜索测试结果: {json.dumps(search_results, indent=2)}")
    
    # 文档处理测试
    print("运行文档处理测试...")
    doc_results = await test_runner.run_document_processing_test(
        document_count=100,
        document_size_mb=2.0
    )
    print(f"文档处理测试结果: {json.dumps(doc_results, indent=2)}")

if __name__ == "__main__":
    asyncio.run(main())
```

## 9. SLA定义

### 9.1 服务等级协议

```yaml
SLA定义:
  可用性承诺:
    系统整体可用性: 99.9%
    核心搜索功能: 99.95%
    文档处理功能: 99.8%
    计算方式: 月度统计
    
  性能承诺:
    搜索响应时间:
      - 语义搜索: P95 ≤ 500ms
      - 关键词搜索: P95 ≤ 200ms
      - 智能问答: P95 ≤ 2000ms
    
    文档处理时间:
      - 小文档(<5MB): ≤ 30秒
      - 中文档(5-20MB): ≤ 2分钟
      - 大文档(>20MB): ≤ 10分钟
    
    系统吞吐量:
      - 搜索请求: ≥ 100 RPS
      - 文档上传: ≥ 10 RPS
      - 并发用户: ≥ 500
  
  质量承诺:
    搜索准确性: ≥ 85%
    文档处理成功率: ≥ 98%
    数据完整性: 99.99%
  
  支持承诺:
    故障响应时间: ≤ 15分钟
    故障修复时间: ≤ 2小时
    计划维护通知: 提前48小时
```

### 9.2 违约补偿机制

```yaml
补偿机制:
  可用性违约:
    99.0% - 99.9%: 服务费用10%补偿
    95.0% - 99.0%: 服务费用25%补偿
    < 95.0%: 服务费用50%补偿
  
  性能违约:
    响应时间超标: 按超标时长比例补偿
    吞吐量不足: 按影响用户数比例补偿
  
  数据违约:
    数据丢失: 全额补偿 + 数据恢复费用
    数据泄露: 按影响范围确定补偿
```

## 10. 总结

本AI功能性能指标设计文档建立了完整的指标体系：

### 10.1 指标覆盖范围
- **业务指标**: 搜索性能、文档处理、智能分析
- **技术指标**: 响应时间、吞吐量、资源利用率
- **质量指标**: 准确性、可靠性、用户满意度
- **运维指标**: 可用性、错误率、容量规划

### 10.2 监控实现
- **多层次监控**: 应用层、系统层、业务层
- **实时告警**: 基于阈值的智能告警
- **性能分析**: 趋势分析和容量预测
- **自动化测试**: 持续的性能基准测试

### 10.3 持续改进
- **定期评估**: 月度指标回顾和优化
- **基准更新**: 根据业务发展调整目标
- **技术升级**: 基于监控数据的技术优化
- **用户反馈**: 结合用户体验持续改进

该指标体系将为AI功能的稳定运行、性能优化和服务质量提供全面的监控和保障。