#!/bin/bash

# ============================================
# 星海论文智能体 - macOS/Linux启动脚本
# 版本: 1.0.0
# 作者: 星海团队
# ============================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 清屏
clear

# 显示欢迎信息
echo -e "${CYAN}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║              ✨ 星海论文智能体 启动向导 ✨                ║"
echo "║                                                            ║"
echo "║                    基于多模型协作的                        ║"
echo "║                  学术论文智能生成系统                      ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# 检查Python环境
echo -e "${BLUE}[1/6]${NC} 正在检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ 错误: 未检测到Python3环境！${NC}"
    echo ""
    echo "请先安装Python 3.8或更高版本："
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "  brew install python3"
    else
        echo "  sudo apt-get install python3 python3-pip"
    fi
    echo ""
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "   ${GREEN}✓${NC} Python ${PYTHON_VERSION} 已安装"
echo ""

# 检查虚拟环境
echo -e "${BLUE}[2/6]${NC} 正在检查虚拟环境..."
if [ ! -d "venv" ]; then
    echo -e "   ${YELLOW}⚠${NC} 未找到虚拟环境，正在创建..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ 创建虚拟环境失败！${NC}"
        exit 1
    fi
    echo -e "   ${GREEN}✓${NC} 虚拟环境创建成功"
else
    echo -e "   ${GREEN}✓${NC} 虚拟环境已存在"
fi
echo ""

# 激活虚拟环境
echo -e "${BLUE}[3/6]${NC} 正在激活虚拟环境..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 激活虚拟环境失败！${NC}"
    exit 1
fi
echo -e "   ${GREEN}✓${NC} 虚拟环境已激活"
echo ""

# 检查并安装依赖
echo -e "${BLUE}[4/6]${NC} 正在检查依赖包..."
if ! python3 -c "import flask" 2>/dev/null; then
    echo -e "   ${YELLOW}⚠${NC} 检测到缺少依赖，正在安装..."
    # 尝试使用清华镜像
    pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple 2>/dev/null || \
    pip3 install -r requirements.txt
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ 依赖安装失败！${NC}"
        exit 1
    fi
    echo -e "   ${GREEN}✓${NC} 依赖安装完成"
else
    echo -e "   ${GREEN}✓${NC} 依赖已安装"
fi
echo ""

# 检查配置文件
echo -e "${BLUE}[5/6]${NC} 正在检查配置文件..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo -e "   ${YELLOW}⚠${NC} 未找到.env配置文件，正在从模板创建..."
        cp .env.example .env
        echo -e "   ${GREEN}✓${NC} 配置文件已创建（.env）"
        echo ""
        echo -e "   ${YELLOW}⚠${NC} 提示: 请编辑 .env 文件配置您的AI服务"
        echo ""
    else
        echo -e "   ${YELLOW}⚠${NC} 未找到配置文件，将使用默认配置"
    fi
else
    echo -e "   ${GREEN}✓${NC} 配置文件已存在"
fi
echo ""

# 检查数据目录
if [ ! -d "data/sessions" ]; then
    echo "   正在创建数据目录..."
    mkdir -p data/sessions
    echo -e "   ${GREEN}✓${NC} 数据目录已创建"
fi

# 检查Ollama服务（可选）
echo -e "${BLUE}[6/6]${NC} 正在检查Ollama服务..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "   ${GREEN}✓${NC} Ollama服务运行中"
    echo ""
else
    echo -e "   ${YELLOW}⚠${NC} Ollama服务未运行（可选）"
    echo ""
    echo "如需使用本地AI模型，请先启动Ollama:"
    echo "  1. 访问 https://ollama.ai 下载安装"
    echo "  2. 运行命令: ollama serve"
    echo "  3. 下载模型: ollama pull qwen2.5:7b"
    echo ""
    echo "或使用自定义API服务（配置.env文件）"
    echo ""
fi

# 显示启动信息
echo -e "${GREEN}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                    🚀 准备启动服务                         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# 读取端口配置
PORT=5006
if [ -f ".env" ]; then
    PORT=$(grep "FLASK_PORT" .env 2>/dev/null | cut -d '=' -f2 | tr -d ' ' || echo "5006")
fi

echo -e "   ${CYAN}📍 服务地址:${NC} http://localhost:${PORT}"
echo -e "   ${CYAN}🔧 调试模式:${NC} 开启"
echo -e "   ${CYAN}💾 数据目录:${NC} data/sessions/"
echo ""
echo "提示: "
echo "  - 按 Ctrl+C 可停止服务"
echo "  - 浏览器将自动打开访问地址"
echo "  - 首次启动可能需要几秒钟"
echo ""
echo "════════════════════════════════════════════════════════════"
echo ""

# 等待2秒后启动浏览器
sleep 2

# 根据操作系统打开浏览器
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open "http://localhost:${PORT}" 2>/dev/null &
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    if command -v xdg-open &> /dev/null; then
        xdg-open "http://localhost:${PORT}" 2>/dev/null &
    elif command -v gnome-open &> /dev/null; then
        gnome-open "http://localhost:${PORT}" 2>/dev/null &
    fi
fi

# 启动Flask应用
echo "正在启动星海论文智能体..."
echo ""
python3 app.py

# 如果服务异常退出
if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}"
    echo "════════════════════════════════════════════════════════════"
    echo ""
    echo "❌ 服务启动失败！"
    echo ""
    echo "可能的原因:"
    echo "  1. 端口 ${PORT} 已被占用"
    echo "  2. 配置文件存在错误"
    echo "  3. Python依赖缺失"
    echo ""
    echo "解决方案:"
    echo "  1. 修改 .env 中的 FLASK_PORT 配置"
    echo "  2. 检查 .env 和 config.yaml 配置"
    echo "  3. 重新运行: pip3 install -r requirements.txt"
    echo ""
    echo "════════════════════════════════════════════════════════════"
    echo -e "${NC}"
    echo ""
    exit 1
fi
