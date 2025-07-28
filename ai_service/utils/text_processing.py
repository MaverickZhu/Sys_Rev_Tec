"""
AI服务文本处理工具
提供文本清理、分块、预处理等功能
"""

import logging
import re
import unicodedata
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ChunkStrategy(Enum):
    """文本分块策略"""

    FIXED_SIZE = "fixed_size"  # 固定大小分块
    SENTENCE = "sentence"  # 按句子分块
    PARAGRAPH = "paragraph"  # 按段落分块
    SEMANTIC = "semantic"  # 语义分块
    SLIDING_WINDOW = "sliding_window"  # 滑动窗口


@dataclass
class TextChunk:
    """文本块"""

    content: str
    start_pos: int
    end_pos: int
    chunk_id: int
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

        # 自动计算基本统计信息
        self.metadata.update(
            {
                "length": len(self.content),
                "word_count": len(self.content.split()),
                "char_count": len(self.content),
                "sentence_count": len(self._split_sentences(self.content)),
            }
        )

    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        """简单的句子分割"""
        # 中英文句子结束符
        sentence_endings = r"[.!?。！？；;]"
        sentences = re.split(sentence_endings, text)
        return [s.strip() for s in sentences if s.strip()]


class TextProcessor:
    """文本处理器"""

    def __init__(self):
        # 编译正则表达式以提高性能
        self.url_pattern = re.compile(
            r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
        )
        self.email_pattern = re.compile(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        )
        self.phone_pattern = re.compile(
            r"\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b"
        )
        self.whitespace_pattern = re.compile(r"\s+")
        self.punctuation_pattern = re.compile(r"[^\w\s\u4e00-\u9fff]")

        # 中文句子分割模式
        self.chinese_sentence_pattern = re.compile(r"[。！？；]")
        # 英文句子分割模式
        self.english_sentence_pattern = re.compile(r"[.!?]\s+")

        # 停用词（简化版）
        self.stop_words = {
            "en": {
                "the",
                "a",
                "an",
                "and",
                "or",
                "but",
                "in",
                "on",
                "at",
                "to",
                "for",
                "of",
                "with",
                "by",
                "is",
                "are",
                "was",
                "were",
                "be",
                "been",
                "have",
                "has",
                "had",
                "do",
                "does",
                "did",
                "will",
                "would",
                "could",
                "should",
                "may",
                "might",
                "must",
                "can",
                "this",
                "that",
                "these",
                "those",
            },
            "zh": {
                "的",
                "了",
                "在",
                "是",
                "我",
                "有",
                "和",
                "就",
                "不",
                "人",
                "都",
                "一",
                "一个",
                "上",
                "也",
                "很",
                "到",
                "说",
                "要",
                "去",
                "你",
                "会",
                "着",
                "没有",
                "看",
                "好",
                "自己",
                "这",
            },
        }

    def clean_text(self, text: str, options: Optional[Dict[str, bool]] = None) -> str:
        """清理文本"""
        if not text or not isinstance(text, str):
            return ""

        # 默认清理选项
        default_options = {
            "remove_urls": True,
            "remove_emails": False,
            "remove_phones": False,
            "normalize_whitespace": True,
            "remove_extra_punctuation": False,
            "normalize_unicode": True,
            "remove_control_chars": True,
            "preserve_line_breaks": False,
        }

        if options:
            default_options.update(options)

        cleaned_text = text

        # Unicode标准化
        if default_options["normalize_unicode"]:
            cleaned_text = unicodedata.normalize("NFKC", cleaned_text)

        # 移除控制字符
        if default_options["remove_control_chars"]:
            cleaned_text = "".join(
                char
                for char in cleaned_text
                if unicodedata.category(char)[0] != "C" or char in "\n\r\t"
            )

        # 移除URL
        if default_options["remove_urls"]:
            cleaned_text = self.url_pattern.sub("", cleaned_text)

        # 移除邮箱
        if default_options["remove_emails"]:
            cleaned_text = self.email_pattern.sub("", cleaned_text)

        # 移除电话号码
        if default_options["remove_phones"]:
            cleaned_text = self.phone_pattern.sub("", cleaned_text)

        # 标准化空白字符
        if default_options["normalize_whitespace"]:
            if default_options["preserve_line_breaks"]:
                # 保留换行符，但标准化其他空白字符
                lines = cleaned_text.split("\n")
                lines = [
                    self.whitespace_pattern.sub(" ", line).strip() for line in lines
                ]
                cleaned_text = "\n".join(lines)
            else:
                cleaned_text = self.whitespace_pattern.sub(" ", cleaned_text)

        # 移除多余标点
        if default_options["remove_extra_punctuation"]:
            # 保留基本标点，移除重复标点
            cleaned_text = re.sub(r"([.!?。！？]){2,}", r"\1", cleaned_text)
            cleaned_text = re.sub(r"([,，]){2,}", r"\1", cleaned_text)

        return cleaned_text.strip()

    def detect_language(self, text: str) -> str:
        """检测文本语言（简化版）"""
        if not text:
            return "unknown"

        # 统计中文字符
        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
        total_chars = len(re.findall(r"[\w\u4e00-\u9fff]", text))

        if total_chars == 0:
            return "unknown"

        chinese_ratio = chinese_chars / total_chars

        if chinese_ratio > 0.3:
            return "zh"
        elif chinese_ratio < 0.1:
            return "en"
        else:
            return "mixed"

    def split_sentences(self, text: str, language: Optional[str] = None) -> List[str]:
        """分割句子"""
        if not text:
            return []

        if language is None:
            language = self.detect_language(text)

        sentences = []

        if language == "zh" or language == "mixed":
            # 中文句子分割
            parts = self.chinese_sentence_pattern.split(text)
            for i, part in enumerate(parts):
                if part.strip():
                    # 重新添加标点符号（除了最后一个部分）
                    if i < len(parts) - 1:
                        # 查找原始标点
                        original_pos = text.find(part) + len(part)
                        if original_pos < len(text):
                            punct = text[original_pos]
                            sentences.append((part + punct).strip())
                        else:
                            sentences.append(part.strip())
                    else:
                        sentences.append(part.strip())

        if language == "en" or (language == "mixed" and not sentences):
            # 英文句子分割
            parts = self.english_sentence_pattern.split(text)
            sentences.extend([part.strip() for part in parts if part.strip()])

        # 如果没有找到句子分割符，按长度分割
        if not sentences:
            sentences = [text]

        return [s for s in sentences if len(s.strip()) > 0]

    def split_paragraphs(self, text: str) -> List[str]:
        """分割段落"""
        if not text:
            return []

        # 按双换行符分割段落
        paragraphs = re.split(r"\n\s*\n", text)

        # 清理并过滤空段落
        cleaned_paragraphs = []
        for para in paragraphs:
            cleaned_para = para.strip()
            if cleaned_para:
                cleaned_paragraphs.append(cleaned_para)

        return cleaned_paragraphs

    def chunk_text(
        self,
        text: str,
        strategy: ChunkStrategy = ChunkStrategy.FIXED_SIZE,
        chunk_size: int = 1000,
        overlap: int = 100,
        min_chunk_size: int = 50,
        **kwargs,
    ) -> List[TextChunk]:
        """文本分块"""
        if not text or len(text) < min_chunk_size:
            if text:
                return [
                    TextChunk(content=text, start_pos=0, end_pos=len(text), chunk_id=0)
                ]
            return []

        chunks = []

        if strategy == ChunkStrategy.FIXED_SIZE:
            chunks = self._chunk_fixed_size(text, chunk_size, overlap)

        elif strategy == ChunkStrategy.SENTENCE:
            chunks = self._chunk_by_sentences(text, chunk_size, overlap)

        elif strategy == ChunkStrategy.PARAGRAPH:
            chunks = self._chunk_by_paragraphs(text, chunk_size, overlap)

        elif strategy == ChunkStrategy.SLIDING_WINDOW:
            window_size = kwargs.get("window_size", chunk_size)
            step_size = kwargs.get("step_size", chunk_size - overlap)
            chunks = self._chunk_sliding_window(text, window_size, step_size)

        elif strategy == ChunkStrategy.SEMANTIC:
            # 语义分块（简化版，基于句子边界）
            chunks = self._chunk_semantic(text, chunk_size, overlap)

        # 过滤太小的块
        filtered_chunks = []
        for _i, chunk in enumerate(chunks):
            if len(chunk.content.strip()) >= min_chunk_size:
                chunk.chunk_id = len(filtered_chunks)
                filtered_chunks.append(chunk)

        return filtered_chunks

    def _chunk_fixed_size(
        self, text: str, chunk_size: int, overlap: int
    ) -> List[TextChunk]:
        """固定大小分块"""
        chunks = []
        start = 0
        chunk_id = 0

        while start < len(text):
            end = min(start + chunk_size, len(text))

            # 尝试在单词边界结束
            if end < len(text):
                # 向后查找空格或标点
                for i in range(end, max(start + chunk_size // 2, end - 100), -1):
                    if text[i] in " \n\t。！？.!?":
                        end = i + 1
                        break

            chunk_content = text[start:end].strip()
            if chunk_content:
                chunks.append(
                    TextChunk(
                        content=chunk_content,
                        start_pos=start,
                        end_pos=end,
                        chunk_id=chunk_id,
                    )
                )
                chunk_id += 1

            # 计算下一个开始位置（考虑重叠）
            start = max(start + 1, end - overlap)

            # 避免无限循环
            if start >= end:
                start = end

        return chunks

    def _chunk_by_sentences(
        self, text: str, max_size: int, overlap: int
    ) -> List[TextChunk]:
        """按句子分块"""
        sentences = self.split_sentences(text)
        chunks = []
        current_chunk = []
        current_size = 0
        chunk_id = 0

        for sentence in sentences:
            sentence_len = len(sentence)

            # 如果当前句子加入后超过大小限制，先保存当前块
            if current_size + sentence_len > max_size and current_chunk:
                chunk_content = " ".join(current_chunk)
                start_pos = text.find(current_chunk[0])
                end_pos = start_pos + len(chunk_content)

                chunks.append(
                    TextChunk(
                        content=chunk_content,
                        start_pos=start_pos,
                        end_pos=end_pos,
                        chunk_id=chunk_id,
                    )
                )
                chunk_id += 1

                # 处理重叠
                if overlap > 0 and len(current_chunk) > 1:
                    overlap_sentences = []
                    overlap_size = 0
                    for sent in reversed(current_chunk):
                        if overlap_size + len(sent) <= overlap:
                            overlap_sentences.insert(0, sent)
                            overlap_size += len(sent)
                        else:
                            break
                    current_chunk = overlap_sentences
                    current_size = overlap_size
                else:
                    current_chunk = []
                    current_size = 0

            current_chunk.append(sentence)
            current_size += sentence_len

        # 处理最后一个块
        if current_chunk:
            chunk_content = " ".join(current_chunk)
            start_pos = text.find(current_chunk[0])
            end_pos = start_pos + len(chunk_content)

            chunks.append(
                TextChunk(
                    content=chunk_content,
                    start_pos=start_pos,
                    end_pos=end_pos,
                    chunk_id=chunk_id,
                )
            )

        return chunks

    def _chunk_by_paragraphs(
        self, text: str, max_size: int, overlap: int
    ) -> List[TextChunk]:
        """按段落分块"""
        paragraphs = self.split_paragraphs(text)
        chunks = []
        current_chunk = []
        current_size = 0
        chunk_id = 0

        for paragraph in paragraphs:
            para_len = len(paragraph)

            # 如果单个段落就超过大小限制，需要进一步分割
            if para_len > max_size:
                # 如果当前有累积的内容，先保存
                if current_chunk:
                    chunk_content = "\n\n".join(current_chunk)
                    start_pos = text.find(current_chunk[0])
                    end_pos = start_pos + len(chunk_content)

                    chunks.append(
                        TextChunk(
                            content=chunk_content,
                            start_pos=start_pos,
                            end_pos=end_pos,
                            chunk_id=chunk_id,
                        )
                    )
                    chunk_id += 1
                    current_chunk = []
                    current_size = 0

                # 对大段落按句子分割
                para_chunks = self._chunk_by_sentences(paragraph, max_size, overlap)
                for para_chunk in para_chunks:
                    para_chunk.chunk_id = chunk_id
                    chunks.append(para_chunk)
                    chunk_id += 1

            # 如果加入当前段落会超过限制，先保存当前块
            elif current_size + para_len > max_size and current_chunk:
                chunk_content = "\n\n".join(current_chunk)
                start_pos = text.find(current_chunk[0])
                end_pos = start_pos + len(chunk_content)

                chunks.append(
                    TextChunk(
                        content=chunk_content,
                        start_pos=start_pos,
                        end_pos=end_pos,
                        chunk_id=chunk_id,
                    )
                )
                chunk_id += 1

                # 处理重叠
                if overlap > 0 and current_chunk:
                    current_chunk = [current_chunk[-1]]  # 保留最后一个段落作为重叠
                    current_size = len(current_chunk[0])
                else:
                    current_chunk = []
                    current_size = 0

                current_chunk.append(paragraph)
                current_size += para_len
            else:
                current_chunk.append(paragraph)
                current_size += para_len

        # 处理最后一个块
        if current_chunk:
            chunk_content = "\n\n".join(current_chunk)
            start_pos = text.find(current_chunk[0])
            end_pos = start_pos + len(chunk_content)

            chunks.append(
                TextChunk(
                    content=chunk_content,
                    start_pos=start_pos,
                    end_pos=end_pos,
                    chunk_id=chunk_id,
                )
            )

        return chunks

    def _chunk_sliding_window(
        self, text: str, window_size: int, step_size: int
    ) -> List[TextChunk]:
        """滑动窗口分块"""
        chunks = []
        chunk_id = 0

        for start in range(0, len(text), step_size):
            end = min(start + window_size, len(text))

            # 尝试在单词边界结束
            if end < len(text):
                for i in range(end, max(start + window_size // 2, end - 50), -1):
                    if text[i] in " \n\t。！？.!?":
                        end = i + 1
                        break

            chunk_content = text[start:end].strip()
            if chunk_content:
                chunks.append(
                    TextChunk(
                        content=chunk_content,
                        start_pos=start,
                        end_pos=end,
                        chunk_id=chunk_id,
                    )
                )
                chunk_id += 1

            if end >= len(text):
                break

        return chunks

    def _chunk_semantic(
        self, text: str, max_size: int, overlap: int
    ) -> List[TextChunk]:
        """语义分块（简化版）"""
        # 这里使用句子边界的启发式方法
        # 在实际应用中，可以使用更复杂的语义分析

        sentences = self.split_sentences(text)
        chunks = []
        current_chunk = []
        current_size = 0
        chunk_id = 0

        for _i, sentence in enumerate(sentences):
            sentence_len = len(sentence)

            # 检查是否应该开始新块
            should_break = False

            if current_size + sentence_len > max_size and current_chunk:
                should_break = True

            # 语义边界检测（简化版）
            if not should_break and current_chunk:
                # 检查话题转换的信号词
                topic_change_signals = [
                    "然而",
                    "但是",
                    "不过",
                    "另外",
                    "此外",
                    "另一方面",
                    "however",
                    "but",
                    "moreover",
                    "furthermore",
                    "on the other hand",
                ]

                sentence_lower = sentence.lower()
                if any(signal in sentence_lower for signal in topic_change_signals):
                    if current_size > max_size * 0.5:  # 至少达到一半大小才考虑分割
                        should_break = True

            if should_break:
                chunk_content = " ".join(current_chunk)
                start_pos = text.find(current_chunk[0])
                end_pos = start_pos + len(chunk_content)

                chunks.append(
                    TextChunk(
                        content=chunk_content,
                        start_pos=start_pos,
                        end_pos=end_pos,
                        chunk_id=chunk_id,
                    )
                )
                chunk_id += 1

                # 处理重叠
                if overlap > 0 and len(current_chunk) > 1:
                    overlap_sentences = []
                    overlap_size = 0
                    for sent in reversed(current_chunk):
                        if overlap_size + len(sent) <= overlap:
                            overlap_sentences.insert(0, sent)
                            overlap_size += len(sent)
                        else:
                            break
                    current_chunk = overlap_sentences
                    current_size = overlap_size
                else:
                    current_chunk = []
                    current_size = 0

            current_chunk.append(sentence)
            current_size += sentence_len

        # 处理最后一个块
        if current_chunk:
            chunk_content = " ".join(current_chunk)
            start_pos = text.find(current_chunk[0])
            end_pos = start_pos + len(chunk_content)

            chunks.append(
                TextChunk(
                    content=chunk_content,
                    start_pos=start_pos,
                    end_pos=end_pos,
                    chunk_id=chunk_id,
                )
            )

        return chunks

    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """提取关键词（简化版）"""
        if not text:
            return []

        # 清理文本
        cleaned_text = self.clean_text(
            text,
            {
                "remove_urls": True,
                "remove_emails": True,
                "normalize_whitespace": True,
                "remove_extra_punctuation": True,
            },
        )

        # 检测语言
        language = self.detect_language(cleaned_text)

        # 分词（简化版）
        if language == "zh":
            # 中文按字符分割（实际应用中应使用jieba等分词工具）
            words = re.findall(r"[\u4e00-\u9fff]+", cleaned_text)
        else:
            # 英文按单词分割
            words = re.findall(r"\b\w+\b", cleaned_text.lower())

        # 过滤停用词和短词
        stop_words = self.stop_words.get(language[:2], set())
        filtered_words = [
            word for word in words if len(word) > 2 and word not in stop_words
        ]

        # 统计词频
        word_freq = {}
        for word in filtered_words:
            word_freq[word] = word_freq.get(word, 0) + 1

        # 按频率排序并返回前N个
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        keywords = [word for word, freq in sorted_words[:max_keywords]]

        return keywords

    def calculate_text_stats(self, text: str) -> Dict[str, Any]:
        """计算文本统计信息"""
        if not text:
            return {
                "char_count": 0,
                "word_count": 0,
                "sentence_count": 0,
                "paragraph_count": 0,
                "language": "unknown",
                "avg_sentence_length": 0,
                "avg_word_length": 0,
            }

        # 基本统计
        char_count = len(text)
        words = re.findall(r"\b\w+\b", text)
        word_count = len(words)
        sentences = self.split_sentences(text)
        sentence_count = len(sentences)
        paragraphs = self.split_paragraphs(text)
        paragraph_count = len(paragraphs)

        # 语言检测
        language = self.detect_language(text)

        # 平均长度
        avg_sentence_length = char_count / sentence_count if sentence_count > 0 else 0
        avg_word_length = (
            sum(len(word) for word in words) / word_count if word_count > 0 else 0
        )

        return {
            "char_count": char_count,
            "word_count": word_count,
            "sentence_count": sentence_count,
            "paragraph_count": paragraph_count,
            "language": language,
            "avg_sentence_length": round(avg_sentence_length, 2),
            "avg_word_length": round(avg_word_length, 2),
            "keywords": self.extract_keywords(text, 5),
        }


# 全局文本处理器实例
_text_processor = None


def get_text_processor() -> TextProcessor:
    """获取文本处理器实例"""
    global _text_processor
    if _text_processor is None:
        _text_processor = TextProcessor()
    return _text_processor


if __name__ == "__main__":
    # 测试文本处理功能
    processor = get_text_processor()

    test_text = """
    这是一个测试文档。它包含多个段落和句子。

    第二个段落开始了。这里有更多的内容需要处理。我们需要测试分块功能是否正常工作。

    This is an English paragraph. It contains multiple sentences for testing purposes. We need to verify that the text processing works correctly for mixed languages.

    最后一个段落。包含了中英文混合的内容。测试完成。
    """

    print("=== 文本清理 ===")
    cleaned = processor.clean_text(test_text)
    print(f"清理后文本: {cleaned[:100]}...")

    print("\n=== 语言检测 ===")
    language = processor.detect_language(test_text)
    print(f"检测语言: {language}")

    print("\n=== 句子分割 ===")
    sentences = processor.split_sentences(test_text)
    print(f"句子数量: {len(sentences)}")
    for i, sentence in enumerate(sentences[:3]):
        print(f"句子 {i + 1}: {sentence}")

    print("\n=== 段落分割 ===")
    paragraphs = processor.split_paragraphs(test_text)
    print(f"段落数量: {len(paragraphs)}")

    print("\n=== 文本分块 ===")
    chunks = processor.chunk_text(test_text, ChunkStrategy.SENTENCE, chunk_size=200)
    print(f"分块数量: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(f"块 {i + 1} (长度: {len(chunk.content)}): {chunk.content[:50]}...")

    print("\n=== 关键词提取 ===")
    keywords = processor.extract_keywords(test_text)
    print(f"关键词: {keywords}")

    print("\n=== 文本统计 ===")
    stats = processor.calculate_text_stats(test_text)
    print(f"统计信息: {stats}")
