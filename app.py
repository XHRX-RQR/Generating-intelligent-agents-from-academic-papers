"""
Flask API服务 - 学术论文智能体后端
"""
from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import os
from dotenv import load_dotenv
from datetime import datetime
import io

from paper_generator import paper_generator
from conversation_manager import conversation_manager
from ai_service import ai_service_manager
from collaboration_engine import collaboration_engine

# 加载环境变量
load_dotenv()

# 创建Flask应用
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
CORS(app)  # 启用跨域支持

# 配置
app.config['JSON_AS_ASCII'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max request size


@app.route('/')
def index():
    """首页"""
    return render_template('index.html')


# ... existing code ...

@app.route('/api/')
def api_index():
    """首页"""
    return jsonify({
        "name": "学术论文智能体",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "start_paper": "/api/paper/start",
            "send_message": "/api/paper/message",
            "get_session": "/api/paper/session/<session_id>",
            "list_sessions": "/api/paper/sessions",
            "regenerate_section": "/api/paper/regenerate",
            "export_paper": "/api/paper/export/<session_id>",
            "get_services": "/api/services",
            "health": "/api/health"
        }
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    services = ai_service_manager.get_service_names()
    
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "ai_services": services,
        "ai_services_count": len(services)
    })


@app.route('/api/services', methods=['GET'])
def get_services():
    """获取可用的AI服务列表"""
    services = ai_service_manager.get_service_names()
    role_mapping = collaboration_engine.get_service_mapping()
    role_info = collaboration_engine.get_role_info()
    
    return jsonify({
        "services": services,
        "role_mapping": role_mapping,
        "role_info": role_info
    })


