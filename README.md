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

## 幂等与去重语义

- 事件自然键为 **(地区 `region`, 外部事件号 `event_id`)**：同一灾害的重复上报（不同 `request_id`）只保留一条处置链；不同地区复用同一事件号不会被合并，派单/审计可按地区区分。
- 所有写接口以 `request_id` 幂等：并发重复提交、超时重试、崩溃重放都只产生一次副作用（队伍能力只扣一次、物资只锁一次）。
- 物资锁定可携带 `reservation_id`（处置链标识），即使重试换了 `request_id`，同一处置链的锁定也不重复放大；对应的 `release` 同样幂等。
- 写请求先落未决日志（SQLite `journal` 表），结果落盘后清除；审计实时落盘，进程重启时先按审计流水重建领域状态，再重放残留未决动作。
- 派单与物资接口返回当前实际状态（派单 `state`、队伍剩余能力、批次 `reserved`/`available`），现场可直接核对。

