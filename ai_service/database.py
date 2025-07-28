"""
AI服务数据库连接管理
管理向量数据库连接和操作
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

import asyncpg
from asyncpg import Pool

from ai_service.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# 全局连接池
_pool: Optional[Pool] = None


class VectorDatabase:
    """向量数据库操作类"""

    def __init__(self, pool: Pool):
        self.pool = pool

    async def close(self):
        """关闭连接池"""
        if self.pool:
            await self.pool.close()

    @asynccontextmanager
    async def get_connection(self):
        """获取数据库连接"""
        async with self.pool.acquire() as conn:
            yield conn

    async def execute_query(self, query: str, *args) -> List[Dict[str, Any]]:
        """执行查询"""
        async with self.get_connection() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]

    async def execute_command(self, command: str, *args) -> str:
        """执行命令"""
        async with self.get_connection() as conn:
            return await conn.execute(command, *args)

    async def insert_document_vector(
        self,
        document_id: str,
        content: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None,
        chunk_index: int = 0,
    ) -> int:
        """插入文档向量"""
        query = """
            INSERT INTO document_vectors (
                document_id, content, embedding, metadata, chunk_index
            ) VALUES ($1, $2, $3, $4, $5)
            RETURNING id
        """

        # 转换embedding为pgvector格式
        embedding_str = f"[{','.join(map(str, embedding))}]"

        async with self.get_connection() as conn:
            row = await conn.fetchrow(
                query, document_id, content, embedding_str, metadata or {}, chunk_index
            )
            return row["id"]

    async def batch_insert_document_vectors(
        self, vectors: List[Dict[str, Any]]
    ) -> List[int]:
        """批量插入文档向量"""
        if not vectors:
            return []

        query = """
            INSERT INTO document_vectors (
                document_id, content, embedding, metadata, chunk_index
            ) VALUES ($1, $2, $3, $4, $5)
            RETURNING id
        """

        async with self.get_connection() as conn:
            # 准备批量数据
            batch_data = []
            for vector in vectors:
                embedding_str = f"[{','.join(map(str, vector['embedding']))}"
                batch_data.append(
                    (
                        vector["document_id"],
                        vector["content"],
                        embedding_str,
                        vector.get("metadata", {}),
                        vector.get("chunk_index", 0),
                    )
                )

            # 执行批量插入
            await conn.fetch(query, *batch_data[0])
            ids = []

            for data in batch_data:
                row = await conn.fetchrow(query, *data)
                ids.append(row["id"])

            return ids

    async def search_similar_vectors(
        self,
        query_embedding: List[float],
        limit: int = 10,
        similarity_threshold: float = 0.7,
        document_ids: Optional[List[str]] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """搜索相似向量"""
        # 构建查询
        query_parts = [
            "SELECT id, document_id, content, metadata, chunk_index,",
            "       1 - (embedding <=> $1::vector) AS similarity",
            "FROM document_vectors",
            "WHERE 1 - (embedding <=> $1::vector) >= $2",
        ]

        params = [f"[{','.join(map(str, query_embedding))}]", similarity_threshold]
        param_count = 2

        # 添加文档ID过滤
        if document_ids:
            param_count += 1
            query_parts.append(f"AND document_id = ANY(${param_count})")
            params.append(document_ids)

        # 添加元数据过滤
        if metadata_filter:
            for key, value in metadata_filter.items():
                param_count += 1
                query_parts.append(f"AND metadata->>'{key}' = ${param_count}")
                params.append(str(value))

        # 添加排序和限制
        query_parts.extend(["ORDER BY embedding <=> $1::vector", f"LIMIT {limit}"])

        query = " ".join(query_parts)

        async with self.get_connection() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]

    async def search_by_text(
        self,
        search_text: str,
        limit: int = 10,
        document_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """基于文本搜索"""
        query_parts = [
            "SELECT id, document_id, content, metadata, chunk_index,",
            "       ts_rank(to_tsvector('english', content), "
            "plainto_tsquery('english', $1)) AS rank",
            "FROM document_vectors",
            "WHERE to_tsvector('english', content) @@ "
            "plainto_tsquery('english', $1)",
        ]

        params = [search_text]

        # 添加文档ID过滤
        if document_ids:
            query_parts.append("AND document_id = ANY($2)")
            params.append(document_ids)

        # 添加排序和限制
        query_parts.extend(["ORDER BY rank DESC", f"LIMIT {limit}"])

        query = " ".join(query_parts)

        async with self.get_connection() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]

    async def hybrid_search(
        self,
        query_embedding: List[float],
        search_text: str,
        limit: int = 10,
        alpha: float = 0.7,
        similarity_threshold: float = 0.5,
        document_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """混合搜索（向量 + 文本）"""
        query_parts = [
            "WITH vector_search AS (",
            "    SELECT id, document_id, content, metadata, chunk_index,",
            "           1 - (embedding <=> $1::vector) AS vector_similarity",
            "    FROM document_vectors",
            "    WHERE 1 - (embedding <=> $1::vector) >= $3",
        ]

        params = [
            f"[{','.join(map(str, query_embedding))}]",
            search_text,
            similarity_threshold,
        ]
        param_count = 3

        # 添加文档ID过滤到向量搜索
        if document_ids:
            param_count += 1
            query_parts.append(f"    AND document_id = ANY(${param_count})")
            params.append(document_ids)

        query_parts.extend(
            [
                "),",
                "text_search AS (",
                "    SELECT id, document_id, content, metadata, chunk_index,",
                "           ts_rank(to_tsvector('english', content), "
                "plainto_tsquery('english', $2)) AS text_rank",
                "    FROM document_vectors",
                "    WHERE to_tsvector('english', content) @@ "
                "plainto_tsquery('english', $2)",
            ]
        )

        # 添加文档ID过滤到文本搜索
        if document_ids:
            query_parts.append(f"    AND document_id = ANY(${param_count})")

        query_parts.extend(
            [
                ")",
                "SELECT COALESCE(v.id, t.id) as id,",
                "       COALESCE(v.document_id, t.document_id) " "as document_id,",
                "       COALESCE(v.content, t.content) as content,",
                "       COALESCE(v.metadata, t.metadata) as metadata,",
                "       COALESCE(v.chunk_index, t.chunk_index) " "as chunk_index,",
                "       COALESCE(v.vector_similarity, 0) " "as vector_similarity,",
                "       COALESCE(t.text_rank, 0) as text_rank,",
                f"       ({alpha} * COALESCE(v.vector_similarity, 0) + "
                f"{1 - alpha} * COALESCE(t.text_rank, 0)) as hybrid_score",
                "FROM vector_search v",
                "FULL OUTER JOIN text_search t ON v.id = t.id",
                "ORDER BY hybrid_score DESC",
                f"LIMIT {limit}",
            ]
        )

        query = " ".join(query_parts)

        async with self.get_connection() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]

    async def get_document_vectors(self, document_id: str) -> List[Dict[str, Any]]:
        """获取文档的所有向量"""
        query = """
            SELECT id, document_id, content, metadata, chunk_index,
                   created_at, updated_at
            FROM document_vectors
            WHERE document_id = $1
            ORDER BY chunk_index
        """

        async with self.get_connection() as conn:
            rows = await conn.fetch(query, document_id)
            return [dict(row) for row in rows]

    async def delete_document_vectors(self, document_id: str) -> int:
        """删除文档的所有向量"""
        query = "DELETE FROM document_vectors WHERE document_id = $1"

        async with self.get_connection() as conn:
            result = await conn.execute(query, document_id)
            # 解析删除的行数
            return int(result.split()[-1])

    async def update_document_vector(
        self,
        vector_id: int,
        content: Optional[str] = None,
        embedding: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """更新文档向量"""
        updates = []
        params = []
        param_count = 0

        if content is not None:
            param_count += 1
            updates.append(f"content = ${param_count}")
            params.append(content)

        if embedding is not None:
            param_count += 1
            updates.append(f"embedding = ${param_count}::vector")
            params.append(f"[{','.join(map(str, embedding))}]")

        if metadata is not None:
            param_count += 1
            updates.append(f"metadata = ${param_count}")
            params.append(metadata)

        if not updates:
            return False

        param_count += 1
        updates.append("updated_at = NOW()")
        params.append(vector_id)

        query = f"""
            UPDATE document_vectors
            SET {", ".join(updates)}
            WHERE id = ${param_count}
        """

        async with self.get_connection() as conn:
            result = await conn.execute(query, *params)
            return int(result.split()[-1]) > 0

    async def log_search_history(
        self,
        query_text: str,
        search_type: str,
        results_count: int,
        execution_time_ms: float,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """记录搜索历史"""
        query = """
            INSERT INTO vector_search_history (
                query_text, search_type, results_count,
                execution_time_ms, user_id, metadata
            ) VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
        """

        async with self.get_connection() as conn:
            row = await conn.fetchrow(
                query,
                query_text,
                search_type,
                results_count,
                execution_time_ms,
                user_id,
                metadata or {},
            )
            return row["id"]

    async def update_vector_stats(
        self,
        operation_type: str,
        count: int = 1,
        execution_time_ms: Optional[float] = None,
    ):
        """更新向量统计"""
        query = """
            INSERT INTO vector_index_stats (
                operation_type, operation_count, total_execution_time_ms
            )
            VALUES ($1, $2, $3)
            ON CONFLICT (operation_type) DO UPDATE SET
                operation_count =
                    vector_index_stats.operation_count + $2,
                total_execution_time_ms =
                    vector_index_stats.total_execution_time_ms + $3,
                updated_at = NOW()
        """

        async with self.get_connection() as conn:
            await conn.execute(query, operation_type, count, execution_time_ms or 0.0)

    async def get_vector_stats(self) -> List[Dict[str, Any]]:
        """获取向量统计"""
        query = """
            SELECT operation_type, operation_count,
                   total_execution_time_ms,
                   CASE WHEN operation_count > 0
                        THEN total_execution_time_ms / operation_count
                        ELSE 0 END as avg_execution_time_ms,
                   created_at, updated_at
            FROM vector_index_stats
            ORDER BY operation_count DESC
        """

        async with self.get_connection() as conn:
            rows = await conn.fetch(query)
            return [dict(row) for row in rows]

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            async with self.get_connection() as conn:
                # 检查基本连接
                await conn.fetchval("SELECT 1")

                # 检查pgvector扩展
                vector_version = await conn.fetchval(
                    "SELECT extversion FROM pg_extension " "WHERE extname = 'vector'"
                )

                # 获取表统计
                table_stats = await conn.fetch(
                    """
                    SELECT
                        schemaname,
                        tablename,
                        n_tup_ins as inserts,
                        n_tup_upd as updates,
                        n_tup_del as deletes
                    FROM pg_stat_user_tables
                    WHERE tablename IN (
                        'document_vectors', 'vector_search_history', 'vector_index_stats'
                    )
                """
                )

                # 获取向量数量
                vector_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM document_vectors"
                )

                return {
                    "status": "healthy",
                    "pgvector_version": vector_version,
                    "vector_count": vector_count,
                    "table_stats": [dict(row) for row in table_stats],
                }

        except Exception as e:
            logger.error(f"数据库健康检查失败: {e}")
            return {"status": "unhealthy", "error": str(e)}


async def create_connection_pool() -> Pool:
    """创建数据库连接池"""
    try:
        pool = await asyncpg.create_pool(
            settings.DATABASE_URL,
            min_size=1,
            max_size=settings.DATABASE_POOL_SIZE,
            command_timeout=60,
            # 禁用JIT以提高向量操作性能
            server_settings={"jit": "off"},
        )

        logger.info(f"✅ 数据库连接池创建成功 (大小: {settings.DATABASE_POOL_SIZE})")
        return pool

    except Exception as e:
        logger.error(f"❌ 数据库连接池创建失败: {e}")
        raise


async def get_vector_database() -> VectorDatabase:
    """获取向量数据库实例"""
    global _pool

    if _pool is None:
        _pool = await create_connection_pool()

    return VectorDatabase(_pool)


async def get_vector_db() -> VectorDatabase:
    """获取向量数据库实例（兼容性别名）"""
    return await get_vector_database()


async def close_vector_db():
    """关闭向量数据库连接"""
    global _pool

    if _pool:
        await _pool.close()
        _pool = None
        logger.info("✅ 向量数据库连接已关闭")


if __name__ == "__main__":
    # 测试数据库连接
    async def test_connection():
        try:
            db = await get_vector_db()
            health = await db.health_check()
            print(f"数据库健康状态: {health}")
            await close_vector_db()
        except Exception as e:
            print(f"数据库连接测试失败: {e}")

    asyncio.run(test_connection())
