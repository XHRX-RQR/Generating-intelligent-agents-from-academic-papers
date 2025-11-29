@echo off
chcp 65001 >nul
title 星海论文智能体 - 启动向导

:: ============================================
:: 星海论文智能体 - Windows启动脚本
:: 版本: 1.0.0
:: 作者: 星海团队
:: ============================================

color 0B
echo.
echo ════════════════════════════════════════════════════════════
echo                                                             
echo               ✨ 星海论文智能体 启动向导 ✨                      
echo                                                            
echo                     基于多模型协作的                         
echo                  学术论文智能生成系统                      
echo                                                             
echo 
echo.

:: 检查Python是否安装
echo [1/6] 正在检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo.
    echo ❌ 错误: 未检测到Python环境！
    echo.
    echo 请先安装Python 3.8或更高版本：
    echo    https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo    ✓ Python %PYTHON_VERSION% 已安装
echo.

:: 检查虚拟环境
echo [2/6] 正在检查虚拟环境...
if not exist "venv\" (
    echo    ⚠ 未找到虚拟环境，正在创建...
    python -m venv venv
    if errorlevel 1 (
        color 0C
        echo    ❌ 创建虚拟环境失败！
        pause
        exit /b 1
    )
    echo    ✓ 虚拟环境创建成功
) else (
    echo    ✓ 虚拟环境已存在
)
echo.

:: 激活虚拟环境
echo [3/6] 正在激活虚拟环境...
call venv\Scripts\activate.bat
if errorlevel 1 (
    color 0C
    echo    ❌ 激活虚拟环境失败！
    pause
    exit /b 1
)
echo    ✓ 虚拟环境已激活
echo.

:: 检查并安装依赖
echo [4/6] 正在检查依赖包...
pip --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo    ❌ pip未找到！
    pause
    exit /b 1
)

:: 检查是否需要安装依赖
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo    ⚠ 检测到缺少依赖，正在安装...
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    if errorlevel 1 (
        echo    ⚠ 使用清华镜像失败，尝试默认源...
        pip install -r requirements.txt
        if errorlevel 1 (
            color 0C
            echo    ❌ 依赖安装失败！
            pause
            exit /b 1
        )
    )
    echo    ✓ 依赖安装完成
) else (
    echo    ✓ 依赖已安装
)
echo.

:: 检查配置文件
echo [5/6] 正在检查配置文件...
if not exist ".env" (
    if exist ".env.example" (
        echo    ⚠ 未找到.env配置文件，正在从模板创建...
        copy .env.example .env >nul
        echo    ✓ 配置文件已创建（.env）
        echo.
        echo    ⚠ 提示: 请编辑 .env 文件配置您的AI服务
        echo.
    ) else (
        echo    ⚠ 未找到配置文件，将使用默认配置
    )
) else (
    echo    ✓ 配置文件已存在
)
echo.

:: 检查数据目录
if not exist "data\sessions\" (
    echo    正在创建数据目录...
    mkdir data\sessions
    echo    ✓ 数据目录已创建
)

:: 检查Ollama服务（可选）
echo [6/6] 正在检查Ollama服务...
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    color 0E
    echo    ⚠ Ollama服务未运行（可选）
    echo.
    echo    如需使用本地AI模型，请先启动Ollama:
    echo      1. 访问 https://ollama.ai 下载安装
    echo      2. 运行命令: ollama serve
    echo      3. 下载模型: ollama pull qwen2.5:7b
    echo.
    echo    或使用自定义API服务（配置.env文件）
    echo.
) else (
    echo    ✓ Ollama服务运行中
    echo.
)

:: 显示启动信息
color 0A
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                    🚀 准备启动服务                         ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

:: 读取端口配置
set PORT=5006
if exist ".env" (
    for /f "tokens=2 delims==" %%a in ('findstr "FLASK_PORT" .env 2^>nul') do set PORT=%%a
)

echo    📍 服务地址: http://localhost:%PORT%
echo    🔧 调试模式: 开启
echo    💾 数据目录: data\sessions\
echo.
echo    提示: 
echo      - 按 Ctrl+C 可停止服务
echo      - 浏览器将自动打开访问地址
echo      - 首次启动可能需要几秒钟
echo.
echo ════════════════════════════════════════════════════════════
echo.

:: 等待2秒后启动浏览器
timeout /t 2 /nobreak >nul
start http://localhost:%PORT%

:: 启动Flask应用
echo 正在启动星海论文智能体...
echo.
python app.py

:: 如果服务异常退出
if errorlevel 1 (
    color 0C
    echo.
    echo ════════════════════════════════════════════════════════════
    echo.
    echo ❌ 服务启动失败！
    echo.
    echo 可能的原因:
    echo   1. 端口 %PORT% 已被占用
    echo   2. 配置文件存在错误
    echo   3. Python依赖缺失
    echo.
    echo 解决方案:
    echo   1. 修改 .env 中的 FLASK_PORT 配置
    echo   2. 检查 .env 和 config.yaml 配置
    echo   3. 重新运行: pip install -r requirements.txt
    echo.
    echo ════════════════════════════════════════════════════════════
    echo.
)

pause
