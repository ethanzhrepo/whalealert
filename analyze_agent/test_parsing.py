#!/usr/bin/env python3
"""
测试LLM响应解析功能
"""

import json
import re
from pydantic import BaseModel, Field

class SentimentAnalysisResult(BaseModel):
    """情绪分析结果模型"""
    情绪: str = Field(description="利多/利空/中性")
    理由: str = Field(description="判断理由")
    情绪评分: float = Field(description="情绪评分，范围-1.0到1.0")

def parse_response(response: str) -> SentimentAnalysisResult:
    """解析LLM响应"""
    try:
        # 清理响应内容
        response = response.strip()
        
        # 移除思考标签（如 <think>...</think>）
        # 移除 <think>...</think> 标签及其内容
        response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
        
        # 移除其他可能的思考标签
        response = re.sub(r'<thinking>.*?</thinking>', '', response, flags=re.DOTALL)
        response = re.sub(r'<thought>.*?</thought>', '', response, flags=re.DOTALL)
        
        # 清理多余的空白字符
        response = response.strip()
        
        # 尝试提取JSON部分
        if response.startswith('```json'):
            response = response[7:]
        if response.endswith('```'):
            response = response[:-3]
        
        # 使用正则表达式提取JSON对象
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        json_matches = re.findall(json_pattern, response, re.DOTALL)
        
        if json_matches:
            # 使用第一个匹配的JSON对象
            response = json_matches[0].strip()
        else:
            # 如果没有找到完整的JSON，尝试逐行解析
            lines = response.split('\n')
            json_lines = []
            in_json = False
            brace_count = 0
            
            for line in lines:
                line = line.strip()
                if not in_json and line.startswith('{'):
                    in_json = True
                    json_lines.append(line)
                    brace_count += line.count('{') - line.count('}')
                elif in_json:
                    json_lines.append(line)
                    brace_count += line.count('{') - line.count('}')
                    if brace_count <= 0:
                        break
            
            if json_lines:
                response = '\n'.join(json_lines)
        
        # 再次清理
        response = response.strip()
        
        print(f"清理后的响应: {response}")
        
        # 解析JSON
        data = json.loads(response)
        
        # 验证和标准化数据
        sentiment = data.get('情绪', '中性')
        if sentiment not in ['利多', '利空', '中性']:
            sentiment = '中性'
        
        reason = data.get('理由', '无法确定')
        score = float(data.get('情绪评分', 0.0))
        score = max(-1.0, min(1.0, score))  # 限制在[-1, 1]范围内
        
        return SentimentAnalysisResult(
            情绪=sentiment,
            理由=reason,
            情绪评分=score
        )
        
    except Exception as e:
        print(f"解析失败: {e}")
        return SentimentAnalysisResult(
            情绪="中性",
            理由="解析失败",
            情绪评分=0.0
        )

def test_parsing():
    """测试不同格式的响应解析"""
    
    test_cases = [
        # 正常JSON
        '''{"情绪": "利多", "理由": "BTC突破关键阻力位", "情绪评分": 0.8}''',
        
        # 带思考标签的响应
        '''<think>
好的，我现在需要分析这条新闻："BTC突破10万美元！牛市来了！"所传达的市场情绪。首先，新闻标题提到BTC价格突破了10万美元，这是一个重要的价格里程碑，通常这样的突破会被市场视为积极的信号。接着，标题中还提到"牛市来了"，这直接表明了市场参与者对未来的乐观预期。
</think>

{"情绪": "利多", "理由": "BTC突破重要价格关口，市场情绪乐观", "情绪评分": 0.9}''',
        
        # 带代码块的响应
        '''```json
{"情绪": "利空", "理由": "市场出现大幅回调", "情绪评分": -0.7}
```''',
        
        # 多行响应
        '''这是一个分析结果：
{
  "情绪": "中性",
  "理由": "技术指标显示中性信号",
  "情绪评分": 0.1
}
以上是我的分析。''',
        
        # 带多种标签的响应
        '''<thinking>
需要分析市场情绪...
</thinking>

<think>
这个消息比较中性...
</think>

{"情绪": "中性", "理由": "消息内容相对平衡", "情绪评分": 0.0}

这就是我的分析结果。'''
    ]
    
    print("🧪 测试LLM响应解析功能")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}:")
        print(f"原始响应: {test_case[:100]}...")
        
        result = parse_response(test_case)
        print(f"解析结果: 情绪={result.情绪}, 理由={result.理由}, 评分={result.情绪评分}")
        
        if result.理由 != "解析失败":
            print("✅ 解析成功")
        else:
            print("❌ 解析失败")

if __name__ == '__main__':
    test_parsing() 