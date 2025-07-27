#!/bin/bash
# AI服务启动脚本

set -e

echo "=== AI服务启动中 ==="
echo "时间: $(date)"
echo "Python版本: $(python --version)"
echo "工作目录: $(pwd)"

# 等待数据库就绪
echo "等待数据库连接..."
until python -c "import psycopg2; psycopg2.connect('$DATABASE_URL')" 2>/dev/null; do
    echo "数据库未就绪，等待5秒..."
    sleep 5
done
echo "数据库连接成功!"

# 等待Redis就绪
echo "等待Redis连接..."
until python -c "import redis; redis.from_url('$REDIS_URL').ping()" 2>/dev/null; do
    echo "Redis未就绪，等待3秒..."
    sleep 3
done
echo "Redis连接成功!"

# 检查向量扩展
echo "检查pgvector扩展..."
python -c "
import psycopg2
conn = psycopg2.connect('$DATABASE_URL')
cur = conn.cursor()
cur.execute(\"SELECT extname FROM pg_extension WHERE extname = 'vector';\")
result = cur.fetchone()
if result:
    print('pgvector扩展已安装:', result[0])
else:
    print('警告: pgvector扩展未找到')
conn.close()
"

# 检查Ollama连接（可选）
if [ ! -z "$OLLAMA_BASE_URL" ]; then
    echo "检查Ollama连接: $OLLAMA_BASE_URL"
    if curl -s "$OLLAMA_BASE_URL/api/tags" > /dev/null 2>&1; then
        echo "Ollama连接成功!"
        echo "可用模型:"
        curl -s "$OLLAMA_BASE_URL/api/tags" | python -c "import sys, json; data=json.load(sys.stdin); [print(f'  - {m[\"name\"]}') for m in data.get('models', [])]"
    else
        echo "警告: 无法连接到Ollama服务，将使用备用AI服务"
    fi
fi

# 初始化向量数据库表（如果需要）
echo "初始化向量数据库..."
python -c "
import sys
sys.path.append('/app')
from ai_service.database import init_vector_database
init_vector_database()
print('向量数据库初始化完成')
"

# 预热模型（可选）
echo "预热AI模型..."
python -c "
import sys
sys.path.append('/app')
from ai_service.services.vector_service import VectorService
vector_service = VectorService()
vector_service.warmup()
print('AI模型预热完成')
" || echo "模型预热跳过（可能是首次启动）"

echo "=== AI服务启动完成 ==="
echo "服务端口: 8001"
echo "健康检查: http://localhost:8001/health"
echo "API文档: http://localhost:8001/docs"
echo ""

# 执行传入的命令
exec "$@"