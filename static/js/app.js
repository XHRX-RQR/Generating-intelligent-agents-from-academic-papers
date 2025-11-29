/**
 * 学术论文智能体 - 前端应用
 */

// API基础URL
// 自动检测当前页面的端口
const API_BASE_URL = `${window.location.protocol}//${window.location.hostname}:${window.location.port}/api`;

// 全局状态
let currentSessionId = null;
let currentStage = null;

/**
 * 初始化应用
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('应用初始化...');
    loadServicesStatus();
    loadSessions();
});

/**
 * 加载AI服务状态
 */
async function loadServicesStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/services`);
        const data = await response.json();
        
        const statusDiv = document.getElementById('servicesStatus');
        
        if (data.services && data.services.length > 0) {
            statusDiv.innerHTML = data.services.map(service => `
                <div class="service-item">
                    <span class="service-indicator"></span>
                    <span>${service}</span>
                </div>
            `).join('');
        } else {
            statusDiv.innerHTML = '<p style="color: #ef4444;">无可用服务</p>';
        }
    } catch (error) {
        console.error('加载服务状态失败:', error);
        document.getElementById('servicesStatus').innerHTML = 
            '<p style="color: #ef4444;">无法连接服务器</p>';
    }
}

/**
 * 加载会话列表
 */
async function loadSessions() {
    try {
        const response = await fetch(`${API_BASE_URL}/paper/sessions`);
        const result = await response.json();
        
        const sessionsList = document.getElementById('sessionsList');
        
        if (result.success && result.data.length > 0) {
            sessionsList.innerHTML = result.data.map(session => `
                <div class="session-item ${session.session_id === currentSessionId ? 'active' : ''}" 
                     onclick="loadSession('${session.session_id}')">
                    <div class="session-item-content">
                        <h4>${escapeHtml(session.title)}</h4>
                        <p>状态: ${getStatusText(session.status)} | ${session.message_count} 条消息</p>
                        <p style="font-size: 11px;">${formatDate(session.updated_at)}</p>
                    </div>
                    <button class="btn-delete" onclick="event.stopPropagation(); deleteSession('${session.session_id}', '${escapeHtml(session.title)}')" title="删除项目">
                        🗑️
                    </button>
                </div>
            `).join('');
        } else {
            sessionsList.innerHTML = '<p class="empty-message">暂无项目</p>';
        }
    } catch (error) {
        console.error('加载会话列表失败:', error);
    }
}

/**
 * 打开新建项目对话框
 */
function startNewPaper() {
    document.getElementById('newPaperModal').classList.add('show');
}

/**
 * 关闭新建项目对话框
 */
function closeNewPaperModal() {
    document.getElementById('newPaperModal').classList.remove('show');
}

/**
 * 确认新建项目（使用表单数据）
 */
async function confirmNewPaperWithForm() {
    const form = document.getElementById('paperInfoForm');
    
    // 验证表单
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }
    
    // 收集表单数据
    const formData = new FormData(form);
    const title = document.getElementById('paperTitle').value.trim();
    const userId = document.getElementById('userId').value.trim() || 'default_user';
    
    // 构建已收集信息
    const collectedInfo = {};
    for (let [key, value] of formData.entries()) {
        if (key !== 'title' && key !== 'userId' && value.trim()) {
            collectedInfo[key] = value.trim();
        }
    }
    
    closeNewPaperModal();
    showLoading('创建项目中...');
    
    try {
        // 创建项目
        const response = await fetch(`${API_BASE_URL}/paper/start`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                user_id: userId, 
                title: title,
                collected_info: collectedInfo,
                skip_conversation: true  // 跳过对话，直接生成
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            currentSessionId = result.data.session_id;
            
            // 更新UI
            document.getElementById('chatTitle').textContent = title;
            document.getElementById('currentStage').textContent = '生成中';
            document.getElementById('roundInfo').textContent = '';
            
            // 清空对话区
            const messagesDiv = document.getElementById('chatMessages');
            messagesDiv.innerHTML = '';
            
            // 显示已收集信息
            addMessage('system', '已收集以下研究信息，即将开始生成论文...');
            
            let infoSummary = '✔️ 基本信息\n';
            for (let [key, value] of Object.entries(collectedInfo)) {
                infoSummary += `  • ${key}\n`;
            }
            addMessage('assistant', infoSummary);
            
            // 禁用输入（生成过程中不需要用户输入）
            document.getElementById('userInput').disabled = true;
            document.getElementById('sendButton').disabled = true;
            
            // 刷新会话列表
            loadSessions();
            
            hideLoading();
            
            // 开始生成论文
            showLoading('正在生成论文，请稍候（约 3-10 分钟）...');
            generatePaperDirectly(currentSessionId);
            
        } else {
            alert('创建项目失败: ' + result.error);
            hideLoading();
        }
    } catch (error) {
        console.error('创建项目失败:', error);
        alert('创建项目失败，请检查服务器连接');
        hideLoading();
    }
}

/**
 * 直接生成论文（不经过多轮对话）
 */
async function generatePaperDirectly(sessionId) {
    try {
        const response = await fetch(`${API_BASE_URL}/paper/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ session_id: sessionId })
        });
        
        const result = await response.json();
        
        if (result.success) {
            hideLoading();
            
            // 显示生成完成消息
            addMessage('assistant', '论文生成完成！您可以在右侧查看完整的论文内容。');
            
            // 显示论文内容
            if (result.data.paper_content) {
                displayPaperContent(result.data.paper_content);
                
                // 启用导出按钮
                document.getElementById('exportMarkdown').disabled = false;
                document.getElementById('exportText').disabled = false;
            }
            
            // 更新阶段
            document.getElementById('currentStage').textContent = '已完成';
            
        } else {
            hideLoading();
            addMessage('assistant', '论文生成失败: ' + (result.error || '未知错误'));
        }
    } catch (error) {
        hideLoading();
        console.error('生成论文失败:', error);
        addMessage('assistant', '论文生成失败，请检查服务器连接');
    }
}

