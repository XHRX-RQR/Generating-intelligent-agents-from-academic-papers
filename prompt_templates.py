"""
预设提示词系统和模板管理
"""
from typing import Dict, List, Any
import yaml


class PromptTemplates:
    """提示词模板库"""
    
    # 系统角色提示词
    SYSTEM_ROLE = """你是一位经验丰富的学术论文写作专家，拥有多年的学术研究和论文指导经验。
你的任务是帮助研究者撰写高质量的学术论文，确保论文的学术性、严谨性和创新性。
你擅长引导用户提供详细信息，并能够根据信息生成结构完整、逻辑清晰的学术论文。"""

    # 信息收集阶段的提示词
    INFORMATION_COLLECTION = {
        "initial": """作为学术论文写作专家，我将帮助您撰写一篇高质量的学术论文。

为了更好地帮助您，我需要了解以下基本信息：

1. **研究主题**: 您的研究主要关注什么问题或领域？
2. **研究背景**: 为什么选择这个研究主题？有什么实际意义？
3. **研究目标**: 您希望通过这项研究达到什么目的？
4. **目标期刊/会议**: 您计划投稿到哪个期刊或会议？（这将帮助我了解格式要求）

请简要回答这些问题，我会根据您的回答进一步引导您完善论文内容。""",
        
        "research_background": """感谢您提供的信息。现在让我们深入了解研究背景：

1. **相关理论基础**: 您的研究基于哪些理论或概念框架？
2. **已有研究**: 在这个领域，已有哪些重要的研究成果？
3. **研究缺口**: 现有研究存在哪些不足或空白？
4. **研究问题**: 您的研究具体要解决什么问题？

详细的背景信息将帮助我们构建更有说服力的引言部分。""",
        
        "methodology": """接下来，让我们讨论研究方法：

1. **研究设计**: 您采用什么研究设计？（实验研究、案例研究、调查研究等）
2. **数据来源**: 研究数据从哪里获取？样本量多大？
3. **数据收集方法**: 如何收集数据？（问卷、访谈、观察、实验等）
4. **分析方法**: 使用什么方法分析数据？（统计分析、内容分析、模型构建等）
5. **研究工具**: 使用了哪些软件或工具？

清晰的方法论描述对于论文的可信度至关重要。""",
        
        "results": """现在让我们关注研究结果：

1. **主要发现**: 您的研究得出了哪些主要发现或结论？
2. **数据呈现**: 您有哪些数据、图表或统计结果需要展示？
3. **关键指标**: 有哪些关键的量化或质化指标？
4. **意外发现**: 是否有一些意外但有价值的发现？

请尽可能详细地描述您的研究结果，包括具体的数据和发现。""",
        
        "discussion": """让我们深入讨论研究的意义：

1. **结果解释**: 如何解释您的研究发现？为什么会得到这样的结果？
2. **理论贡献**: 您的研究对现有理论有什么贡献或挑战？
3. **实践启示**: 研究结果对实践有什么指导意义？
4. **研究局限**: 您认为这项研究有哪些局限性？
5. **未来方向**: 基于这项研究，未来可以在哪些方向深入探索？

这些讨论将使您的论文更有深度和价值。""",
        
        "literature_review": """让我们完善文献综述部分：

1. **核心文献**: 您的研究领域有哪些必读的经典文献？
2. **近期研究**: 最近3-5年有哪些相关的重要研究？
3. **理论框架**: 您采用或参考了哪些理论框架？
4. **研究流派**: 这个领域存在哪些不同的研究视角或流派？
5. **批判性分析**: 对现有研究，您有什么批判性的看法？

全面的文献综述将展现您对研究领域的深入理解。"""
    }
    
    # 内容生成阶段的提示词
    CONTENT_GENERATION = {
        "abstract": """基于以下研究信息，请生成一篇学术论文的摘要（Abstract）：

{collected_info}

要求：
1. 包含研究背景、研究目的、研究方法、主要发现四个部分
2. 字数控制在200-300字
3. 使用学术化、正式的语言
4. 突出研究的创新性和重要性
5. 避免使用第一人称

请生成摘要内容：""",
        
        "introduction": """基于以下研究信息，请生成论文的引言（Introduction）部分：

{collected_info}

要求：
1. 从宏观背景引入，逐步聚焦到具体研究问题
2. 阐述研究的重要性和必要性
3. 简要回顾相关文献
4. 明确提出研究问题和研究目标
5. 说明论文的结构安排
6. 字数控制在1000-1500字
7. 使用学术化语言，逻辑清晰

请生成引言内容：""",
        
        "literature_review": """基于以下研究信息，请生成论文的文献综述（Literature Review）部分：

{collected_info}

要求：
1. 系统梳理相关领域的研究成果
2. 按照主题或时间顺序组织文献
3. 不仅罗列文献，更要进行批判性分析
4. 指出现有研究的不足和研究缺口
5. 为本研究的必要性提供支撑
6. 字数控制在2000-3000字
7. 引用格式规范，逻辑严密

请生成文献综述内容：""",
        
        "methodology": """基于以下研究信息，请生成论文的研究方法（Methodology）部分：

{collected_info}

要求：
1. 详细描述研究设计和研究流程
2. 说明数据来源、样本选择和样本量
3. 阐述数据收集的具体方法和工具
4. 解释数据分析的方法和技术
5. 说明研究的信度和效度保证措施
6. 字数控制在1500-2000字
7. 语言精确，可操作性强

请生成研究方法内容：""",
        
        "results": """基于以下研究信息，请生成论文的研究结果（Results）部分：

{collected_info}

要求：
1. 客观呈现研究发现，不加主观解释
2. 使用表格、图表等形式展示数据（用文字描述表格内容）
3. 按照逻辑顺序组织结果
4. 突出关键发现和重要数据
5. 数据呈现清晰、准确
6. 字数控制在2000-3000字
7. 避免在此部分进行讨论和解释

请生成研究结果内容：""",
        
        "discussion": """基于以下研究信息，请生成论文的讨论（Discussion）部分：

{collected_info}

要求：
1. 深入解释研究发现的含义
2. 将研究结果与已有文献进行对比和讨论
3. 阐述研究的理论贡献和实践意义
4. 客观分析研究的局限性
5. 提出未来研究方向和建议
6. 字数控制在1500-2000字
7. 论述有深度，逻辑严密

请生成讨论内容：""",
        
        "conclusion": """基于以下研究信息，请生成论文的结论（Conclusion）部分：

{collected_info}

要求：
1. 总结研究的主要发现
2. 强调研究的贡献和价值
3. 简要说明研究的局限性
4. 提出未来研究方向
5. 呼应引言，首尾照应
6. 字数控制在500-800字
7. 语言凝练，观点明确

请生成结论内容："""
    }
    
    # 质量审核的提示词
    QUALITY_REVIEW = """请作为一位严格的学术审稿人，对以下论文内容进行审核：

{content}

请从以下维度进行评审：

1. **学术规范性**: 语言是否符合学术规范？是否有口语化表达？
2. **逻辑严密性**: 论述逻辑是否清晰？前后是否一致？
3. **内容完整性**: 是否涵盖了该部分应该包含的所有要素？
4. **创新性**: 是否体现了研究的创新点？
5. **可读性**: 表达是否清晰易懂？结构是否合理？
6. **具体问题**: 指出具体的问题和需要改进的地方

请提供详细的审核意见和修改建议："""
    
    # 结构优化的提示词
    STRUCTURE_OPTIMIZATION = """请作为论文结构专家，优化以下论文内容的结构和组织：

{content}

请从以下方面进行优化：

1. **段落组织**: 段落划分是否合理？是否需要重组？
2. **逻辑流程**: 内容的展开顺序是否最优？
3. **过渡衔接**: 段落和部分之间的过渡是否自然？
4. **重点突出**: 是否突出了关键信息和重要观点？
5. **冗余删减**: 是否有重复或冗余的内容需要删减？

请提供优化后的内容或具体的优化建议："""
    
    # 多模型协作的提示词
    MODEL_COLLABORATION = {
        "information_collector": """你是信息收集专家。你的任务是：
1. 分析已收集的信息，识别缺失的关键信息
2. 设计针对性的问题，引导用户提供更多细节
3. 评估信息的完整性和充分性

当前已收集信息：
{collected_info}

当前阶段：{current_stage}

请分析还需要收集哪些信息，并生成3-5个引导性问题：""",
        
        "content_generator": """你是论文内容生成专家。你的任务是：
1. 基于收集的信息生成高质量的学术论文内容
2. 确保内容符合学术规范和标准
3. 保持学术语言的严谨性和专业性

请基于以下信息生成{section}部分的内容：
{collected_info}

生成要求：
{requirements}

请生成内容：""",
        
        "quality_reviewer": """你是论文质量审核专家。你的任务是：
1. 严格审核论文内容的质量
2. 发现逻辑问题、语言问题和学术规范问题
3. 提供具体的改进建议

请审核以下内容：
{content}

审核维度：
1. 学术规范性
2. 逻辑严密性
3. 内容完整性
4. 语言表达
5. 创新性

请提供详细的审核报告：""",
        
        "structure_optimizer": """你是论文结构优化专家。你的任务是：
1. 优化论文的整体结构和组织
2. 改善段落的逻辑流程
3. 增强内容的连贯性和可读性

请优化以下内容的结构：
{content}

优化目标：
1. 提升逻辑性
2. 增强可读性
3. 突出重点
4. 改善过渡

请提供优化方案或优化后的内容："""
    }
    
    @staticmethod
    def get_information_collection_prompt(stage: str) -> str:
        """获取信息收集阶段的提示词"""
        return PromptTemplates.INFORMATION_COLLECTION.get(
            stage, 
            PromptTemplates.INFORMATION_COLLECTION["initial"]
        )
    
    @staticmethod
    def get_content_generation_prompt(section: str, collected_info: Dict) -> str:
        """获取内容生成提示词"""
        template = PromptTemplates.CONTENT_GENERATION.get(section, "")
        info_text = PromptTemplates._format_collected_info(collected_info)
        return template.format(collected_info=info_text)
    
    @staticmethod
    def get_quality_review_prompt(content: str) -> str:
        """获取质量审核提示词"""
        return PromptTemplates.QUALITY_REVIEW.format(content=content)
    
    @staticmethod
    def get_structure_optimization_prompt(content: str) -> str:
        """获取结构优化提示词"""
        return PromptTemplates.STRUCTURE_OPTIMIZATION.format(content=content)
    
    @staticmethod
    def get_model_collaboration_prompt(role: str, **kwargs) -> str:
        """获取多模型协作提示词"""
        template = PromptTemplates.MODEL_COLLABORATION.get(role, "")
        return template.format(**kwargs)
    
    @staticmethod
    def _format_collected_info(collected_info: Dict) -> str:
        """格式化已收集的信息"""
        if not collected_info:
            return "暂无收集的信息"
        
        formatted = []
        for key, value in collected_info.items():
            if value:
                formatted.append(f"**{key}**: {value}")
        
        return "\n".join(formatted) if formatted else "暂无收集的信息"


