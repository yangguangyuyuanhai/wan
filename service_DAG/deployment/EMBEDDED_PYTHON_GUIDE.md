# 嵌入式Python部署指南

**适用场景**: 完全离线环境，无法安装Python

---

## 方案1：使用Python嵌入式版本（推荐）

### 1. 下载Python嵌入式包

访问 https://www.python.org/downloads/windows/

下载 "Windows embeddable package (64-bit)"

例如: `python-3.11.0-embed-amd64.zip`

### 2. 解压到项目目录

```
service_DAG/
├── python/              # 解压Python嵌入式包到这里
│   ├── python.exe
│   ├── python311.dll
│   └── ...
├── core/
├── plugins/
└── ...
```

### 3. 配置python._pth

编辑 `python/python311._pth`:

```
python311.zip
.
..
../core
../engine
../plugins
../Lib/site-packages
```

### 4. 安装pip

```bash
# 下载get-pip.py
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py

# 使用嵌入式Python安装pip
python/python.exe get-pip.py
```

### 5. 安装依赖

```bash
python/python.exe -m pip install -r requirements.txt --target=python/Lib/site-packages
```

### 6. 创建启动脚本

**run.bat**:
```batch
@echo off
set PYTHON_HOME=%~dp0python
%PYTHON_HOME%\python.exe main_optimized.py %*
```

---

## 方案2：使用构建脚本（自动化）

### 1. 运行构建脚本

```bash
python deployment/build_deployment.py
```

### 2. 手动添加Python嵌入式包

```bash
# 下载并解压Python嵌入式包到 dist/service_DAG/python/
cd dist/service_DAG
unzip python-3.11.0-embed-amd64.zip -d python/
```

### 3. 配置和安装

```bash
# 配置python._pth
echo python311.zip > python/python311._pth
echo . >> python/python311._pth
echo .. >> python/python311._pth
echo ../Lib/site-packages >> python/python311._pth

# 安装依赖到嵌入式Python
python/python.exe -m pip install --no-index --find-links=libs -r requirements.txt --target=python/Lib/site-packages
```

---

## 方案3：完全离线打包

### 准备工作（在有网络的机器上）

```bash
# 1. 构建部署包
python deployment/build_deployment.py

# 2. 下载Python嵌入式包
# 手动下载 python-3.11.0-embed-amd64.zip

# 3. 下载get-pip.py
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py

# 4. 打包所有文件
# dist/service_DAG/ + python嵌入式包 + get-pip.py
```

### 在离线机器上部署

```bash
# 1. 解压部署包
unzip service_DAG_offline.zip

# 2. 解压Python到python/目录
unzip python-3.11.0-embed-amd64.zip -d service_DAG/python/

# 3. 配置python._pth
cd service_DAG
notepad python/python311._pth
# 添加路径配置

# 4. 安装pip
python/python.exe get-pip.py --no-index --find-links=libs

# 5. 安装依赖
python/python.exe -m pip install --no-index --find-links=libs -r requirements.txt --target=python/Lib/site-packages

# 6. 运行
python/python.exe main_optimized.py
```

---

## 启动脚本示例

### run.bat (Windows)

```batch
@echo off
REM 使用嵌入式Python运行

set SCRIPT_DIR=%~dp0
set PYTHON_EXE=%SCRIPT_DIR%python\python.exe

if not exist "%PYTHON_EXE%" (
    echo 错误: 未找到Python，请先配置嵌入式Python
    pause
    exit /b 1
)

echo 启动 DAG 工业视觉系统...
"%PYTHON_EXE%" "%SCRIPT_DIR%main_optimized.py" %*
```

### run.sh (Linux)

```bash
#!/bin/bash
# 使用嵌入式Python运行

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON_EXE="$SCRIPT_DIR/python/bin/python3"

if [ ! -f "$PYTHON_EXE" ]; then
    echo "错误: 未找到Python"
    exit 1
fi

echo "启动 DAG 工业视觉系统..."
"$PYTHON_EXE" "$SCRIPT_DIR/main_optimized.py" "$@"
```

---

## 验证部署

```bash
# 使用嵌入式Python验证
python/python.exe quick_verify.py

# 检查依赖
python/python.exe deployment/check_dependencies.py
```

---

## 注意事项

1. **路径配置**: 确保python._pth包含所有必要路径
2. **依赖完整性**: 使用check_dependencies.py验证
3. **权限问题**: Windows可能需要管理员权限
4. **版本兼容**: Python版本需与依赖包兼容

---

## 故障排查

### 问题1: 找不到模块

**解决**: 检查python._pth配置

```
python311.zip
.
..
../core
../engine
../plugins
../Lib/site-packages
```

### 问题2: pip不可用

**解决**: 重新安装pip

```bash
python/python.exe get-pip.py --no-index --find-links=libs
```

### 问题3: 依赖缺失

**解决**: 手动安装缺失的包

```bash
python/python.exe -m pip install package_name --no-index --find-links=libs --target=python/Lib/site-packages
```

---

**文档维护**: Kiro AI Assistant  
**最后更新**: 2026-01-30
