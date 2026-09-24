"""
智能课程匹配模块

实现高容错率的课程匹配，支持模糊输入、字段组合、错字纠正
"""

import re
from difflib import SequenceMatcher
from typing import Optional
from dataclasses import dataclass

from .models import Course
from ..utils.logger import get_logger


@dataclass
class MatchResult:
    """
    匹配结果

    Attributes:
        course: 匹配到的课程
        score: 匹配分数 (0-100)
        confidence: 置信度 (high/medium/low)
        matched_fields: 匹配到的字段列表
    """

    course: Course
    score: float
    confidence: str
    matched_fields: list[str]


class CourseMatcher:
    """
    智能课程匹配器

    特点：
    1. 不预设字段类型，自动从课程信息提取所有特征
    2. 支持模糊匹配（错字、漏字、多字）
    3. 支持任意字段组合
    4. 多层次匹配策略
    """

    def __init__(self) -> None:
        self.logger = get_logger(__name__)

    def match(
        self, query: str, courses: list[Course], threshold: float = 15.0
    ) -> list[MatchResult]:
        """
        匹配课程

        Args:
            query: 用户输入的查询字符串
            courses: 课程列表
            threshold: 最低匹配分数阈值

        Returns:
            匹配结果列表，按分数降序排列
        """
        if not courses:
            return []

        # 预处理查询
        query_normalized = self._normalize_text(query)
        if not query_normalized:
            self.logger.warning("课程查询关键词不能为空")
            return []

        self.logger.debug(f"查询: '{query}'")
        self.logger.debug(f"标准化: '{query_normalized}'")

        results = []

        for course in courses:
            result = self._match_course(query, query_normalized, course)
            if result and result.score >= threshold:
                results.append(result)

        # 按分数降序排序
        results.sort(key=lambda x: x.score, reverse=True)

        return results

    def match_best(
        self,
        query: str,
        courses: list[Course],
        auto_confirm_threshold: float = 80.0,
        confirm_threshold: float = 50.0,
    ) -> Optional[MatchResult]:
        """
        匹配最佳课程

        Args:
            query: 用户输入的查询字符串
            courses: 课程列表
            auto_confirm_threshold: 自动确认阈值
            confirm_threshold: 需要确认的阈值

        Returns:
            最佳匹配结果，如果没有匹配则返回None
        """
        results = self.match(query, courses, threshold=confirm_threshold)

        if not results:
            return None

        best = results[0]

        # 高置信度：自动确认
        if best.score >= auto_confirm_threshold:
            best.confidence = "high"
            self.logger.info(
                f"高置信度匹配: {best.course.name} (分数: {best.score:.1f})"
            )
        # 中置信度：需要确认
        elif best.score >= confirm_threshold:
            best.confidence = "medium"
            self.logger.info(
                f"中置信度匹配: {best.course.name} (分数: {best.score:.1f})"
            )
        else:
            best.confidence = "low"
            self.logger.info(
                f"低置信度匹配: {best.course.name} (分数: {best.score:.1f})"
            )

        return best

    def _match_course(
        self, query: str, query_normalized: str, course: Course
    ) -> Optional[MatchResult]:
        """
        匹配单门课程

        使用多层次匹配策略：
        1. 精确匹配
        2. 包含匹配
        3. 模糊匹配（编辑距离）
        """
        matched_fields = []
        best_score = 0.0

        # 提取所有可匹配字段
        fields = {
            "name": (course.name or "", 3.0),
            "teacher": (course.teacher or "", 2.0),
            "schedule": (course.schedule or "", 1.5),
            "category": (course.category or "", 1.0),
            "class_name": (course.class_name or "", 1.0),
        }

        # 对每个字段计算匹配分数
        for field_name, (field_text, weight) in fields.items():
            if not field_text:
                continue

            field_normalized = self._normalize_text(field_text)
            score = 0.0

            # 1. 精确匹配
            if query_normalized == field_normalized:
                score = 100.0
                matched_fields.append(f"{field_name}(精确)")
                best_score = max(best_score, score * (weight / 3.0))
                continue

            # 2. 包含匹配
            if query_normalized in field_normalized:
                ratio = len(query_normalized) / len(field_normalized)
                score = 60 + ratio * 40  # 60-100分
                matched_fields.append(field_name)
                best_score = max(best_score, score * (weight / 3.0))
                continue

            # 3. 反向包含
            if field_normalized in query_normalized:
                ratio = len(field_normalized) / len(query_normalized)
                score = 40 + ratio * 40  # 40-80分
                matched_fields.append(field_name)
                best_score = max(best_score, score * (weight / 3.0))
                continue

            # 4. 模糊匹配（编辑距离）
            similarity = self._similarity(query_normalized, field_normalized)
            if similarity > 0.5:
                score = similarity * 60  # 30-60分
                if similarity > 0.7:
                    matched_fields.append(f"{field_name}(模糊)")

            # 课程名称保留完整分值，其他字段按权重降分。这样可以用
            # 教师、时间等信息辅助排序，但不会单独触发高置信度报名。
            weighted_score = score * (weight / 3.0)
            best_score = max(best_score, weighted_score)

        # 如果没有匹配，返回None
        if best_score < 10:
            return None

        return MatchResult(
            course=course,
            score=best_score,
            confidence="unknown",
            matched_fields=matched_fields,
        )

    def _normalize_text(self, text: str) -> str:
        """
        标准化文本

        - 转小写
        - 去除空格
        - 统一括号
        """
        if not text:
            return ""

        # 转小写
        text = text.lower()

        # 统一括号
        text = text.replace("（", "(").replace("）", ")")
        text = text.replace("【", "[").replace("】", "]")

        # 去除空格
        text = re.sub(r"\s+", "", text)

        return text

    def _similarity(self, text1: str, text2: str) -> float:
        """
        计算两个文本的相似度（编辑距离）

        Returns:
            相似度 (0-1)
        """
        if not text1 or not text2:
            return 0.0

        return SequenceMatcher(None, text1, text2).ratio()
