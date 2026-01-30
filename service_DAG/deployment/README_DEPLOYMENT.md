# 部署指南

**版本**: 1.0.0  
**更新时间**: 2026-01-30

---

## 快速部署

### 1. 环境要求

- Python 3.8+
- Windows 10/11 或 Linux
- 至少 2GB 可用磁盘空间
- 至少 4GB 内存

### 2. 安装步骤

```bash
# 1. 解压部署包
unzip service_DAG_deployment.zip
cd service_DAG

# 2. 安装依赖
pip install -r requirements.txt

# 3. 验证安装
python quick_verify.py

# 4. 运行系统
python main_optimized.py
```

---

## 生产环境部署

### 1. 依赖检查

```bash
# 检查所有插件依赖
python deployment/check_dependencies.py

# 查看报告
cat dependency_report.txt
```

### 2. 配置系统

编辑配置文件 `config/production.json`:

```json
{
  "nodes": [...],
  "connections": [...],
  "execution_config": {
    "error_strategy": "skip",
    "max_retries": 3
  }
}
```

### 3. 启动守护进程（Windows）

```batch
# 安装开机自启动
cd deployment
install_autostart.bat

# 手动启动守护进程
watchdog.bat
```

### 4. 启动守护进程（Linux）

```bash
# 使用systemd
sudo cp deployment/dag-system.service /etc/systemd/system/
sudo systemctl enable dag-system
sudo systemctl start dag-system
```

---

## 磁盘空间管理

### 自动清理配置

在 `config/production.json` 中配置:

```json
{
  "nodes": [
    {
      "id": "image_writer",
      "type": "image_writer",
      "config": {
        "save_path": "./output",
        "max_files": 1000,
        "max_days": 7,
        "auto_cleanup": true
      }
    }
  ]
}
```

### 手动清理

```python
from service_DAG.core.disk_monitor import FileRotationManager

manager = FileRotationManager("./output", max_files=500)
result = manager.cleanup()
print(f"删除 {result['deleted']} 个文件，释放 {result['freed_mb']:.2f} MB")
```

---

## 监控和日志

### 查看日志

```bash
# 系统日志
tail -f logs/system.log

# 错误日志
tail -f logs/error.log

# 守护进程日志
tail -f logs/watchdog.log
```

### 性能监控

```bash
# 启动Qt监控界面
python test_qt_integration.py
```

---

## 故障排查

### 问题1: 程序无法启动

**检查**:
1. Python版本是否正确
2. 依赖是否完整安装
3. 配置文件是否正确

```bash
python quick_verify.py
python deployment/check_dependencies.py
```

### 问题2: 相机无法连接

**检查**:
1. 相机是否连接
2. 驱动是否安装
3. 环境变量是否设置

```bash
# Windows
setx MVCAM_COMMON_RUNENV "C:\MVS"
```

### 问题3: 磁盘空间不足

**解决**:
1. 检查磁盘空间
2. 运行清理脚本
3. 调整保留策略

```bash
# 查看磁盘使用
df -h

# 清理旧文件
python -c "from service_DAG.core.disk_monitor import FileRotationManager; FileRotationManager('./output').cleanup()"
```

### 问题4: 程序频繁重启

**检查**:
1. 查看错误日志
2. 检查心跳文件
3. 检查资源使用

```bash
# 查看守护日志
cat logs/watchdog.log

# 检查进程
ps aux | grep python
```

---

## 性能优化

### 1. 调整队列大小

```python
# 在main_optimized.py中
executor = StreamingExecutor(graph, event_bus, queue_size=50)
```

### 2. 调整线程池

```python
# 在插件中
import concurrent.futures
executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
```

### 3. 禁用不必要的功能

```json
{
  "nodes": [
    {
      "id": "display",
      "type": "display",
      "config": {
        "enabled": false  // 生产环境禁用显示
      }
    }
  ]
}
```

---

## 备份和恢复

### 备份配置

```bash
# 备份配置文件
cp -r config config_backup_$(date +%Y%m%d)

# 备份日志
tar -czf logs_backup_$(date +%Y%m%d).tar.gz logs/
```

### 恢复配置

```bash
# 恢复配置
cp -r config_backup_20260130/* config/
```

---

## 更新升级

### 1. 备份当前版本

```bash
cp -r service_DAG service_DAG_backup
```

### 2. 更新代码

```bash
git pull origin change
```

### 3. 更新依赖

```bash
pip install -r requirements.txt --upgrade
```

### 4. 验证更新

```bash
python quick_verify.py
```

### 5. 重启服务

```bash
# Windows
taskkill /F /IM python.exe
watchdog.bat

# Linux
sudo systemctl restart dag-system
```

---

## 安全建议

### 1. 文件权限

```bash
# 限制配置文件权限
chmod 600 config/*.json

# 限制日志目录权限
chmod 700 logs/
```

### 2. 网络安全

- 不要暴露内部端口
- 使用防火墙限制访问
- 定期更新依赖库

### 3. 数据安全

- 定期备份配置和数据
- 加密敏感配置
- 限制文件访问权限

---

## 联系支持

- 文档: [docs/](../docs/)
- 问题: 查看日志文件
- 验证: `python quick_verify.py`

---

**文档维护**: Kiro AI Assistant  
**最后更新**: 2026-01-30
