"""
多轮对话管理和会话存储
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum


class MessageRole(Enum):
    """消息角色"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class Message:
    """对话消息"""
    role: str
    content: str
    timestamp: str
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata or {}
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'Message':
        """从字典创建"""
        return Message(
            role=data["role"],
            content=data["content"],
            timestamp=data["timestamp"],
            metadata=data.get("metadata", {})
        )


@dataclass
class ConversationSession:
    """对话会话"""
    session_id: str
    user_id: str
    title: str
    messages: List[Message]
    context: Dict[str, Any]
    created_at: str
    updated_at: str
    status: str  # active, completed, abandoned
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "title": self.title,
            "messages": [msg.to_dict() for msg in self.messages],
            "context": self.context,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "status": self.status
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'ConversationSession':
        """从字典创建"""
        return ConversationSession(
            session_id=data["session_id"],
            user_id=data["user_id"],
            title=data["title"],
            messages=[Message.from_dict(msg) for msg in data["messages"]],
            context=data["context"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            status=data["status"]
        )


class ConversationManager:
    """对话管理器"""
    
    def __init__(self, storage_path: str = "./data/sessions"):
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)
        self.active_sessions: Dict[str, ConversationSession] = {}
    
    def create_session(self, user_id: str, title: str = "新论文项目") -> ConversationSession:
        """
        创建新会话
        
        Args:
            user_id: 用户ID
            title: 会话标题
            
        Returns:
            会话对象
        """
        session_id = f"{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        now = datetime.now().isoformat()
        
        session = ConversationSession(
            session_id=session_id,
            user_id=user_id,
            title=title,
            messages=[],
            context={
                "collected_info": {},
                "current_stage": "initial",
                "missing_info": [],
                "paper_outline": {}
            },
            created_at=now,
            updated_at=now,
            status="active"
        )
        
        self.active_sessions[session_id] = session
        self._save_session(session)
        
        return session
    
    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """
        获取会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话对象
        """
        # 先从内存中查找
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]
        
        # 从磁盘加载
        session = self._load_session(session_id)
        if session:
            self.active_sessions[session_id] = session
        
        return session
    
    def add_message(self, session_id: str, role: str, content: str, metadata: Dict = None) -> Message:
        """
        添加消息到会话
        
        Args:
            session_id: 会话ID
            role: 消息角色
            content: 消息内容
            metadata: 元数据
            
        Returns:
            消息对象
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"会话不存在: {session_id}")
        
        message = Message(
            role=role,
            content=content,
            timestamp=datetime.now().isoformat(),
            metadata=metadata or {}
        )
        
        session.messages.append(message)
        session.updated_at = datetime.now().isoformat()
        
        self._save_session(session)
        
        return message
    
    def get_messages(self, session_id: str, limit: int = None) -> List[Message]:
        """
        获取会话的消息列表
        
        Args:
            session_id: 会话ID
            limit: 限制返回数量
            
        Returns:
            消息列表
        """
        session = self.get_session(session_id)
        if not session:
            return []
        
        messages = session.messages
        if limit:
            messages = messages[-limit:]
        
        return messages
    
    def get_messages_for_api(self, session_id: str, limit: int = None) -> List[Dict[str, str]]:
        """
        获取适用于API调用的消息格式
        
        Args:
            session_id: 会话ID
            limit: 限制返回数量
            
        Returns:
            消息列表 [{"role": "user", "content": "..."}]
        """
        messages = self.get_messages(session_id, limit)
        return [{"role": msg.role, "content": msg.content} for msg in messages]
    
    def update_context(self, session_id: str, context_updates: Dict[str, Any]):
        """
        更新会话上下文
        
        Args:
            session_id: 会话ID
            context_updates: 上下文更新内容
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"会话不存在: {session_id}")
        
        session.context.update(context_updates)
        session.updated_at = datetime.now().isoformat()
        
        self._save_session(session)
    
    def get_context(self, session_id: str) -> Dict[str, Any]:
        """
        获取会话上下文
        
        Args:
            session_id: 会话ID
            
        Returns:
            上下文字典
        """
        session = self.get_session(session_id)
        if not session:
            return {}
        
        return session.context
    
    def update_session_status(self, session_id: str, status: str):
        """
        更新会话状态
        
        Args:
            session_id: 会话ID
            status: 新状态
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"会话不存在: {session_id}")
        
        session.status = status
        session.updated_at = datetime.now().isoformat()
        
        self._save_session(session)
    
    def list_sessions(self, user_id: str = None) -> List[ConversationSession]:
        """
        列出所有会话
        
        Args:
            user_id: 用户ID过滤
            
        Returns:
            会话列表
        """
        sessions = []
        
        for filename in os.listdir(self.storage_path):
            if filename.endswith('.json'):
                session_id = filename[:-5]
                session = self._load_session(session_id)
                
                if session:
                    if user_id is None or session.user_id == user_id:
                        sessions.append(session)
        
        # 按更新时间倒序排列
        sessions.sort(key=lambda x: x.updated_at, reverse=True)
        
        return sessions
    
    def delete_session(self, session_id: str):
        """
        删除会话
        
        Args:
            session_id: 会话ID
        """
        # 从内存中删除
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        
        # 从磁盘删除
        file_path = os.path.join(self.storage_path, f"{session_id}.json")
        if os.path.exists(file_path):
            os.remove(file_path)
    
    def _save_session(self, session: ConversationSession):
        """保存会话到磁盘"""
        file_path = os.path.join(self.storage_path, f"{session.session_id}.json")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(session.to_dict(), f, ensure_ascii=False, indent=2)
    
    def _load_session(self, session_id: str) -> Optional[ConversationSession]:
        """从磁盘加载会话"""
        file_path = os.path.join(self.storage_path, f"{session_id}.json")
        
        if not os.path.exists(file_path):
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return ConversationSession.from_dict(data)
        except Exception as e:
            print(f"加载会话失败 {session_id}: {str(e)}")
            return None
    
    def clear_old_sessions(self, days: int = 30):
        """
        清理旧会话
        
        Args:
            days: 保留天数
        """
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for session in self.list_sessions():
            updated_at = datetime.fromisoformat(session.updated_at)
            if updated_at < cutoff_date and session.status != "active":
                self.delete_session(session.session_id)


# 全局对话管理器实例
conversation_manager = ConversationManager()
