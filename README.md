# zzu-wlan

zzu校园网自动登录脚本

- 使用uv管理依赖
- 支持win，mac,linux
- 结构简单易使用

## 安装指南

### 安装python和uv
下载python，确保python版本应在3.11以上

https://www.python.org/downloads/

[安装uv](https://uv.oaix.tech/getting-started/installation)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 部署

克隆此项目
```bash
git clone https://github.com/lava-xa/zzu-wlan
```
将.env.example重命名为.env，并填写相应账号密码

### 安装依赖
```bash
uv venv
uv pip install -r requirements.txt
```
单次运行
```bash
uv run python main.py
```


## Windows 定时运行

在项目目录中打开 PowerShell 或 CMD，执行：

```bat
.\run-every-10s.bat
```

脚本会运行 `uv run python main.py`，命令结束后等待 10 秒再次运行。按 `Ctrl+C` 停止。

如果无法运行，检查python环境变量，如不是python3,可将.bat内python3换为python
