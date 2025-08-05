# 常见问题解答 (FAQ)

本文档收集了政府采购项目审查分析系统使用过程中的常见问题和解决方案。

## 📋 目录

- [安装和部署](#安装和部署)
- [系统配置](#系统配置)
- [功能使用](#功能使用)
- [性能优化](#性能优化)
- [故障排除](#故障排除)
- [安全相关](#安全相关)
- [API使用](#api使用)
- [AI功能](#ai功能)

---

## 安装和部署

### Q1: 系统支持哪些操作系统？

**A:** 系统支持以下操作系统：
- **Linux**: Ubuntu 20.04+, CentOS 8+, RHEL 8+
- **Windows**: Windows 10/11, Windows Server 2019+
- **macOS**: macOS 10.15+

推荐使用Linux系统进行生产部署。

### Q2: 最低硬件配置要求是什么？

**A:** 最低配置要求：
- **CPU**: 2核心
- **内存**: 4GB RAM
- **存储**: 50GB 可用空间
- **网络**: 100Mbps

推荐配置：
- **CPU**: 4核心以上
- **内存**: 8GB+ RAM
- **存储**: 100GB+ SSD
- **网络**: 1Gbps

### Q3: Docker部署失败怎么办？

**A:** 常见解决方案：

1. **检查Docker版本**：
   ```bash
   docker --version
   docker-compose --version
   ```
   确保Docker版本 ≥ 20.10，Docker Compose版本 ≥ 1.29

2. **检查端口占用**：
   ```bash
   netstat -tlnp | grep :8000
   netstat -tlnp | grep :5432
   ```

3. **查看容器日志**：
   ```bash
   docker-compose logs app
   docker-compose logs postgres
   ```

4. **重新构建镜像**：
   ```bash
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

### Q4: 数据库连接失败怎么解决？

**A:** 检查以下几个方面：

1. **数据库服务状态**：
   ```bash
   sudo systemctl status postgresql
   ```

2. **连接参数**：
   检查 `.env` 文件中的数据库配置：
   ```
   DATABASE_URL=postgresql://username:password@localhost:5432/database_name
   ```

3. **防火墙设置**：
   ```bash
   sudo ufw allow 5432/tcp
   ```

4. **PostgreSQL配置**：
   编辑 `postgresql.conf` 和 `pg_hba.conf` 文件

---

## 系统配置

### Q5: 如何修改系统配置？

**A:** 系统配置主要通过以下文件管理：

1. **环境变量** (`.env`)：
   ```bash
   # 应用配置
   APP_NAME="系统审查技术"
   DEBUG=false
   SECRET_KEY="your-secret-key"
   
   # 数据库配置
   DATABASE_URL="postgresql://..."
   
   # Redis配置
   REDIS_URL="redis://localhost:6379/0"
   ```

2. **应用配置** (`app/core/config.py`)：
   修改后需要重启服务

3. **AI服务配置** (`ai_service/config.py`)：
   配置AI模型和向量数据库

### Q6: 如何配置HTTPS？

**A:** HTTPS配置步骤：

1. **获取SSL证书**：
   ```bash
   # 使用Let's Encrypt
   sudo certbot --nginx -d your-domain.com
   ```

2. **配置Nginx**：
   ```nginx
   server {
       listen 443 ssl http2;
       server_name your-domain.com;
       
       ssl_certificate /path/to/certificate.crt;
       ssl_certificate_key /path/to/private.key;
       
       # 其他配置...
   }
   ```

3. **更新应用配置**：
   ```bash
   FORCE_HTTPS=true
   SECURE_SSL_REDIRECT=true
   ```

### Q7: 如何配置邮件服务？

**A:** 邮件服务配置：

1. **SMTP配置** (`.env`)：
   ```bash
   SMTP_HOST="smtp.gmail.com"
   SMTP_PORT=587
   SMTP_USER="your-email@gmail.com"
   SMTP_PASSWORD="your-app-password"
   SMTP_TLS=true
   ```

2. **测试邮件发送**：
   ```bash
   python scripts/test_email.py
   ```

---

## 功能使用

### Q8: 如何上传大文件？

**A:** 大文件上传配置：

1. **调整上传限制**：
   ```python
   # app/core/config.py
   MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100MB
   ```

2. **Nginx配置**：
   ```nginx
   client_max_body_size 100M;
   ```

3. **使用分块上传**：
   前端使用分块上传功能，支持断点续传

### Q9: OCR识别准确率低怎么办？

**A:** 提高OCR准确率的方法：

1. **图片预处理**：
   - 确保图片清晰度足够
   - 调整图片对比度和亮度
   - 去除噪点和倾斜

2. **选择合适的OCR模型**：
   ```python
   # 中文文档推荐使用
   OCR_MODEL = "ch_ppocr_v3"
   ```

3. **调整识别参数**：
   ```python
   ocr_config = {
       "det_limit_side_len": 960,
       "det_limit_type": "max",
       "rec_batch_num": 6
   }
   ```

### Q10: 如何批量处理文档？

**A:** 批量处理功能：

1. **使用批量上传API**：
   ```bash
   curl -X POST "http://localhost:8000/api/v1/documents/batch-upload/1" \
     -H "Authorization: Bearer <token>" \
     -F "files=@file1.pdf" \
     -F "files=@file2.pdf"
   ```

2. **使用脚本批量处理**：
   ```bash
   python scripts/batch_process.py --project-id 1 --folder /path/to/documents
   ```

3. **监控处理进度**：
   通过WebSocket或轮询API获取处理状态

---

## 性能优化

### Q11: 系统响应慢怎么优化？

**A:** 性能优化建议：

1. **数据库优化**：
   ```sql
   -- 创建索引
   CREATE INDEX idx_documents_project_id ON documents(project_id);
   CREATE INDEX idx_documents_created_at ON documents(created_at);
   
   -- 定期维护
   VACUUM ANALYZE;
   ```

2. **缓存优化**：
   ```python
   # 启用Redis缓存
   CACHE_ENABLED = True
   CACHE_TTL = 3600  # 1小时
   ```

3. **应用优化**：
   - 增加worker进程数
   - 启用异步处理
   - 使用连接池

### Q12: 内存使用过高怎么办？

**A:** 内存优化方案：

1. **调整worker配置**：
   ```bash
   # 减少worker数量
   uvicorn app.main:app --workers 2
   ```

2. **优化AI模型加载**：
   ```python
   # 延迟加载模型
   LAZY_LOAD_MODELS = True
   # 使用模型量化
   MODEL_QUANTIZATION = True
   ```

3. **配置内存限制**：
   ```bash
   # Docker容器内存限制
   docker run -m 4g sys-rev-tec:latest
   ```

---

## 故障排除

### Q13: 服务启动失败怎么排查？

**A:** 故障排查步骤：

1. **查看日志**：
   ```bash
   # 应用日志
   tail -f logs/app.log
   
   # 系统服务日志
   sudo journalctl -u sys-rev-tec -f
   ```

2. **检查依赖服务**：
   ```bash
   # 检查PostgreSQL
   sudo systemctl status postgresql
   
   # 检查Redis
   sudo systemctl status redis
   ```

3. **验证配置文件**：
   ```bash
   # 检查配置语法
   python -c "from app.core.config import settings; print('配置正确')"
   ```

### Q14: AI服务无响应怎么处理？

**A:** AI服务故障处理：

1. **检查AI服务状态**：
   ```bash
   curl http://localhost:8001/health
   ```

2. **重启AI服务**：
   ```bash
   sudo systemctl restart sys-rev-tec-ai
   ```

3. **检查模型文件**：
   ```bash
   ls -la ai_service/models/
   ```

4. **查看GPU使用情况**（如果使用GPU）：
   ```bash
   nvidia-smi
   ```

### Q15: 数据库连接池耗尽怎么解决？

**A:** 连接池优化：

1. **调整连接池配置**：
   ```python
   # app/db/session.py
   engine = create_engine(
       DATABASE_URL,
       pool_size=20,
       max_overflow=30,
       pool_timeout=30,
       pool_recycle=3600
   )
   ```

2. **检查连接泄漏**：
   ```sql
   SELECT count(*) FROM pg_stat_activity WHERE state = 'active';
   ```

3. **使用连接池监控**：
   ```python
   # 添加连接池监控
   from sqlalchemy import event
   
   @event.listens_for(engine, "connect")
   def receive_connect(dbapi_connection, connection_record):
       logger.info("数据库连接建立")
   ```

---

## 安全相关

### Q16: 如何加强系统安全？

**A:** 安全加固建议：

1. **更新密钥**：
   ```bash
   # 生成新的SECRET_KEY
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **启用HTTPS**：
   强制使用HTTPS访问

3. **配置防火墙**：
   ```bash
   sudo ufw enable
   sudo ufw allow ssh
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   ```

4. **定期更新依赖**：
   ```bash
   pip list --outdated
   pip install -U package_name
   ```

### Q17: 如何备份和恢复数据？

**A:** 数据备份方案：

1. **数据库备份**：
   ```bash
   # 创建备份
   pg_dump -h localhost -U sys_user -d sys_rev_tech > backup.sql
   
   # 恢复备份
   psql -h localhost -U sys_user -d sys_rev_tech < backup.sql
   ```

2. **文件备份**：
   ```bash
   # 备份上传文件
   tar -czf uploads_backup.tar.gz uploads/
   
   # 恢复文件
   tar -xzf uploads_backup.tar.gz
   ```

3. **自动备份脚本**：
   ```bash
   # 添加到crontab
   0 2 * * * /opt/sys_rev_tec/scripts/backup.sh
   ```

---

## API使用

### Q18: 如何获取API访问令牌？

**A:** 获取访问令牌：

1. **用户登录**：
   ```bash
   curl -X POST "http://localhost:8000/api/v1/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "password"}'
   ```

2. **响应示例**：
   ```json
   {
     "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
     "token_type": "bearer",
     "expires_in": 3600
   }
   ```

3. **使用令牌**：
   ```bash
   curl -H "Authorization: Bearer <access_token>" \
     "http://localhost:8000/api/v1/projects/"
   ```

### Q19: API请求频率限制是多少？

**A:** API频率限制：

- **普通用户**: 100请求/分钟
- **管理员**: 1000请求/分钟
- **系统API**: 无限制

超出限制会返回429状态码。

### Q20: 如何处理API错误？

**A:** 常见API错误处理：

1. **401 未授权**：
   - 检查访问令牌是否有效
   - 重新登录获取新令牌

2. **403 禁止访问**：
   - 检查用户权限
   - 联系管理员分配权限

3. **422 参数错误**：
   - 检查请求参数格式
   - 参考API文档修正参数

4. **500 服务器错误**：
   - 查看服务器日志
   - 联系技术支持

---

## AI功能

### Q21: AI分析结果不准确怎么办？

**A:** 提高AI分析准确性：

1. **优化输入数据**：
   - 确保文档质量良好
   - 提供完整的上下文信息
   - 使用标准格式的文档

2. **调整模型参数**：
   ```python
   # ai_service/config.py
   AI_CONFIG = {
       "confidence_threshold": 0.8,
       "max_tokens": 2048,
       "temperature": 0.1
   }
   ```

3. **使用专业模型**：
   针对特定领域使用专门训练的模型

### Q22: 如何自定义AI分析规则？

**A:** 自定义分析规则：

1. **配置规则文件**：
   ```json
   {
     "rules": [
       {
         "name": "价格异常检测",
         "pattern": "价格.*异常",
         "severity": "high",
         "action": "alert"
       }
     ]
   }
   ```

2. **通过API添加规则**：
   ```bash
   curl -X POST "http://localhost:8001/api/v1/ai/rules" \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"name": "自定义规则", "pattern": "..."}'
   ```

### Q23: AI服务占用资源过多怎么优化？

**A:** AI服务资源优化：

1. **模型量化**：
   ```python
   # 启用模型量化
   MODEL_QUANTIZATION = True
   QUANTIZATION_BITS = 8
   ```

2. **批处理优化**：
   ```python
   # 调整批处理大小
   BATCH_SIZE = 4
   MAX_CONCURRENT_REQUESTS = 2
   ```

3. **使用GPU加速**：
   ```python
   # 启用GPU
   USE_GPU = True
   GPU_MEMORY_FRACTION = 0.5
   ```

---

## 📞 获取帮助

如果以上FAQ没有解决您的问题，请通过以下方式获取帮助：

### 技术支持
- **邮箱**: support@example.com
- **电话**: +86-xxx-xxxx-xxxx
- **工作时间**: 周一至周五 9:00-18:00

### 在线资源
- **官方文档**: [https://docs.example.com](https://docs.example.com)
- **GitHub Issues**: [https://github.com/org/Sys_Rev_Tec/issues](https://github.com/org/Sys_Rev_Tec/issues)
- **社区论坛**: [https://forum.example.com](https://forum.example.com)

### 紧急联系
- **紧急热线**: +86-xxx-xxxx-xxxx (24小时)
- **紧急邮箱**: emergency@example.com

---

**文档版本**: 1.0.0  
**最后更新**: 2025-01-04  
**维护团队**: 技术支持团队

> 💡 **提示**: 本FAQ会定期更新，建议收藏此页面以获取最新信息。如有新问题或建议，欢迎反馈给我们。