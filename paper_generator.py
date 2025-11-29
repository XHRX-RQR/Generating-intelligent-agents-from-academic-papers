"""
论文生成核心逻辑
"""
import yaml
from typing import Dict, List, Any, Optional
from datetime import datetime
from conversation_manager import ConversationManager, conversation_manager
from collaboration_engine import MultiModelCollaborationEngine, collaboration_engine
from prompt_templates import PromptBuilder, PromptTemplates


class PaperGenerationStage:
    """论文生成阶段"""
    INITIAL = "initial"
    RESEARCH_BACKGROUND = "research_background"
    METHODOLOGY = "methodology"
    RESULTS = "results"
    DISCUSSION = "discussion"
    LITERATURE_REVIEW = "literature_review"
    GENERATING = "generating"
    COMPLETED = "completed"


class PaperSection:
    """论文章节"""
    ABSTRACT = "abstract"
    INTRODUCTION = "introduction"
    LITERATURE_REVIEW = "literature_review"
    METHODOLOGY = "methodology"
    RESULTS = "results"
    DISCUSSION = "discussion"
    CONCLUSION = "conclusion"


class AcademicPaperGenerator:
    """学术论文生成器"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.conversation_manager = conversation_manager
        self.collaboration_engine = collaboration_engine
        self.prompt_builder = PromptBuilder()
        
        # 论文生成配置
        self.paper_config = self.config.get("paper_generation", {})
        self.max_rounds = self.paper_config.get("max_rounds", 15)
        self.min_rounds = self.paper_config.get("min_rounds", 5)
        self.sections_config = self.paper_config.get("sections", [])
        
        # 阶段流程定义
        self.stage_flow = [
            PaperGenerationStage.INITIAL,
            PaperGenerationStage.RESEARCH_BACKGROUND,
            PaperGenerationStage.METHODOLOGY,
            PaperGenerationStage.RESULTS,
            PaperGenerationStage.DISCUSSION,
            PaperGenerationStage.LITERATURE_REVIEW,
            PaperGenerationStage.GENERATING
        ]
    
    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"加载配置文件失败: {str(e)}")
            return {}
    
    def start_new_paper(self, user_id: str, title: str = "新论文项目") -> Dict[str, Any]:
        """
        开始新的论文生成项目
        
        Args:
            user_id: 用户ID
            title: 项目标题
            
        Returns:
            项目信息
        """
        # 创建新会话
        session = self.conversation_manager.create_session(user_id, title)
        
        # 添加初始系统消息
        self.conversation_manager.add_message(
            session.session_id,
            "system",
            PromptTemplates.SYSTEM_ROLE
        )
        
        # 生成初始引导消息
        initial_message = self.prompt_builder.build_information_collection_message(
            PaperGenerationStage.INITIAL
        )
        
        # 添加助手消息
        self.conversation_manager.add_message(
            session.session_id,
            "assistant",
            initial_message
        )
        
        return {
            "session_id": session.session_id,
            "stage": PaperGenerationStage.INITIAL,
            "message": initial_message,
            "round": 1
        }
    
    def process_user_input(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """
        处理用户输入
        
        Args:
            session_id: 会话ID
            user_input: 用户输入
            
        Returns:
            响应信息
        """
        # 获取会话
        session = self.conversation_manager.get_session(session_id)
        if not session:
            return {"error": "会话不存在"}
        
        # 添加用户消息
        self.conversation_manager.add_message(session_id, "user", user_input)
        
        # 获取当前上下文
        context = self.conversation_manager.get_context(session_id)
        current_stage = context.get("current_stage", PaperGenerationStage.INITIAL)
        collected_info = context.get("collected_info", {})
        
        # 提取用户输入中的信息
        extracted_info = self._extract_information(user_input, current_stage)
        collected_info.update(extracted_info)
        
        # 更新上下文
        self.conversation_manager.update_context(session_id, {
            "collected_info": collected_info
        })
        
        # 获取当前轮次
        current_round = len(session.messages) // 2
        
        # 判断是否需要继续收集信息
        if current_round < self.min_rounds:
            # 继续收集信息
            response = self._continue_information_collection(
                session_id, 
                current_stage, 
                collected_info,
                current_round
            )
        else:
            # 检查信息完整性
            completeness = self._check_information_completeness(collected_info)
            
            if completeness["is_complete"] or current_round >= self.max_rounds:
                # 信息收集完成，开始生成论文
                response = self._start_paper_generation(session_id, collected_info)
            else:
                # 继续收集缺失信息
                response = self._collect_missing_information(
                    session_id,
                    collected_info,
                    completeness["missing_info"]
                )
        
        return response
    
    def _extract_information(self, user_input: str, stage: str) -> Dict[str, Any]:
        """
        从用户输入中提取信息
        
        Args:
            user_input: 用户输入
            stage: 当前阶段
            
        Returns:
            提取的信息
        """
        # 使用AI提取结构化信息
        extraction_prompt = f"""