class PromptBuilder:
    """提示词构建器"""
    
    def __init__(self):
        self.templates = PromptTemplates()
    
    def build_system_message(self, role: str = None) -> Dict[str, str]:
        """
        构建系统消息
        
        Args:
            role: 角色描述
            
        Returns:
            系统消息字典
        """
        content = role or PromptTemplates.SYSTEM_ROLE
        return {"role": "system", "content": content}
    
    def build_information_collection_message(self, stage: str, collected_info: Dict = None) -> str:
        """
        构建信息收集消息
        
        Args:
            stage: 当前阶段
            collected_info: 已收集的信息
            
        Returns:
            消息内容
        """
        base_prompt = PromptTemplates.get_information_collection_prompt(stage)
        
        if collected_info and any(collected_info.values()):
            info_summary = "\n\n**您已提供的信息：**\n" + PromptTemplates._format_collected_info(collected_info)
            return base_prompt + info_summary
        
        return base_prompt
    
    def build_content_generation_message(self, section: str, collected_info: Dict) -> str:
        """
        构建内容生成消息
        
        Args:
            section: 论文章节
            collected_info: 已收集的信息
            
        Returns:
            消息内容
        """
        return PromptTemplates.get_content_generation_prompt(section, collected_info)
    
    def build_review_message(self, content: str) -> str:
        """
        构建审核消息
        
        Args:
            content: 待审核内容
            
        Returns:
            消息内容
        """
        return PromptTemplates.get_quality_review_prompt(content)
    
    def build_optimization_message(self, content: str) -> str:
        """
        构建优化消息
        
        Args:
            content: 待优化内容
            
        Returns:
            消息内容
        """
        return PromptTemplates.get_structure_optimization_prompt(content)


# 全局提示词构建器实例
prompt_builder = PromptBuilder()