/**
 * 发送消息
 */
async function sendMessage() {
    const input = document.getElementById('userInput');
    const message = input.value.trim();
    
    if (!message) {
        return;
    }
    
    if (!currentSessionId) {
        alert('请先创建项目');
        return;
    }
    
    // 添加用户消息到UI
    addMessage('user', message);
    
    // 清空输入框
    input.value = '';
    
    // 禁用输入
    input.disabled = true;
    document.getElementById('sendButton').disabled = true;
    
    showLoading('AI 思考中...');
    
    try {
        const response = await fetch(`${API_BASE_URL}/paper/message`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: currentSessionId,
                message: message
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            const data = result.data;
            
            // 更新阶段信息
            if (data.stage) {
                currentStage = data.stage;
                document.getElementById('currentStage').textContent = getStageText(data.stage);
            }
            
            if (data.round) {
                document.getElementById('roundInfo').textContent = `第 ${data.round} 轮`;
            }
            
            // 添加AI回复
            addMessage('assistant', data.message);
            
            // 如果论文生成完成，加载论文内容
            if (data.status === 'completed' && data.paper_content) {
                displayPaperContent(data.paper_content);
                
                // 启用导出按钮
                document.getElementById('exportMarkdown').disabled = false;
                document.getElementById('exportText').disabled = false;
            }
            
            // 重新启用输入
            input.disabled = false;
            document.getElementById('sendButton').disabled = false;
            input.focus();
        } else {
            alert('发送失败: ' + result.error);
            input.disabled = false;
            document.getElementById('sendButton').disabled = false;
        }
    } catch (error) {
        console.error('发送消息失败:', error);
        alert('发送失败，请检查服务器连接');
        input.disabled = false;
        document.getElementById('sendButton').disabled = false;
    } finally {
        hideLoading();
    }
}

/**
 * 加载会话
 */
