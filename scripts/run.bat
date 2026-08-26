@echo off
chcp 65001 >nul
cd /d %~dp0\..
echo [1/4] 检查 Python 虚拟环境...
if not exist .venv\Scripts\python.exe (
    echo 创建 .venv（Python 3.10）
    py -3.10 -m venv .venv
)
echo [2/4] 安装依赖...
call .venv\Scripts\activate.bat
pip install -r requirements.txt
echo [3/4] 启动 Web 服务...
echo 打开浏览器访问 http://127.0.0.1:8000
echo 按 Ctrl+C 停止
echo [4/4] 首次启动会自动导入 data/knowledge 示例知识库
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload