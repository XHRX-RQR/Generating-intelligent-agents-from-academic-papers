"""
多模型协作引擎
"""
import yaml
from typing import Dict, List, Any, Optional
from ai_service import ai_service_manager, AIServiceBase
from prompt_templates import PromptTemplates


class ModelRole:
    """模型角色定义"""
    INFORMATION_COLLECTOR = "information_collector"
    CONTENT_GENERATOR = "content_generator"
    QUALITY_REVIEWER = "quality_reviewer"
    STRUCTURE_OPTIMIZER = "structure_optimizer"


class MultiModelCollaborationEngine:
    """多模型协作引擎"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.service_manager = ai_service_manager
        self.role_config = self.config.get("model_collaboration", {}).get("roles", {})
        
        # 为不同角色分配不同的服务（如果有多个服务可用）
        self.role_service_mapping = self._assign_services_to_roles()
    
    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"加载配置文件失败: {str(e)}")
            return {}
    
    def _assign_services_to_roles(self) -> Dict[str, str]:
        """为不同角色分配AI服务"""
        services = self.service_manager.get_service_names()
        
        if not services:
            return {}
        
        # 如果只有一个服务，所有角色使用同一个服务
        if len(services) == 1:
            service_name = services[0]
            return {
                ModelRole.INFORMATION_COLLECTOR: service_name,
                ModelRole.CONTENT_GENERATOR: service_name,
                ModelRole.QUALITY_REVIEWER: service_name,
                ModelRole.STRUCTURE_OPTIMIZER: service_name
            }
        
        # 如果有多个服务，分配不同的服务给不同角色
        mapping = {}
        roles = [
            ModelRole.INFORMATION_COLLECTOR,
            ModelRole.CONTENT_GENERATOR,
            ModelRole.QUALITY_REVIEWER,
            ModelRole.STRUCTURE_OPTIMIZER
        ]
        
        for i, role in enumerate(roles):
            mapping[role] = services[i % len(services)]
        
        return mapping
    
    def collect_information(self, 
                          current_stage: str,
                          collected_info: Dict[str, Any],
                          conversation_history: List[Dict[str, str]] = None) -> str:
        """
        信息收集角色：分析已收集信息，生成引导性问题
        
        Args:
            current_stage: 当前阶段
            collected_info: 已收集的信息
            conversation_history: 对话历史
            
        Returns:
            引导性问题或反馈
        """
        # 获取角色配置
        role_config = self.role_config.get(ModelRole.INFORMATION_COLLECTOR, {})
        temperature = role_config.get("temperature", 0.7)
        
        # 构建提示词
        collected_info_text = self._format_collected_info(collected_info)
        prompt = PromptTemplates.get_model_collaboration_prompt(
            ModelRole.INFORMATION_COLLECTOR,
            collected_info=collected_info_text,
            current_stage=current_stage
        )
        
        # 构建消息
        messages = []
        
        # 添加系统角色
        system_role = role_config.get("description", "信息收集专家")
        messages.append({"role": "system", "content": system_role})
        
        # 添加对话历史（如果有）
        if conversation_history:
            messages.extend(conversation_history[-6:])  # 只保留最近3轮对话
        
        # 添加当前提示
        messages.append({"role": "user", "content": prompt})
        
        # 调用AI服务
        service_name = self.role_service_mapping.get(ModelRole.INFORMATION_COLLECTOR)
        try:
            response = self.service_manager.chat(
                messages=messages,
                service_name=service_name,
                temperature=temperature,
                max_tokens=2000
            )
            return response
        except Exception as e:
            return f"信息收集失败: {str(e)}"
    
    def generate_content(self,
                        section: str,
                        collected_info: Dict[str, Any],
                        requirements: str = "") -> str:
        """
        内容生成角色：基于收集的信息生成论文内容
        
        Args:
            section: 论文章节
            collected_info: 已收集的信息
            requirements: 额外要求
            
        Returns:
            生成的内容
        """
        # 获取角色配置
        role_config = self.role_config.get(ModelRole.CONTENT_GENERATOR, {})
        temperature = role_config.get("temperature", 0.8)
        
        # 构建提示词
        collected_info_text = self._format_collected_info(collected_info)
        
        # 获取章节生成模板
        prompt = PromptTemplates.get_content_generation_prompt(section, collected_info)
        
        if requirements:
            prompt += f"\n\n额外要求：\n{requirements}"
        
        # 构建消息
        messages = []
        
        # 添加系统角色
        system_role = role_config.get("description", "内容生成专家")
        messages.append({"role": "system", "content": system_role})
        
        # 添加生成请求
        messages.append({"role": "user", "content": prompt})
        
        # 调用AI服务
        service_name = self.role_service_mapping.get(ModelRole.CONTENT_GENERATOR)
        try:
            response = self.service_manager.chat(
                messages=messages,
                service_name=service_name,
                temperature=temperature,
                max_tokens=4000
            )
            return response
        except Exception as e:
            return f"内容生成失败: {str(e)}"
    
    def review_quality(self, content: str, section: str = "") -> Dict[str, Any]:
        """
        质量审核角色：审核内容质量并提供改进建议
        
        Args:
            content: 待审核内容
            section: 内容所属章节
            
        Returns:
            审核结果，包含评分和建议
        """
        # 获取角色配置
        role_config = self.role_config.get(ModelRole.QUALITY_REVIEWER, {})
        temperature = role_config.get("temperature", 0.3)
        
        # 构建提示词
        prompt = PromptTemplates.get_quality_review_prompt(content)
        
        if section:
            prompt = f"请审核以下论文{section}部分的内容：\n\n" + prompt
        
        # 构建消息
        messages = []
        
        # 添加系统角色
        system_role = role_config.get("description", "质量审核专家")
        messages.append({"role": "system", "content": system_role})
        
        # 添加审核请求
        messages.append({"role": "user", "content": prompt})
        
        # 调用AI服务
        service_name = self.role_service_mapping.get(ModelRole.QUALITY_REVIEWER)
        try:
            response = self.service_manager.chat(
                messages=messages,
                service_name=service_name,
                temperature=temperature,
                max_tokens=3000
            )
            
            return {
                "review": response,
                "status": "success"
            }
        except Exception as e:
            return {
                "review": f"审核失败: {str(e)}",
                "status": "error"
            }
    
    def optimize_structure(self, content: str, section: str = "") -> str:
        """
        结构优化角色：优化内容结构和逻辑
        
        Args:
            content: 待优化内容
            section: 内容所属章节
            
        Returns:
            优化建议或优化后的内容
        """
        # 获取角色配置
        role_config = self.role_config.get(ModelRole.STRUCTURE_OPTIMIZER, {})
        temperature = role_config.get("temperature", 0.5)
        
        # 构建提示词
        prompt = PromptTemplates.get_structure_optimization_prompt(content)
        
        if section:
            prompt = f"请优化以下论文{section}部分的结构：\n\n" + prompt
        
        # 构建消息
        messages = []
        
        # 添加系统角色
        system_role = role_config.get("description", "结构优化专家")
        messages.append({"role": "system", "content": system_role})
        
        # 添加优化请求
        messages.append({"role": "user", "content": prompt})
        
        # 调用AI服务
        service_name = self.role_service_mapping.get(ModelRole.STRUCTURE_OPTIMIZER)
        try:
            response = self.service_manager.chat(
                messages=messages,
                service_name=service_name,
                temperature=temperature,
                max_tokens=4000
            )
            return response
        except Exception as e:
            return f"结构优化失败: {str(e)}"
    
    def collaborative_generation(self,
                                section: str,
                                collected_info: Dict[str, Any],
                                iterations: int = 2) -> Dict[str, Any]:
        """
        协作生成：多个角色协作生成高质量内容
        
        Args:
            section: 论文章节
            collected_info: 已收集的信息
            iterations: 迭代次数
            
        Returns:
            生成结果，包含最终内容和过程记录
        """
        result = {
            "section": section,
            "final_content": "",
            "iterations": [],
            "status": "success"
        }
        
        try:
            # 第一步：生成初始内容
            print(f"生成{section}初始内容...")
            initial_content = self.generate_content(section, collected_info)
            
            current_content = initial_content
            result["iterations"].append({
                "iteration": 0,
                "type": "initial_generation",
                "content": initial_content
            })
            
            # 迭代优化
            for i in range(iterations):
                print(f"第{i+1}轮优化...")
                
                # 第二步：质量审核
                review_result = self.review_quality(current_content, section)
                result["iterations"].append({
                    "iteration": i + 1,
                    "type": "quality_review",
                    "content": review_result["review"]
                })
                
                # 第三步：结构优化
                optimized_content = self.optimize_structure(current_content, section)
                result["iterations"].append({
                    "iteration": i + 1,
                    "type": "structure_optimization",
                    "content": optimized_content
                })
                
                # 第四步：根据审核意见重新生成
                improvement_prompt = f"""
