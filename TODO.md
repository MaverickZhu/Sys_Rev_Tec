# 待办事项 (TODO)

## 明日计划

1.  **完善API文档和测试**:
    *   [x] 为所有API端点添加详细的 `summary` 和 `description`。
    *   [ ] 使用 `pytest` 编写单元测试和集成测试，确保核心功能（用户认证、项目CRUD）的稳定性。

2.  **前端集成准备**:
    *   [x] 配置静态文件服务，以处理前端应用的 `index.html` 和其他静态资源（如 `/@vite/client`）。
    *   [x] 考虑将FastAPI与一个简单的前端框架（如Vue或React）集成，或至少提供一个基本的API交互页面。

3.  **实现核心业务逻辑**:
    *   [x] 在 `app/crud` 和 `app/services` 目录中实现更复杂的业务逻辑，例如，基于角色的访问控制 (RBAC)。
    *   [x] 完善 `Project` 模型的CRUD操作，并添加相关API端点。

## 数据库模型和CRUD操作
- [x] 完善项目模型（Project）的字段定义
- [x] 创建问题跟踪模型（Issue）
- [x] 创建项目比对模型（ProjectComparison）
- [x] 实现文档模型（Document）的完整CRUD操作
- [x] 实现OCR结果模型（OCRResult）的CRUD操作
- [ ] 优化数据库查询性能

4.  **配置和部署**:
    *   [ ] 整理并完善项目文档，包括 `README.md` 中的部署指南。
    *   [ ] 研究并确定生产环境的部署方案（例如，使用Docker和Gunicorn）。

5.  **代码审查和重构**:
    *   [ ] 审查现有代码，确保遵循代码风格和最佳实践。
    *   [ ] 对重复代码或可优化的部分进行重构。