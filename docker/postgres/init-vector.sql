-- pgvector 扩展初始化脚本
-- 此脚本在数据库初始化时自动执行，用于配置向量数据库功能

-- 创建 pgvector 扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 验证扩展安装
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';

-- 创建向量相关的数据表

-- 文档向量表
CREATE TABLE IF NOT EXISTS document_vectors (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL DEFAULT 0,
    content TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    embedding vector(1024),  -- 支持 bge-m3 模型的 1024 维向量
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- 约束
    CONSTRAINT unique_document_chunk UNIQUE (document_id, chunk_index),
    CONSTRAINT unique_content_hash UNIQUE (content_hash)
);

-- 向量搜索历史表
CREATE TABLE IF NOT EXISTS vector_search_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    query_text TEXT NOT NULL,
    query_embedding vector(1024),
    search_type VARCHAR(50) NOT NULL DEFAULT 'semantic',
    results_count INTEGER DEFAULT 0,
    response_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- 索引
    INDEX idx_search_user_time (user_id, created_at),
    INDEX idx_search_type (search_type)
);

-- 向量索引统计表
CREATE TABLE IF NOT EXISTS vector_index_stats (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    index_name VARCHAR(100) NOT NULL,
    total_vectors INTEGER DEFAULT 0,
    avg_query_time_ms DECIMAL(10,2),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- 约束
    CONSTRAINT unique_table_index UNIQUE (table_name, index_name)
);

-- 创建向量索引
-- HNSW 索引用于快速近似最近邻搜索
CREATE INDEX IF NOT EXISTS idx_document_vectors_embedding_hnsw 
ON document_vectors USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- IVFFlat 索引作为备选方案
CREATE INDEX IF NOT EXISTS idx_document_vectors_embedding_ivfflat 
ON document_vectors USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- 查询历史的向量索引
CREATE INDEX IF NOT EXISTS idx_search_history_embedding_hnsw 
ON vector_search_history USING hnsw (query_embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- 创建其他必要的索引
CREATE INDEX IF NOT EXISTS idx_document_vectors_document_id ON document_vectors (document_id);
CREATE INDEX IF NOT EXISTS idx_document_vectors_created_at ON document_vectors (created_at);
CREATE INDEX IF NOT EXISTS idx_document_vectors_metadata ON document_vectors USING GIN (metadata);

-- 创建更新时间触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为 document_vectors 表添加更新时间触发器
CREATE TRIGGER update_document_vectors_updated_at 
    BEFORE UPDATE ON document_vectors 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- 创建向量相似度搜索函数
CREATE OR REPLACE FUNCTION search_similar_documents(
    query_embedding vector(1024),
    similarity_threshold FLOAT DEFAULT 0.7,
    max_results INTEGER DEFAULT 10
)
RETURNS TABLE (
    document_id INTEGER,
    chunk_index INTEGER,
    content TEXT,
    similarity FLOAT,
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        dv.document_id,
        dv.chunk_index,
        dv.content,
        1 - (dv.embedding <=> query_embedding) AS similarity,
        dv.metadata
    FROM document_vectors dv
    WHERE 1 - (dv.embedding <=> query_embedding) >= similarity_threshold
    ORDER BY dv.embedding <=> query_embedding
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

-- 创建向量统计更新函数
CREATE OR REPLACE FUNCTION update_vector_stats()
RETURNS void AS $$
BEGIN
    -- 更新文档向量统计
    INSERT INTO vector_index_stats (table_name, index_name, total_vectors, last_updated)
    VALUES ('document_vectors', 'idx_document_vectors_embedding_hnsw', 
            (SELECT COUNT(*) FROM document_vectors WHERE embedding IS NOT NULL), 
            CURRENT_TIMESTAMP)
    ON CONFLICT (table_name, index_name) 
    DO UPDATE SET 
        total_vectors = EXCLUDED.total_vectors,
        last_updated = EXCLUDED.last_updated;
        
    -- 更新搜索历史统计
    INSERT INTO vector_index_stats (table_name, index_name, total_vectors, last_updated)
    VALUES ('vector_search_history', 'idx_search_history_embedding_hnsw', 
            (SELECT COUNT(*) FROM vector_search_history WHERE query_embedding IS NOT NULL), 
            CURRENT_TIMESTAMP)
    ON CONFLICT (table_name, index_name) 
    DO UPDATE SET 
        total_vectors = EXCLUDED.total_vectors,
        last_updated = EXCLUDED.last_updated;
END;
$$ LANGUAGE plpgsql;

-- 创建定期统计更新的调度（需要 pg_cron 扩展，可选）
-- SELECT cron.schedule('update-vector-stats', '0 */6 * * *', 'SELECT update_vector_stats();');

-- 插入初始统计数据
SELECT update_vector_stats();

-- 验证向量功能
DO $$
BEGIN
    -- 测试向量操作
    PERFORM '[1,2,3]'::vector;
    RAISE NOTICE 'pgvector 扩展安装成功，向量功能可用';
EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'pgvector 扩展安装失败: %', SQLERRM;
END
$$;

-- 输出配置信息
SELECT 
    'pgvector 数据库配置完成' AS status,
    version() AS postgres_version,
    (SELECT extversion FROM pg_extension WHERE extname = 'vector') AS vector_version,
    CURRENT_TIMESTAMP AS configured_at;