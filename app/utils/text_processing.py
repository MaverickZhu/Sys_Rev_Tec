# -*- coding: utf-8 -*-
"""
文本处理工具模块
提供文本清理、分块、预处理等功能
"""

import re
import unicodedata
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class TextChunk:
    """文本块数据类"""
    text: str
    start_index: int
    end_index: int
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class TextProcessor:
    """文本处理器"""
    
    def __init__(self):
        self.chunk_size = 1000
        self.chunk_overlap = 200
        
    def clean_text(self, text: str) -> str:
        """清理文本"""
        if not text:
            return ""
            
        # 标准化Unicode字符
        text = unicodedata.normalize('NFKC', text)
        
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        
        # 移除控制字符
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        # 去除首尾空白
        text = text.strip()
        
        return text
    
    def split_text(self, text: str, chunk_size: Optional[int] = None, 
                   chunk_overlap: Optional[int] = None) -> List[TextChunk]:
        """分割文本为块"""
        if not text:
            return []
            
        chunk_size = chunk_size or self.chunk_size
        chunk_overlap = chunk_overlap or self.chunk_overlap
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = min(start + chunk_size, len(text))
            
            # 尝试在句子边界分割
            if end < len(text):
                # 查找最近的句号、问号或感叹号
                for i in range(end, max(start, end - 100), -1):
                    if text[i] in '.!?。！？':
                        end = i + 1
                        break
            
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(TextChunk(
                    text=chunk_text,
                    start_index=start,
                    end_index=end,
                    metadata={
                        'chunk_id': len(chunks),
                        'chunk_size': len(chunk_text)
                    }
                ))
            
            # 计算下一个块的起始位置
            start = max(start + 1, end - chunk_overlap)
            
        return chunks
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """提取关键词（简单实现）"""
        if not text:
            return []
            
        # 简单的关键词提取：基于词频
        words = re.findall(r'\b\w{2,}\b', text.lower())
        
        # 过滤停用词（简化版）
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            '的', '了', '在', '是', '我', '你', '他', '她', '它', '们', '这', '那',
            '有', '没', '不', '也', '都', '很', '就', '还', '要', '可以', '能够'
        }
        
        # 计算词频
        word_freq = {}
        for word in words:
            if word not in stop_words and len(word) > 2:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # 按频率排序并返回前N个
        keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in keywords[:max_keywords]]
    
    def get_text_stats(self, text: str) -> Dict[str, Any]:
        """获取文本统计信息"""
        if not text:
            return {
                'char_count': 0,
                'word_count': 0,
                'sentence_count': 0,
                'paragraph_count': 0
            }
        
        # 字符数
        char_count = len(text)
        
        # 词数
        words = re.findall(r'\b\w+\b', text)
        word_count = len(words)
        
        # 句子数
        sentences = re.split(r'[.!?。！？]+', text)
        sentence_count = len([s for s in sentences if s.strip()])
        
        # 段落数
        paragraphs = text.split('\n\n')
        paragraph_count = len([p for p in paragraphs if p.strip()])
        
        return {
            'char_count': char_count,
            'word_count': word_count,
            'sentence_count': sentence_count,
            'paragraph_count': paragraph_count
        }
    
    def chunk_text(self, text: str, chunk_size: Optional[int] = None, 
                   chunk_overlap: Optional[int] = None) -> List[Dict[str, Any]]:
        """分块文本（兼容性方法）"""
        chunks = self.split_text(text, chunk_size, chunk_overlap)
        return [
            {
                'text': chunk.text,
                'start_char': chunk.start_index,
                'end_char': chunk.end_index,
                'metadata': chunk.metadata
            }
            for chunk in chunks
        ]
    
    def get_text_statistics(self, text: str) -> Dict[str, Any]:
        """获取文本统计信息（兼容性方法）"""
        return self.get_text_stats(text)
    
    def preprocess_for_embedding(self, text: str) -> str:
        """为嵌入预处理文本"""
        # 清理文本
        text = self.clean_text(text)
        
        # 限制长度（避免超过模型限制）
        max_length = 8000  # 保守估计
        if len(text) > max_length:
            text = text[:max_length]
        
        return text