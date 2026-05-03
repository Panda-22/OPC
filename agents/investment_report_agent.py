import re
from typing import Any, Dict, List


class InvestmentReportAgent:
    """Agent to parse and interpret professional investment reports in the餐饮领域.

    Input: raw text report
    Output: structured interpretation with core conclusions, scores and actionable recommendations.
    """

    def __init__(self, language: str = 'zh'):
        self.language = language

    def _split_sections(self, text: str) -> Dict[str, str]:
        # Known section headings we want to capture
        headings = {
            '核心结论': '核心结论',
            '维度雷达图': '维度雷达图',
            '维度得分对比': '维度得分对比',
            '一、四大维度打分逻辑': '四大维度打分逻辑',
            '二、智能体制定建议': '智能体制定建议',
        }
        curr = None
        parts: Dict[str, str] = {v: '' for v in headings.values()}
        lines = text.splitlines()
        buffer: List[str] = []
        for raw_line in lines:
            line = raw_line.rstrip()
            key_line = line.strip()
            # detect exact heading lines
            if key_line in headings:
                # flush previous
                if curr and buffer:
                    parts[curr] = (parts[curr] + '\n' if parts[curr] else '') + '\n'.join(buffer).strip()
                    buffer = []
                curr = headings[key_line]
                continue
            # detect numbered headings like 一、 二、
            m_num = re.match(r'^(一|二|三|四)、', key_line)
            if m_num:
                # normalize to 四大维度打分逻辑 if we encounter the first one
                if curr is None:
                    curr = '四大维度打分逻辑'
                continue
            if curr:
                buffer.append(line)
        if curr and buffer:
            parts[curr] = (parts[curr] + '\n' if parts[curr] else '') + '\n'.join(buffer).strip()
        # remove empty entries
        return {k: v.strip() for k, v in parts.items() if v.strip()}

    def analyze(self, report_text: str) -> Dict[str, Any]:
        sections = self._split_sections(report_text)
        core = sections.get('核心结论', '')
        radar_raw = sections.get('维度雷达图', '')
        score_raw = sections.get('维度得分对比', '')
        suggestions_raw = sections.get('智能体制定建议', '') or sections.get('智能体建议', '')

        # Parse radar-like data: label: value or label value
        radar_points: List[Dict[str, Any]] = []
        if radar_raw:
            for line in radar_raw.splitlines():
                line = line.strip()
                if not line:
                    continue
                m = re.match(r'([^：:]+)[：:]\s*([0-9]+(?:\.[0-9]+)?)', line)
                if m:
                    radar_points.append({'label': m.group(1).strip(), 'value': float(m.group(2))})
                else:
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            radar_points.append({'label': parts[0], 'value': float(re.sub(r'[^0-9.]', '', parts[1]))})
                        except ValueError:
                            pass

        # Parse scores into a list of dimension-score pairs
        dimension_scores: List[Dict[str, Any]] = []
        if score_raw:
            for line in score_raw.splitlines():
                line = line.strip()
                if not line:
                    continue
                m = re.match(r'([^：:]+)[：:]\s*([0-9]+(?:\.[0-9]+)?)', line)
                if m:
                    dimension_scores.append({'dimension': m.group(1).strip(), 'score': float(m.group(2))})

        analysis = {
            'title': self._extract_title(report_text),
            'core_conclusion': core,
            'radar_points': radar_points,
            'dimension_scores': dimension_scores,
            'suggestions': self._split_sentences(suggestions_raw) if suggestions_raw else [],
        }
        return analysis

    def _extract_title(self, text: str) -> str:
        # Naive extraction: look for the first line containing 报告 or 投资
        for line in text.splitlines():
            t = line.strip()
            if not t:
                continue
            if '报告' in t or '分析' in t or '投资' in t:
                return t
        return '投资分析报告'

    def _split_sentences(self, text: str) -> List[str]:
        # Simple line-based sentences; trim empty lines
        items: List[str] = []
        for line in text.splitlines():
            t = line.strip()
            if not t:
                continue
            items.append(t)
        return items