async function loadSession(sessionId) {
    showLoading('加载会话中...');
    
    try {
        const response = await fetch(`${API_BASE_URL}/paper/session/${sessionId}`);
        const result = await response.json();
        
        if (result.success) {
            const session = result.data.session;
            const paperContent = result.data.paper_content;
            
            currentSessionId = sessionId;
            currentStage = session.context.current_stage;
            
            // 更新UI
            document.getElementById('chatTitle').textContent = session.title;
            document.getElementById('currentStage').textContent = getStageText(currentStage);
            
            const roundCount = Math.floor(session.messages.length / 2);
            document.getElementById('roundInfo').textContent = roundCount > 0 ? `第 ${roundCount} 轮` : '';
            
            // 清空并加载消息
            const messagesDiv = document.getElementById('chatMessages');
            messagesDiv.innerHTML = '';
            
            session.messages.forEach(msg => {
                if (msg.role !== 'system') {
                    addMessage(msg.role, msg.content, msg.timestamp, false);
                }
            });
            
            // 滚动到底部
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
            
            // 显示论文内容
            if (paperContent) {
                displayPaperContent(paperContent);
                document.getElementById('exportMarkdown').disabled = false;
                document.getElementById('exportText').disabled = false;
            } else {
                document.getElementById('paperContent').innerHTML = 
                    '<p class="empty-message">论文内容将在这里显示</p>';
                document.getElementById('exportMarkdown').disabled = true;
                document.getElementById('exportText').disabled = true;
            }
            
            // 启用输入
            if (session.status === 'active') {
                document.getElementById('userInput').disabled = false;
                document.getElementById('sendButton').disabled = false;
            } else {
                document.getElementById('userInput').disabled = true;
                document.getElementById('sendButton').disabled = true;
            }
            
            // 刷新会话列表
            loadSessions();
        } else {
            alert('加载会话失败: ' + result.error);
        }
    } catch (error) {
        console.error('加载会话失败:', error);
        alert('加载会话失败');
    } finally {
        hideLoading();
    }
}

/**
 * 删除会话
 */