请从以下用户输入中提取学术论文相关的信息，并以结构化方式返回：

用户输入：
{user_input}

当前阶段：{stage}

请提取以下类型的信息（如果有）：
- 研究主题
- 研究背景
- 研究目标
- 研究方法
- 数据来源
- 研究发现
- 理论基础
- 文献引用
- 研究问题
- 研究意义
- 研究局限
- 未来方向

请以JSON格式返回提取的信息，例如：
{{
    "研究主题": "...",
    "研究背景": "...",
    ...
}}

如果某项信息不存在，请忽略该字段。
"""
        
        try:
            messages = [
                {"role": "system", "content": "你是信息提取专家，擅长从文本中提取结构化信息。"},
                {"role": "user", "content": extraction_prompt}
            ]
            
            response = self.collaboration_engine.service_manager.chat(
                messages=messages,
                temperature=0.3,
                max_tokens=1000
            )
            
            # 尝试解析JSON
            import json
            import re
            
            # 查找JSON块
            json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
            if json_match:
                try:
                    extracted = json.loads(json_match.group())
                    return extracted
                except:
                    pass
            
            # 如果无法解析JSON，返回原始输入作为"用户补充信息"
            return {"用户补充信息": user_input}
            
        except Exception as e:
            print(f"信息提取失败: {str(e)}")
            return {"用户补充信息": user_input}
    
    def _check_information_completeness(self, collected_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        检查收集信息的完整性
        
        Args:
            collected_info: 已收集的信息
            
        Returns:
            完整性检查结果
        """
        required_fields = [
            "研究主题", "研究背景", "研究目标", "研究方法",
            "数据来源", "研究发现"
        ]
        
        missing_info = []
        for field in required_fields:
            if field not in collected_info or not collected_info[field]:
                missing_info.append(field)
        
        return {
            "is_complete": len(missing_info) == 0,
            "missing_info": missing_info,
            "completeness_rate": (len(required_fields) - len(missing_info)) / len(required_fields)
        }
    
    def _continue_information_collection(self, 
                                        session_id: str,
                                        current_stage: str,
                                        collected_info: Dict[str, Any],
                                        current_round: int) -> Dict[str, Any]:
        """
        继续收集信息
        
        Args:
            session_id: 会话ID
            current_stage: 当前阶段
            collected_info: 已收集的信息
            current_round: 当前轮次
            
        Returns:
            响应信息
        """
        # 根据轮次切换阶段
        if current_round >= len(self.stage_flow):
            stage_index = len(self.stage_flow) - 1
        else:
            stage_index = current_round
        
        next_stage = self.stage_flow[min(stage_index, len(self.stage_flow) - 1)]
        
        # 更新阶段
        self.conversation_manager.update_context(session_id, {
            "current_stage": next_stage
        })
        
        # 使用多模型协作收集信息
        conversation_history = self.conversation_manager.get_messages_for_api(session_id, limit=6)
        
        response_message = self.collaboration_engine.collect_information(
            current_stage=next_stage,
            collected_info=collected_info,
            conversation_history=conversation_history
        )
        
        # 添加助手消息
        self.conversation_manager.add_message(session_id, "assistant", response_message)
        
        return {
            "session_id": session_id,
            "stage": next_stage,
            "message": response_message,
            "round": current_round + 1,
            "status": "collecting"
        }
    
    def _collect_missing_information(self,
                                    session_id: str,
                                    collected_info: Dict[str, Any],
                                    missing_info: List[str]) -> Dict[str, Any]:
        """
        收集缺失信息
        
        Args:
            session_id: 会话ID
            collected_info: 已收集的信息
            missing_info: 缺失的信息
            
        Returns:
            响应信息
        """
        missing_info_text = "、".join(missing_info)
        
        prompt = f"""
感谢您提供的详细信息！我注意到还需要补充一些关键信息，以便生成更完整的论文：

缺失的信息：{missing_info_text}

请补充这些信息，或者如果您认为现有信息已经足够，我可以开始生成论文。您希望：

1. 补充缺失的信息
2. 基于现有信息开始生成论文

请选择或直接提供补充信息。
"""
        
        # 添加助手消息
        self.conversation_manager.add_message(session_id, "assistant", prompt)
        
        return {
            "session_id": session_id,
            "stage": "collecting_missing",
            "message": prompt,
            "missing_info": missing_info,
            "status": "collecting"
        }
    
    def _start_paper_generation(self, session_id: str, collected_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        开始生成论文
        
        Args:
            session_id: 会话ID
            collected_info: 已收集的信息
            
        Returns:
            响应信息
        """
        # 更新会话状态
        self.conversation_manager.update_context(session_id, {
            "current_stage": PaperGenerationStage.GENERATING
        })
        
        # 发送生成开始通知
        notification = """
非常好！我已经收集到足够的信息。现在我将开始为您生成学术论文。

生成过程包括以下步骤：
1. 生成摘要（Abstract）
2. 生成引言（Introduction）
3. 生成文献综述（Literature Review）
4. 生成研究方法（Methodology）
5. 生成研究结果（Results）
6. 生成讨论（Discussion）
7. 生成结论（Conclusion）

整个过程可能需要几分钟时间，请稍候...
"""
        
        self.conversation_manager.add_message(session_id, "assistant", notification)
        
        # 开始生成论文（异步处理）
        paper_content = self._generate_full_paper(session_id, collected_info)
        
        # 保存论文内容
        self.conversation_manager.update_context(session_id, {
            "paper_content": paper_content,
            "current_stage": PaperGenerationStage.COMPLETED
        })
        
        # 更新会话状态
        self.conversation_manager.update_session_status(session_id, "completed")
        
        completion_message = """
论文生成完成！您可以在右侧查看完整的论文内容。

您可以：
1. 下载论文
2. 继续修改某个部分
3. 重新生成某个章节

请告诉我您的需求。
"""
        
        self.conversation_manager.add_message(session_id, "assistant", completion_message)
        
        return {
            "session_id": session_id,
            "stage": PaperGenerationStage.COMPLETED,
            "message": completion_message,
            "paper_content": paper_content,
            "status": "completed"
        }
    
    def _generate_full_paper(self, session_id: str, collected_info: Dict[str, Any]) -> Dict[str, str]:
        """
        生成完整论文
        
        Args:
            session_id: 会话ID
            collected_info: 已收集的信息
            
        Returns:
            论文内容字典
        """
        paper_content = {}
        
        sections = [
            PaperSection.ABSTRACT,
            PaperSection.INTRODUCTION,
            PaperSection.LITERATURE_REVIEW,
            PaperSection.METHODOLOGY,
            PaperSection.RESULTS,
            PaperSection.DISCUSSION,
            PaperSection.CONCLUSION
        ]
        
        for section in sections:
            print(f"正在生成 {section}...")
            
            # 使用多模型协作生成高质量内容
            result = self.collaboration_engine.collaborative_generation(
                section=section,
                collected_info=collected_info,
                iterations=1  # 可以根据需要调整迭代次数
            )
            
            paper_content[section] = result["final_content"]
            
            # 记录生成过程
            self.conversation_manager.update_context(session_id, {
                f"{section}_generation_process": result["iterations"]
            })
        
        return paper_content
    
    def regenerate_section(self, session_id: str, section: str, additional_requirements: str = "") -> Dict[str, Any]:
        """
        重新生成特定章节
        
        Args:
            session_id: 会话ID
            section: 章节名称
            additional_requirements: 额外要求
            
        Returns:
            生成结果
        """
        # 获取已收集的信息
        context = self.conversation_manager.get_context(session_id)
        collected_info = context.get("collected_info", {})
        
        # 重新生成
        result = self.collaboration_engine.collaborative_generation(
            section=section,
            collected_info=collected_info,
            iterations=1
        )
        
        # 更新论文内容
        paper_content = context.get("paper_content", {})
        paper_content[section] = result["final_content"]
        
        self.conversation_manager.update_context(session_id, {
            "paper_content": paper_content
        })
        
        return {
            "session_id": session_id,
            "section": section,
            "content": result["final_content"],
            "status": "success"
        }
    
    def get_paper_content(self, session_id: str) -> Optional[Dict[str, str]]:
        """
        获取论文内容
        
        Args:
            session_id: 会话ID
            
        Returns:
            论文内容
        """
        context = self.conversation_manager.get_context(session_id)
        return context.get("paper_content")
    
    def export_paper(self, session_id: str, format: str = "markdown") -> str:
        """
        导出论文
        
        Args:
            session_id: 会话ID
            format: 导出格式
            
        Returns:
            论文文本
        """
        paper_content = self.get_paper_content(session_id)
        
        if not paper_content:
            return ""
        
        if format == "markdown":
            return self._export_as_markdown(paper_content)
        elif format == "text":
            return self._export_as_text(paper_content)
        else:
            return self._export_as_markdown(paper_content)
    
    def _export_as_markdown(self, paper_content: Dict[str, str]) -> str:
        """导出为Markdown格式"""
        sections_order = [
            ("abstract", "摘要 (Abstract)"),
            ("introduction", "引言 (Introduction)"),
            ("literature_review", "文献综述 (Literature Review)"),
            ("methodology", "研究方法 (Methodology)"),
            ("results", "研究结果 (Results)"),
            ("discussion", "讨论 (Discussion)"),
            ("conclusion", "结论 (Conclusion)")
        ]
        
        markdown = "# 学术论文\n\n"
        markdown += f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        markdown += "---\n\n"
        
        for section_key, section_title in sections_order:
            if section_key in paper_content:
                markdown += f"## {section_title}\n\n"
                markdown += paper_content[section_key]
                markdown += "\n\n"
        
        return markdown
    
    def _export_as_text(self, paper_content: Dict[str, str]) -> str:
        """导出为纯文本格式"""
        sections_order = [
            ("abstract", "摘要"),
            ("introduction", "引言"),
            ("literature_review", "文献综述"),
            ("methodology", "研究方法"),
            ("results", "研究结果"),
            ("discussion", "讨论"),
            ("conclusion", "结论")
        ]
        
        text = "=" * 60 + "\n"
        text += "学术论文\n"
        text += f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        text += "=" * 60 + "\n\n"
        
        for section_key, section_title in sections_order:
            if section_key in paper_content:
                text += f"{section_title}\n"
                text += "-" * 60 + "\n\n"
                text += paper_content[section_key]
                text += "\n\n"
        
        return text


# 全局论文生成器实例
paper_generator = AcademicPaperGenerator()