@app.route('/api/paper/start', methods=['POST'])
def start_paper():
    """开始新的论文项目"""
    try:
        data = request.json
        user_id = data.get('user_id', 'default_user')
        title = data.get('title', '新论文项目')
        collected_info = data.get('collected_info', {})  # 从表单收集的信息
        skip_conversation = data.get('skip_conversation', False)  # 是否跳过对话
        
        # 创建会话
        session = conversation_manager.create_session(user_id, title)
        
        # 如果有预填信息，直接更新上下文
        if collected_info:
            conversation_manager.update_context(session.session_id, {
                'collected_info': collected_info,
                'current_stage': 'generating' if skip_conversation else 'initial'
            })
        
        # 如果跳过对话，直接返回成功
        if skip_conversation:
            return jsonify({
                'success': True,
                'data': {
                    'session_id': session.session_id,
                    'stage': 'generating',
                    'message': '项目创建成功，即将开始生成论文'
                }
            })
        
        # 否则返回初始引导消息
        result = paper_generator.start_new_paper(user_id, title)
        return jsonify({
            'success': True,
            'data': result
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/paper/message', methods=['POST'])
def send_message():
    """发送用户消息"""
    try:
        data = request.json
        session_id = data.get('session_id')
        message = data.get('message')
        
        if not session_id or not message:
            return jsonify({
                "success": False,
                "error": "缺少session_id或message参数"
            }), 400
        
        result = paper_generator.process_user_input(session_id, message)
        
        return jsonify({
            "success": True,
            "data": result
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/paper/session/<session_id>', methods=['GET'])
def get_session(session_id):
    """获取会话详情"""
    try:
        session = conversation_manager.get_session(session_id)
        
        if not session:
            return jsonify({
                "success": False,
                "error": "会话不存在"
            }), 404
        
        # 获取论文内容
        paper_content = paper_generator.get_paper_content(session_id)
        
        return jsonify({
            "success": True,
            "data": {
                "session": session.to_dict(),
                "paper_content": paper_content
            }
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/paper/sessions', methods=['GET'])
def list_sessions():
    """获取会话列表"""
    try:
        user_id = request.args.get('user_id')
        
        sessions = conversation_manager.list_sessions(user_id)
        
        sessions_data = [
            {
                "session_id": s.session_id,
                "user_id": s.user_id,
                "title": s.title,
                "status": s.status,
                "created_at": s.created_at,
                "updated_at": s.updated_at,
                "message_count": len(s.messages)
            }
            for s in sessions
        ]
        
        return jsonify({
            "success": True,
            "data": sessions_data
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/paper/regenerate', methods=['POST'])
def regenerate_section():
    """重新生成论文章节"""
    try:
        data = request.json
        session_id = data.get('session_id')
        section = data.get('section')
        requirements = data.get('requirements', '')
        
        if not session_id or not section:
            return jsonify({
                'success': False,
                'error': '缺少session_id或section参数'
            }), 400
        
        result = paper_generator.regenerate_section(
            session_id, 
            section, 
            requirements
        )
        
        return jsonify({
            'success': True,
            'data': result
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/paper/generate', methods=['POST'])
def generate_paper():
    """直接生成完整论文（不经过多轮对话）"""
    try:
        data = request.json
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({
                'success': False,
                'error': '缺少session_id参数'
            }), 400
        
        # 获取已收集的信息
        context = conversation_manager.get_context(session_id)
        collected_info = context.get('collected_info', {})
        
        # 生成论文
        paper_content = paper_generator._generate_full_paper(session_id, collected_info)
        
        # 保存论文内容
        conversation_manager.update_context(session_id, {
            'paper_content': paper_content,
            'current_stage': 'completed'
        })
        
        # 更新会话状态
        conversation_manager.update_session_status(session_id, 'completed')
        
        return jsonify({
            'success': True,
            'data': {
                'paper_content': paper_content,
                'session_id': session_id
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/paper/export/<session_id>', methods=['GET'])
def export_paper(session_id):
    """导出论文"""
    try:
        format = request.args.get('format', 'markdown')
        
        # 获取论文内容
        content = paper_generator.export_paper(session_id, format)
        
        if not content:
            return jsonify({
                "success": False,
                "error": "论文内容不存在"
            }), 404
        
        # 设置文件名
        session = conversation_manager.get_session(session_id)
        filename = f"{session.title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if format == 'markdown':
            filename += '.md'
            mimetype = 'text/markdown'
        else:
            filename += '.txt'
            mimetype = 'text/plain'
        
        # 创建文件对象
        file_obj = io.BytesIO(content.encode('utf-8'))
        file_obj.seek(0)
        
        return send_file(
            file_obj,
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/paper/delete/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """删除会话"""
    try:
        conversation_manager.delete_session(session_id)
        
        return jsonify({
            "success": True,
            "message": "会话已删除"
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/paper/session/<session_id>', methods=['DELETE'])
def delete_session_by_id(session_id):
    """删除会话（与GET同路径，使用DELETE方法）"""
    try:
        conversation_manager.delete_session(session_id)
        
        return jsonify({
            "success": True,
            "message": "会话已删除"
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/paper/messages/<session_id>', methods=['GET'])
def get_messages(session_id):
    """获取会话消息列表"""
    try:
        messages = conversation_manager.get_messages(session_id)
        
        messages_data = [msg.to_dict() for msg in messages]
        
        return jsonify({
            "success": True,
            "data": messages_data
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/paper/content/<session_id>', methods=['GET'])
def get_paper_content(session_id):
    """获取论文内容"""
    try:
        paper_content = paper_generator.get_paper_content(session_id)
        
        if not paper_content:
            return jsonify({
                "success": False,
                "error": "论文内容不存在"
            }), 404
        
        return jsonify({
            "success": True,
            "data": paper_content
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return jsonify({
        "success": False,
        "error": "资源不存在"
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    return jsonify({
        "success": False,
        "error": "服务器内部错误"
    }), 500


if __name__ == '__main__':
    # 确保数据目录存在
    os.makedirs('./data/sessions', exist_ok=True)
    
    # 获取配置
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    print("=" * 60)
    print("学术论文智能体服务启动中...")
    print(f"服务地址: http://localhost:{port}")
    print(f"调试模式: {debug}")
    print("=" * 60)
    
    # 启动服务
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
