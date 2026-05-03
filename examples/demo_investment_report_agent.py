from agents.investment_report_agent import InvestmentReportAgent

SAMPLE_REPORT = '''
餐饮投资分析报告

核心结论
本期投资具备良好成长性，餐饮市场复苏显著， excepc 调整空间有限，建议适度入局，优选大品牌和区域连锁以分散风险。

维度雷达图
资金匹配度：8.5
经验适配度：7.0
时间/心态匹配度：6.8
区域匹配度：7.2

维度得分对比
资金匹配度：22/25
经验匹配度：6/25
时间/心态匹配度：12/25
区域匹配度：20/25

二、智能体制定建议
1) 经验补充：先择经验丰富的投资人/团队，确保选址与开店策略符合本地市场。
2) 时间优化：重点关注周末/节假日高峰期的客流规律，制定灵活排期。
3) 资金与预期：设定50万初始投资，目标回收期12-18个月。
4) 区域优先：优先考虑人口密集区与商业圈，降低单店风险。
5) 风险控制：设置止损与止盈点，建立现金流缓冲。
'''

def main():
    agent = InvestmentReportAgent()
    analysis = agent.analyze(SAMPLE_REPORT)
    import json
    print(json.dumps(analysis, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