async function deleteSession(sessionId, title) {
    // 确认删除
    if (!confirm(`确定要删除论文项目 "${title}" 吗？\n\n此操作不可恢复！`)) {
        return;
    }
    
    showLoading('删除中...');
    
    try {
        const response = await fetch(`${API_BASE_URL}/paper/session/${sessionId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            // 如果删除的是当前会话，清空界面
            if (sessionId === currentSessionId) {
                currentSessionId = null;
                currentStage = null;
                
                // 重置UI
                document.getElementById('chatTitle').textContent = '开始新的论文项目';
                document.getElementById('currentStage').textContent = '未开始';
                document.getElementById('roundInfo').textContent = '';
                
                // 清空消息
                const messagesDiv = document.getElementById('chatMessages');
                messagesDiv.innerHTML = `
                    <div class="welcome-message">
                        <h2>欢迎使用星海论文智能体</h2>
                        <p>我将通过多轮对话帮助您撰写高质量的学术论文。</p>
                        <p>点击左上角"新建论文项目"开始吧！</p>
                        
                        <div class="features">
                            <div class="feature">
                                <span class="feature-icon">🤖</span>
                                <h3>多模型协作</h3>
                                <p>多个AI模型分工协作，确保论文质量</p>
                            </div>
                            <div class="feature">
                                <span class="feature-icon">💬</span>
                                <h3>多轮对话</h3>
                                <p>通过引导式对话收集详细信息</p>
                            </div>
                            <div class="feature">
                                <span class="feature-icon">📝</span>
                                <h3>结构完整</h3>
                                <p>自动生成摘要、引言、方法等完整章节</p>
                            </div>
                            <div class="feature">
                                <span class="feature-icon">🔄</span>
                                <h3>迭代优化</h3>
                                <p>质量审核和结构优化，持续改进</p>
                            </div>
                        </div>
                    </div>
                `;
                
                // 清空论文内容
                document.getElementById('paperContent').innerHTML = 
                    '<p class="empty-message">论文内容将在这里显示</p>';
                
                // 禁用输入和导出
                document.getElementById('userInput').disabled = true;
                document.getElementById('sendButton').disabled = true;
                document.getElementById('exportMarkdown').disabled = true;
                document.getElementById('exportText').disabled = true;
            }
            
            // 刷新会话列表
            await loadSessions();
            
        } else {
            alert('删除失败: ' + result.error);
        }
    } catch (error) {
        console.error('删除会话失败:', error);
        alert('删除失败，请检查服务器连接');
    } finally {
        hideLoading();
    }
}

/**
 * 添加消息到聊天区
 */
function addMessage(role, content, timestamp = null, scroll = true) {
    const messagesDiv = document.getElementById('chatMessages');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const time = timestamp ? new Date(timestamp) : new Date();
    const timeStr = formatTime(time);
    
    messageDiv.innerHTML = `
        <div class="message-header">
            <span class="message-role">${getRoleText(role)}</span>
            <span class="message-time">${timeStr}</span>
        </div>
        <div class="message-content">${escapeHtml(content).replace(/\n/g, '<br>')}</div>
    `;
    
    messagesDiv.appendChild(messageDiv);
    
    if (scroll) {
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }
}

/**
 * 显示论文内容
 */
function displayPaperContent(paperContent) {
    const contentDiv = document.getElementById('paperContent');
    
    const sections = [
        { key: 'abstract', title: '摘要 (Abstract)' },
        { key: 'introduction', title: '引言 (Introduction)' },
        { key: 'literature_review', title: '文献综述 (Literature Review)' },
        { key: 'methodology', title: '研究方法 (Methodology)' },
        { key: 'results', title: '研究结果 (Results)' },
        { key: 'discussion', title: '讨论 (Discussion)' },
        { key: 'conclusion', title: '结论 (Conclusion)' }
    ];
    
    let html = '';
    
    sections.forEach(section => {
        if (paperContent[section.key]) {
            html += `
                <div class="paper-section">
                    <h3>${section.title}</h3>
                    <div class="paper-section-content">${escapeHtml(paperContent[section.key])}</div>
                </div>
            `;
        }
    });
    
    if (html) {
        contentDiv.innerHTML = html;
    } else {
        contentDiv.innerHTML = '<p class="empty-message">论文内容为空</p>';
    }
}

/**
 * 导出论文
 */
async function exportPaper(format) {
    if (!currentSessionId) {
        alert('请先选择一个项目');
        return;
    }
    
    try {
        const url = `${API_BASE_URL}/paper/export/${currentSessionId}?format=${format}`;
        
        // 创建临时链接并触发下载
        const a = document.createElement('a');
        a.href = url;
        a.download = '';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    } catch (error) {
        console.error('导出失败:', error);
        alert('导出失败');
    }
}

/**
 * 显示加载动画
 */
function showLoading(text = '处理中...') {
    document.getElementById('loadingText').textContent = text;
    document.getElementById('loadingOverlay').style.display = 'flex';
}

/**
 * 隐藏加载动画
 */
function hideLoading() {
    document.getElementById('loadingOverlay').style.display = 'none';
}

/**
 * 获取角色显示文本
 */
function getRoleText(role) {
    const roleMap = {
        'user': '👤 用户',
        'assistant': '🤖 AI助手',
        'system': '⚙️ 系统'
    };
    return roleMap[role] || role;
}

/**
 * 获取阶段显示文本
 */
function getStageText(stage) {
    const stageMap = {
        'initial': '初始阶段',
        'research_background': '研究背景',
        'methodology': '研究方法',
        'results': '研究结果',
        'discussion': '讨论分析',
        'literature_review': '文献综述',
        'generating': '生成中',
        'completed': '已完成'
    };
    return stageMap[stage] || stage;
}

/**
 * 获取状态显示文本
 */
function getStatusText(status) {
    const statusMap = {
        'active': '进行中',
        'completed': '已完成',
        'abandoned': '已放弃'
    };
    return statusMap[status] || status;
}

/**
 * 格式化时间
 */
function formatTime(date) {
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    return `${hours}:${minutes}`;
}

/**
 * 格式化日期
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    
    // 小于1分钟
    if (diff < 60000) {
        return '刚刚';
    }
    
    // 小于1小时
    if (diff < 3600000) {
        const minutes = Math.floor(diff / 60000);
        return `${minutes}分钟前`;
    }
    
    // 小于24小时
    if (diff < 86400000) {
        const hours = Math.floor(diff / 3600000);
        return `${hours}小时前`;
    }
    
    // 其他情况显示日期
    const year = date.getFullYear();
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const day = date.getDate().toString().padStart(2, '0');
    return `${year}-${month}-${day}`;
}

/**
 * HTML转义
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * 回车发送消息
 */
document.addEventListener('DOMContentLoaded', function() {
    const input = document.getElementById('userInput');
    
    if (input) {
        input.addEventListener('keydown', function(e) {
            // Ctrl+Enter 或 Command+Enter 发送
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                e.preventDefault();
                sendMessage();
            }
        });
    }
});
