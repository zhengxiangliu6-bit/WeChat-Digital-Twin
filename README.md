# crj AI Digital Twin

基于微信聊天记录蒸馏的 crj（陈荣君）AI 数字分身聊天程序。

**这不是 crj 本人，是基于聊天风格训练的 AI 模拟。**

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API

复制 `.env.example` 为 `.env`，填入你的 API 配置：

```bash
copy .env.example .env
```

支持任何 OpenAI Chat Completions 兼容接口（OpenAI、DeepSeek 等）。

### 3. 启动

双击 `start.bat`，或运行：

```bash
python -m streamlit run app/main.py
```

浏览器自动打开 `http://localhost:8501`。

## 项目结构

```
app/
  main.py        # Streamlit 聊天界面
  persona.py     # 人物档案加载
  llm.py         # API 调用
  database.py    # SQLite 对话存储
output/friend/   # crj 人物 Skill 文件
.env             # API 配置（不提交 git）
```
