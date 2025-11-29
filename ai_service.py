"""
AI服务接口层 - 支持Ollama和自定义API
"""
import os
import requests
import json
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
from dotenv import load_dotenv

load_dotenv()


class AIServiceBase(ABC):
    """AI服务基类"""
    
    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: int = 4000) -> str:
        """发送聊天请求"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """检查服务是否可用"""
        pass


class OllamaService(AIServiceBase):
    """Ollama服务"""
    
    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = model or os.getenv("OLLAMA_DEFAULT_MODEL", "llama2")
        
    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: int = 4000) -> str:
        """
        发送聊天请求到Ollama
        
        Args:
            messages: 消息列表，格式 [{"role": "user", "content": "..."}]
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            模型响应文本
        """
        try:
            url = f"{self.base_url}/api/chat"
            
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            return result.get("message", {}).get("content", "")
            
        except Exception as e:
            raise Exception(f"Ollama服务调用失败: {str(e)}")
    
    def is_available(self) -> bool:
        """检查Ollama服务是否可用"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False


class CustomAPIService(AIServiceBase):
    """自定义API服务 - 兼容OpenAI格式的API"""
    
    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.model = model
        
    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: int = 4000) -> str:
        """
        发送聊天请求到自定义API
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            模型响应文本
        """
        try:
            url = f"{self.base_url}/chat/completions"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            return result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
        except Exception as e:
            raise Exception(f"自定义API服务调用失败 ({self.model}): {str(e)}")
    
    def is_available(self) -> bool:
        """检查自定义API服务是否可用"""
        try:
            url = f"{self.base_url}/models"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.get(url, headers=headers, timeout=5)
            return response.status_code == 200
        except:
            return False


class AIServiceManager:
    """AI服务管理器 - 管理多个AI服务"""
    
    def __init__(self):
        self.services: Dict[str, AIServiceBase] = {}
        self._load_services()
        
    def _load_services(self):
        """从环境变量加载所有可用的AI服务"""
        # 加载Ollama服务
        if os.getenv("OLLAMA_BASE_URL"):
            ollama = OllamaService()
            if ollama.is_available():
                self.services["ollama"] = ollama
                print("✓ Ollama服务已加载")
        
        # 加载自定义API服务
        i = 1
        while True:
            api_key = os.getenv(f"API_KEY_{i}")
            api_base_url = os.getenv(f"API_BASE_URL_{i}")
            api_model = os.getenv(f"API_MODEL_{i}")
            
            if not all([api_key, api_base_url, api_model]):
                break
            
            try:
                service = CustomAPIService(api_key, api_base_url, api_model)
                service_name = f"api_{i}_{api_model}"
                self.services[service_name] = service
                print(f"✓ 自定义API服务已加载: {service_name}")
            except Exception as e:
                print(f"✗ 自定义API服务加载失败 (API_{i}): {str(e)}")
            
            i += 1
        
        if not self.services:
            print("⚠ 警告: 没有可用的AI服务，请检查配置")
    
    def get_service(self, service_name: str = None) -> Optional[AIServiceBase]:
        """
        获取指定的AI服务
        
        Args:
            service_name: 服务名称，如果为None则返回第一个可用服务
            
        Returns:
            AI服务实例
        """
        if service_name:
            return self.services.get(service_name)
        
        # 返回第一个可用服务
        if self.services:
            return list(self.services.values())[0]
        
        return None
    
    def get_all_services(self) -> Dict[str, AIServiceBase]:
        """获取所有可用的AI服务"""
        return self.services
    
    def get_service_names(self) -> List[str]:
        """获取所有服务名称"""
        return list(self.services.keys())
    
    def chat(self, messages: List[Dict[str, str]], service_name: str = None, 
             temperature: float = 0.7, max_tokens: int = 4000) -> str:
        """
        使用指定服务进行对话
        
        Args:
            messages: 消息列表
            service_name: 服务名称
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            模型响应文本
        """
        service = self.get_service(service_name)
        if not service:
            raise Exception("没有可用的AI服务")
        
        return service.chat(messages, temperature, max_tokens)


# 全局服务管理器实例
ai_service_manager = AIServiceManager()
