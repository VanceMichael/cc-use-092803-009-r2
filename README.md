# 山区应急协同服务

该服务用于记录灾害事件、风险区域、救援队伍、物资批次和跨部门处置行动。领域层保持事件顺序，仓储层使用 SQLite 保存可恢复状态，接口层提供本地 JSON 调用入口。

## 测试

```bash
python3 -m unittest discover -s tests
```

## 构建检查

```bash
python3 -m compileall emergency_service
```

## 使用

可通过 `python3 -m emergency_service.cli` 向标准输入提交一行 JSON 请求。所有时间使用带时区的 ISO-8601 字符串，数据文件由启动参数指定。