基于以下审核意见和优化建议，改进内容：

原始内容：
{current_content}

审核意见：
{review_result['review']}

优化建议：
{optimized_content}

请生成改进后的内容：
"""
                
                role_config = self.role_config.get(ModelRole.CONTENT_GENERATOR, {})
                messages = [
                    {"role": "system", "content": role_config.get("description", "内容生成专家")},
                    {"role": "user", "content": improvement_prompt}
                ]
                
                service_name = self.role_service_mapping.get(ModelRole.CONTENT_GENERATOR)
                improved_content = self.service_manager.chat(
                    messages=messages,
                    service_name=service_name,
                    temperature=0.7,
                    max_tokens=4000
                )
                
                current_content = improved_content
                result["iterations"].append({
                    "iteration": i + 1,
                    "type": "improved_generation",
                    "content": improved_content
                })
            
            result["final_content"] = current_content
            
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            result["final_content"] = current_content if 'current_content' in locals() else ""
        
        return result
    
    def _format_collected_info(self, collected_info: Dict[str, Any]) -> str:
        """格式化已收集的信息"""
        if not collected_info:
            return "暂无收集的信息"
        
        formatted = []
        for key, value in collected_info.items():
            if value:
                formatted.append(f"【{key}】\n{value}")
        
        return "\n\n".join(formatted) if formatted else "暂无收集的信息"
    
    def get_role_info(self) -> Dict[str, Dict[str, Any]]:
        """获取所有角色的配置信息"""
        return self.role_config
    
    def get_service_mapping(self) -> Dict[str, str]:
        """获取角色到服务的映射"""
        return self.role_service_mapping


# 全局多模型协作引擎实例
collaboration_engine = MultiModelCollaborationEngine()
