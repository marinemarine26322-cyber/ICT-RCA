# SPN 故障诊断评测用例模板

## 1. 根因定义与组网拓扑

### 1.1 根因说明
* **根因类型**：硬件单板故障 (Card Fault)
* **根因对象**：`FixedNetworkCard`，名称 `CR57L5XFB 6/0` (resId: `7783ac9c-235d-11ea-a3da-286ed4a6f283`)
* **所属网元**：`PMR1-SJDD-PTN6900-HX2` (resId: `ad873c30-235e-11ea-b3e4-286ed4a6f27b`)
* **故障机理**：LPU/PIC 单板底层硬件寄存器异常或驱动故障，导致单板状态机进入 `FAULT` 隔离态。系统为防止错误数据转发，强制将该单板下挂的所有物理端口 PHY 层 Shutdown，并停止光模块发光。

### 1.2 组网与拓扑图

> mermaid语法描述拓扑图

```mermaid

```

## 2. 根因影响链 (传导路径)

故障从物理硬件层逐层向上层业务传导，形成完整的影响链条：

1. **L0 硬件层 (根因)**：单板 `CR57L5XFB 6/0` 发生硬件故障，`cardStatus` 变为 `FAULT`。
2. **L1 物理端口层 (本端)**：单板驱动隔离，导致该板下挂的所有物理端口（如 `GE6/0/3`）被强制 Down，光模块停止发光。`portOpticalPowerErrCode` 报 `BOARD_STATUS_ABNORMAL`。
3. **L2 物理端口层 (对端)**：本端停止发光，导致光纤对端端口接收不到光信号，触发 `LOS` (Loss of Signal)，对端端口 `inPowerStatus` 变为 `无光`。
4. **L3 逻辑聚合层**：`Eth-Trunk66` 的成员口失效。若配置了最小活跃链路数，或该口为唯一成员，则 Trunk 逻辑口 Down，`activeMemberCount` 降为 0。
5. **L4 链路层**：物理端口 Down 触发关联链路（如 `l-331`）协议状态翻转，`localPortFaultType` 升级为 `Critical`。
6. **L5 隧道层**：`Tunnel0/0/2786` 的 OAM 连续性检测中断，LSP Trace 在故障节点首跳失败，`tunnelOperateStatus` 变为 `down`。
7. **L6 伪线与业务层**：底层 Tunnel 中断导致绑定的 PW 去激活 (`pwOperateStatus: down`)，最终导致 SAP 业务面 100% 丢包 (`isPacketLoss: true`)。
8. **L7 告警层**：网管系统按时间序列依次收到 `BOARD_FAULT` (T0) -> `PORT_DOWN` (T0+2s) -> `TUNNEL_DOWN` (T0+3s) -> `PW_DOWN` (T0+5s)。

---

## 3. 受影响对象范围界定与证据链 (关联查找逻辑)

在构建 Mock 数据时，必须通过拓扑关联关系找出**所有受波及的对象范围**。以下为每一步查找逻辑的权威协议与规范依据及文档链接：

| 对象层级 | 受影响范围界定规则 (查找逻辑) | 具体枚举对象 (基于当前 Topo) | 证据链 / 权威参考依据 (传导原理) |
| :--- | :--- | :--- | :--- |
| **故障单板** | 根因对象本身。 | `CR57L5XFB 6/0` | **ITU-T X.731** (管理信息模型) / **TMF SID** (共享信息数据模型)：硬件故障是物理层最底层的 Root Cause，状态机进入 `FAULT` 态。<br>[ITU-T X.731 链接](https://www.itu.int/rec/T-REC-X.731/en) \| [TMF SID 链接](https://www.tmforum.org/resources/sid/) |
| **同板物理端口** | 查找 `FixedNetworkLTP.refParentCard == 故障单板.resId` 且 `isPhysical == true` 的所有端口。 | `GigabitEthernet6/0/3` (及同板其他物理口) | **IEEE 802.3 (Clause 30 MAU/PHY)**：单板管理芯片检测到硬件不可恢复故障时，会向端口驱动下发 `FORCE_DOWN` 指令，隔离该板卡下所有 LTP，光模块 TX 关闭。<br>[IEEE 802.3 链接](https://standards.ieee.org/ieee/802.3/4393/) |
| **对端互联端口** | 查找 `FixedNetworkLink` 中 `refAEndLTP` 或 `refZEndLTP` 包含上述同板物理端口的链路，获取对端端口。 | `l-331` 的对端端口 (当前拓扑中未纳管) | **ITU-T G.698.1** (光接口) / **IETF RFC 2790** (RMON MIB)：本端 TX 关闭导致光纤无光信号传递，对端 RX 模块检测不到有效光功率，触发 LOS 告警并 Down。<br>[G.698.1 链接](https://www.itu.int/rec/T-REC-G.698.1) \| [RFC 2790 链接](https://datatracker.ietf.org/doc/html/rfc2790) |
| **逻辑聚合口** | 查找 `FixedNetworkLTP.refTrunkLTP` 包含上述同板物理端口的 Eth-Trunk 逻辑口。 | `Eth-Trunk66` | **IEEE 802.1AX** (Link Aggregation)：物理成员口 Down 导致聚合组 (LAG) 重新计算活动链路数。若低于最小阈值或无成员存活，逻辑 Trunk 口状态翻转为 Down。<br>[IEEE 802.1AX 链接](https://standards.ieee.org/ieee/802.1AX/4321/) |
| **关联链路** | 查找 `FixedNetworkLink` 中绑定上述物理口或逻辑口的链路对象。 | `l-331` | **ITU-T Y.1731** (以太网 OAM)：物理层中断直接导致链路可用性归零，链路协议状态机翻转，故障等级升级为 Critical。<br>[Y.1731 链接](https://www.itu.int/rec/T-REC-Y.1731) |
| **承载隧道** | 查找 `TunnelHop` 中 `refAEndLTP` 或 `refZEndLTP` 经过上述故障端口/链路的 Tunnel。 | `Tunnel0/0/2786` | **IETF RFC 4379** (MPLS LSP Ping/Trace) / **ITU-T G.8113.1** (MPLS-TP OAM)：MPLS-TP 隧道依赖逐跳转发。底层出端口 Down 导致 OAM 连续性检测 (CCM) 超时或 Trace 探测报文无法封装发送。<br>[RFC 4379 链接](https://datatracker.ietf.org/doc/html/rfc4379) \| [G.8113.1 链接](https://www.itu.int/rec/T-REC-G.8113.1) |
| **承载伪线/业务**| 查找 `PWTrail` 中 `refTunnelList` 包含上述故障 Tunnel 的 PW 及绑定的 SAP。 | `PW(ETHERNET...)`, `Eth-Trunk66 (SAP)` | **IETF RFC 4447** (PWE3) / **3GPP TS 28.531** (故障管理)：PW 通过 Tunnel 伪线承载。Tunnel 状态机 Down 触发 PW 去激活，SAP 绑定的业务流无法转发，导致业务面 100% 丢包。<br>[RFC 4447 链接](https://datatracker.ietf.org/doc/html/rfc4447) \| [TS 28.531 链接](https://www.3gpp.org/DynaReport/28531.htm) |

---

## 4. 全量 API 字段受影响详细清单 (100% 逐行展开)

> **说明**：以下表格穷尽了 API Schema 中的**所有字段路径**，无任何省略。这里可以只写受影响的字段，其他使用默认正常值，但要确保受影响的字段+默认值字段的总和与`api_shcema.json`一致。

| API类别 | 字段路径 | 是否受影响 | 受影响对象范围/查找逻辑 | 预期 Mock 结果 | 影响说明与传导逻辑 |
| :--- | :--- | :---: | :--- | :--- | :--- |
| **port** | `isPhysical` | 否 | 所有端口 | `true` / `false` | 固有属性，不随故障改变。 |
| **port** | `portType` | 否 | 所有端口 | `"Physical"` / `"Eth-Trunk"` | 固有属性。 |
| **port** | `activeMemberCount` | 是 | 关联的逻辑聚合口 | `0` | 物理成员口 Down 导致 Trunk 成员失效。 |
| **port** | `totalMemberCount` | 否 | 关联的逻辑聚合口 | `2` | 配置总数不变。 |
| **port** | `currentAlarms` | 是 | 同板物理端口 / 逻辑口 | `["ETH_LOS", "PORT_DOWN"]` | 端口 Down 触发的衍生告警。 |
| **port** | `isSameFecMode` | 否 | 全局对象 | `true` | 未受此次硬件故障波及。 |
| **port** | `isSamePortWorkMode` | 否 | 全局对象 | `true` | 未受此次硬件故障波及。 |
| **port** | `portAdminStatus` | 否 | 全局对象 | `"up"` | 管理状态未变（非人为 Shutdown）。 |
| **port** | `portOperateStatus` | 是 | 同板所有物理端口 | `"down"` | 单板故障联动端口 PHY Down。 |
| **port** | `portOpticalPowerStatus` | 是 | 同板所有物理端口 | `"abnormal"` | 单板异常导致光模块不可用。 |
| **port** | `inPower` | 是 | 同板所有物理端口 | `-50.0` | 实际光功率跌落至底噪。 |
| **port** | `inPowerStatus` | 是 | 同板所有物理端口 | `"无光"` | 单板异常导致停止发光/收无光。 |
| **port** | `outPower` | 是 | 同板所有物理端口 | `-50.0` | 实际光功率跌落至底噪。 |
| **port** | `outPowerStatus` | 是 | 同板所有物理端口 | `"无光"` | 单板异常导致停止发光。 |
| **port** | `portOpticalPowerErrCode` | 是 | 同板所有物理端口 | `"BOARD_STATUS_ABNORMAL"` | **核心定界字段**：证明非光纤断裂。 |
| **port** | `portOpticalPowerDetails.portOpticalPowerInfo.inPower` | 是 | 同板所有物理端口 | `-50.0` | 详细光功率值越限。 |
| **port** | `portOpticalPowerDetails.portOpticalPowerInfo.minInPower` | 否 | 全局对象 | `-20.0` | 门限配置不变。 |
| **port** | `portOpticalPowerDetails.portOpticalPowerInfo.maxInPower` | 否 | 全局对象 | `0.0` | 门限配置不变。 |
| **port** | `portOpticalPowerDetails.portOpticalPowerInfo.outPower` | 是 | 同板所有物理端口 | `-50.0` | 详细光功率值越限。 |
| **port** | `portOpticalPowerDetails.portOpticalPowerInfo.minOutPower` | 否 | 全局对象 | `-15.0` | 门限配置不变。 |
| **port** | `portOpticalPowerDetails.portOpticalPowerInfo.maxOutPower` | 否 | 全局对象 | `5.0` | 门限配置不变。 |
| **port** | `isOffline` | 否 | 全局对象 | `false` | 对端网元未掉电。 |
| **port** | `isManagedPE` | 否 | 全局对象 | `true` / `false` | 对端纳管状态未变。 |
| **port** | `isNormal` | 是 | 同板所有物理端口 | `false` | 网络异常。 |
| **port** | `isOpticalNormal` | 是 | 同板所有物理端口 | `false` | 光功率异常。 |
| **port** | `aEndAlarmNames` | 是 | 同板所有物理端口 | `"ETH_LOS"` | 本端历史告警。 |
| **port** | `zEndAlarmNames` | 否 | 全局对象 | `""` | 对端历史告警未变。 |
| **link** | `localPortFaultType` | 是 | 关联链路 (如 l-331) | `"Critical"` | 本端端口 Down 导致链路 Critical。 |
| **link** | `localPortDetailInfo` | 是 | 关联链路 | `"单板FAULT导致端口强制Down"` | 携带根因归因描述。 |
| **link** | `remotePortFaultType` | 视情况 | 关联链路的对端 | `"Major"` 或 `"Unknown"` | 若对端未纳管，必须返回 `Unknown`。 |
| **link** | `remotePortDetailInfo` | 视情况 | 关联链路的对端 | `"对端收无光"` 或 `"对端未纳管"` | 对端详情描述。 |
| **card** | `cardList.cardCategory` | 否 | 全局对象 | `"LPU"` | 固有属性。 |
| **card** | `cardType` | 否 | 故障单板本身 | `"PIC"` | 固有属性。 |
| **card** | `cardRegistered` | 否 | 故障单板本身 | `true` | 单板在位。 |
| **card** | `cardStatus` | 是 | 故障单板本身 | `"FAULT"` | 根因所在，硬件状态机隔离。 |
| **card** | `currentAlarms` | 是 | 故障单板本身 | `["BOARD_FAULT"]` | 产生单板级根源告警。 |
| **tunnel** | `tunnelOperateStatus` | 是 | 经过故障节点的 Tunnel | `"down"` | 隧道 OAM 检测中断。 |
| **tunnel** | `tunnelOamStatus` | 是 | 经过故障节点的 Tunnel | `"timeout"` | OAM 超时。 |
| **tunnel** | `currentAlarms` | 是 | 经过故障节点的 Tunnel | `["TUNNEL_DOWN"]` | 隧道告警。 |
| **tunnel** | `remainBwForAllTunnels` | 否 | 全局对象 | 正常数值 | 未受此次硬件故障波及。 |
| **tunnel** | `remainBwRatioForAllTunnels` | 否 | 全局对象 | 正常数值 | 未受此次硬件故障波及。 |
| **tunnel** | `tunnelResults.tunnelRemainBw` | 否 | 全局对象 | 正常数值 | 未受此次硬件故障波及。 |
| **tunnel** | `tunnelResults.tunnelRemainBwRatio` | 否 | 全局对象 | 正常数值 | 未受此次硬件故障波及。 |
| **tunnel** | `tunnelResults.hopRemainBw.linkId` | 否 | 全局对象 | 正常字符串 | 未受此次硬件故障波及。 |
| **tunnel** | `tunnelResults.hopRemainBw.linkTopoId` | 否 | 全局对象 | 正常字符串 | 未受此次硬件故障波及。 |
| **tunnel** | `tunnelResults.hopRemainBw.linkName` | 否 | 全局对象 | 正常字符串 | 未受此次硬件故障波及。 |
| **tunnel** | `tunnelResults.hopRemainBw.remainBw` | 否 | 全局对象 | 正常字符串 | 未受此次硬件故障波及。 |
| **tunnel** | `tunnelResults.hopRemainBw.remainBwRatio` | 否 | 全局对象 | 正常字符串 | 未受此次硬件故障波及。 |
| **tunnel** | `topoObj.nodes.commuState` | 否 | 故障网元 | `"0"` | 网元在线。 |
| **tunnel** | `incidentObjList` | 是 | 经过故障节点的 Tunnel | `{...}` | 包含故障事件。 |
| **tunnel** | `faultPortResIdList` | 是 | 经过故障节点的 Tunnel | `["779671f6..."]` | 关联故障端口。 |
| **tunnel** | `faultNeResIdList` | 是 | 经过故障节点的 Tunnel | `["ad873c30..."]` | 关联故障网元。 |
| **tunnel** | `faultCardResIdList` | 是 | 经过故障节点的 Tunnel | `["7783ac9c..."]` | 关联故障单板。 |
| **tunnel** | `alarmObjList` | 是 | 经过故障节点的 Tunnel | `{...}` | 关联告警对象。 |
| **tunnel** | `notPingReachableTunnelObjList` | 是 | 经过故障节点的 Tunnel | `{...}` | Ping 不通。 |
| **tunnel** | `pingRstObjList` | 是 | 经过故障节点的 Tunnel | `{...}` | Ping 结果超时。 |
| **tunnel** | `notTraceReachableTunnelObjList` | 是 | 经过故障节点的 Tunnel | `{...}` | Trace 不通。 |
| **tunnel** | `traceRstObjList.tunnelObj.name` | 否 | 全局对象 | 正常字符串 | 隧道基础信息。 |
| **tunnel** | `traceRstObjList.tunnelObj.role` | 否 | 全局对象 | `"WORK"` | 隧道基础信息。 |
| **tunnel** | `traceRstObjList.tunnelObj.instance` | 否 | 全局对象 | `{...}` | 透传数据结构。 |
| **tunnel** | `traceRstObjList.tunnelObj.srcNeName` | 否 | 全局对象 | 正常字符串 | 隧道基础信息。 |
| **tunnel** | `traceRstObjList.tunnelObj.snkNeName` | 否 | 全局对象 | 正常字符串 | 隧道基础信息。 |
| **tunnel** | `traceRstObjList.traceRstList.errorCode` | 是 | 经过故障节点的 Tunnel | `1` | Trace 失败。 |
| **tunnel** | `traceRstObjList.traceRstList.sourceName` | 否 | 全局对象 | 正常字符串 | 基础路由信息。 |
| **tunnel** | `traceRstObjList.traceRstList.desName` | 否 | 全局对象 | 正常字符串 | 基础路由信息。 |
| **tunnel** | `traceRstObjList.traceRstList.direction` | 否 | 全局对象 | `"forward"` | 基础路由信息。 |
| **tunnel** | `traceRstObjList.traceRstList.role` | 否 | 全局对象 | `"WORK"` | 基础路由信息。 |
| **tunnel** | `traceRstObjList.traceRstList.reason` | 是 | 经过故障节点的 Tunnel | `"端口Down"` | 失败原因。 |
| **tunnel** | `traceRstObjList.traceRstList.tunnelName` | 否 | 全局对象 | 正常字符串 | 基础路由信息。 |
| **tunnel** | `traceRstObjList.traceRstList.tracerHop.seq` | 是 | Trace 失败跳数 | `1` | 逐跳序号。 |
| **tunnel** | `traceRstObjList.traceRstList.tracerHop.midIp` | 是 | Trace 失败跳数 | `"10.1.1.1"` | 中间 IP。 |
| **tunnel** | `traceRstObjList.traceRstList.tracerHop.minDelay` | 是 | Trace 失败跳数 | `-1` | 失败时无时延。 |
| **tunnel** | `traceRstObjList.traceRstList.tracerHop.maxDelay` | 是 | Trace 失败跳数 | `-1` | 失败时无时延。 |
| **tunnel** | `traceRstObjList.traceRstList.tracerHop.avgDelay` | 是 | Trace 失败跳数 | `-1` | 失败时无时延。 |
| **tunnel** | `traceRstObjList.traceRstList.nodeDiagnoseInfo.refNeName` | 是 | Trace 失败跳数 | `"PMR1-SJDD..."` | 挂载网元名称。 |
| **tunnel** | `traceRstObjList.traceRstList.nodeDiagnoseInfo.neStatus` | 否 | Trace 失败跳数 | `"online"` | 网元在线。 |
| **tunnel** | `traceRstObjList.traceRstList.nodeDiagnoseInfo.portName` | 是 | Trace 失败跳数 | `"GE6/0/3"` | 故障端口名称。 |
| **tunnel** | `traceRstObjList.traceRstList.nodeDiagnoseInfo.operateStatus`| 是 | Trace 失败跳数 | `"down"` | 透传故障端口状态。 |
| **tunnel** | `traceRstObjList.traceRstList.nodeDiagnoseInfo.adminStatus` | 否 | Trace 失败跳数 | `"up"` | 管理状态未变。 |
| **tunnel** | `traceRstObjList.traceRstList.nodeDiagnoseInfo.alarmNum` | 是 | Trace 失败跳数 | `"3"` | 告警条数。 |
| **tunnel** | `traceRstObjList.traceRstList.nodeDiagnoseInfo.alarmNames` | 是 | Trace 失败跳数 | `"BOARD_FAULT..."` | 告警名称。 |
| **tunnel** | `traceRstObjList.traceRstList.nodeDiagnoseInfo.powerStatus` | 是 | Trace 失败跳数 | `"异常"` | 光功率状态异常。 |
| **tunnel** | `isFillTunnelObjList` | 否 | 全局对象 | `false` | 未补充。 |
| **alarm** | `alarms.csn` | 是 | 全局告警流水 | `"ALM-001"` | 生成新流水号。 |
| **alarm** | `alarms.alarmName` | 是 | 全局告警流水 | `"BOARD_FAULT"` | 告警名称。 |
| **alarm** | `alarms.occurUtc` | 是 | 全局告警流水 | `1717200000000` | 发生时间，用于根因排序。 |
| **alarm** | `alarms.clearUtc` | 否 | 全局告警流水 | `0` | 未清除。 |
| **alarm** | `alarms.extParam` | 是 | 全局告警流水 | `"0x01 0x02..."` | 硬件错误码。 |
| **alarm** | `alarms.resourceResId` | 是 | 全局告警流水 | `"7783ac9c..."` | 锚定具体资源对象。 |
| **alarm** | `alarms.resourceType` | 是 | 全局告警流水 | `"Card"` | 资源类型。 |
| **alarm** | `alarmNames` | 是 | 全局告警流水 | `"BOARD_FAULT..."` | 聚合告警名。 |
| **alarm** | `deviceType` | 否 | 全局对象 | `"PTN6900"` | 设备型号。 |
| **base_station**| `accessRingObj` | 否 | 全局对象 | 保持默认值 | 未受此次硬件故障波及。 |
| **base_station**| `aggregationRingObj` | 否 | 全局对象 | 保持默认值 | 未受此次硬件故障波及。 |
| **base_station**| `offLineRangeTopoObjList` | 否 | 全局对象 | 保持默认值 | 未受此次硬件故障波及。 |
| **base_station**| `sapOfflineRangeObjList` | 否 | 全局对象 | 保持默认值 | 未受此次硬件故障波及。 |
| **clock** | `alarms` | 否 | 全局对象 | 保持默认值 | 未受此次硬件故障波及。 |
| **clock** | `clockPathList` | 否 | 全局对象 | 保持默认值 | 未受此次硬件故障波及。 |
| **clock** | `alarmNeResId` | 否 | 全局对象 | 保持默认值 | 未受此次硬件故障波及。 |
| **ne** | `currentAlarms` | 是 | 故障网元 | `["BOARD_FAULT"]` | 网元级告警聚合。 |
| **ne** | `neStatus` | 否 | 故障网元 | `"online"` | 网元整体在线。 |
| **ne** | `topoObj` | 否 | 全局对象 | 保持默认值 | 未受此次硬件故障波及。 |
| **ne** | `incidentObjList` | 是 | 故障网元 | `{...}` | 故障事件。 |
| **ne** | `faultPortResIdList` | 是 | 故障网元 | `["779671f6..."]` | 故障端口列表。 |
| **ne** | `faultNeResIdList` | 否 | 故障网元 | `[]` | 自身非故障网元。 |
| **ne** | `faultCardResIdList` | 是 | 故障网元 | `["7783ac9c..."]` | 故障单板列表。 |
| **ne** | `alarmObjList` | 是 | 故障网元 | `{...}` | 告警对象。 |
| **ne** | `offlineRangeCategory` | 否 | 全局对象 | `"NORMAL"` | 无脱管区域。 |
| **ne** | `isPortAllDown` | 否 | 故障网元 | `false` | 假设还有其他板卡。 |
| **ne** | `portAlarmObjList` | 是 | 故障网元 | `{...}` | 端口告警。 |
| **ne** | `contemporaneous` | 否 | 全局对象 | 保持默认值 | 未受此次硬件故障波及。 |
| **ne** | `resetInTimeDifference` | 否 | 全局对象 | 保持默认值 | 未受此次硬件故障波及。 |
| **ne** | `resetRecords` | 否 | 全局对象 | 保持默认值 | 未受此次硬件故障波及。 |
| **ne** | `clkTimeLockSta` | 否 | 全局对象 | 保持默认值 | 未受此次硬件故障波及。 |
| **ne** | `clkFreqLockSta` | 否 | 全局对象 | 保持默认值 | 未受此次硬件故障波及。 |
| **ne** | `poPtpSrcTraceClkid` | 否 | 全局对象 | 保持默认值 | 未受此次硬件故障波及。 |
| **ne** | `hasPtpSetUni` | 否 | 全局对象 | 保持默认值 | 未受此次硬件故障波及。 |
| **ne** | `poPtpPreSetState` | 否 | 全局对象 | 保持默认值 | 未受此次硬件故障波及。 |
| **ne** | `poPtpRealPortState` | 否 | 全局对象 | 保持默认值 | 未受此次硬件故障波及。 |
| **ne** | `poPtpSyncInterval` | 否 | 全局对象 | 保持默认值 | 未受此次硬件故障波及。 |
| **ne** | `poPtpDlyReqInterval` | 否 | 全局对象 | 保持默认值 | 未受此次硬件故障波及。 |
| **ne** | `poPtpAnnInterval` | 否 | 全局对象 | 保持默认值 | 未受此次硬件故障波及。 |
| **ne** | `maxPassive` | 否 | 全局对象 | 保持默认值 | 未受此次硬件故障波及。 |
| **ne** | `passiveList` | 否 | 全局对象 | 保持默认值 | 未受此次硬件故障波及。 |
| **ne** | `nePortDCNStatusList.name` | 否 | 全局对象 | 保持默认值 | 未受此次硬件故障波及。 |
| **ne** | `nePortDCNStatusList.productName` | 否 | 全局对象 | 保持默认值 | 未受此次硬件故障波及。 |
| **ne** | `nePortDCNStatusList.commuState` | 否 | 全局对象 | 保持默认值 | 未受此次硬件故障波及。 |
| **ne** | `nePortDCNStatusList.portObjList.name` | 否 | 全局对象 | 保持默认值 | 未受此次硬件故障波及。 |
| **ne** | `nePortDCNStatusList.portObjList.neNativeId` | 否 | 全局对象 | 保持默认值 | 未受此次硬件故障波及。 |
| **ne** | `nePortDCNStatusList.portObjList.nativeId` | 否 | 全局对象 | 保持默认值 | 未受此次硬件故障波及。 |
| **ne** | `nePortDCNStatusList.portObjList.operateState` | 否 | 全局对象 | 保持默认值 | 未受此次硬件故障波及。 |
| **ne** | `nePortDCNStatusList.portObjList.adminState` | 否 | 全局对象 | 保持默认值 | 未受此次硬件故障波及。 |
| **ne** | `nePortDCNStatusList.lspPingResult.notPingReachableTunnelObjList`| 否 | 全局对象 | 保持默认值 | 未受此次硬件故障波及。 |
| **ne** | `nePortDCNStatusList.lspPingResult.pingRstObjList` | 否 | 全局对象 | 保持默认值 | 未受此次硬件故障波及。 |
| **ne** | `dcnFaultType` | 否 | 全局对象 | `"NONE"` | 无 DCN 故障。 |
| **ne** | `offlineOrMpuFaultNeResIds` | 否 | 全局对象 | `[]` | 无离线网元。 |
| **ne** | `downAndDcnEnabledPortResIds` | 是 | 故障网元 | `["779671f6..."]` | Down 且使能 DCN 的端口。 |
| **ring** | `incidentObjList` | 否 | 全局对象 | 保持默认值 | 未受此次硬件故障波及。 |
| **ring** | `faultPortResIdList` | 否 | 全局对象 | 保持默认值 | 未受此次硬件故障波及。 |
| **ring** | `faultNeResIdList` | 否 | 全局对象 | 保持默认值 | 未受此次硬件故障波及。 |
| **ring** | `faultCardResIdList` | 否 | 全局对象 | 保持默认值 | 未受此次硬件故障波及。 |
| **ring** | `alarmObjList` | 否 | 全局对象 | 保持默认值 | 未受此次硬件故障波及。 |
| **service** | `sapStatus` | 是 | 绑定的 SAP 业务 | `"down"` | 业务接入点状态 Down。 |
| **service** | `bindingPwStatus` | 是 | 绑定的 SAP 业务 | `"down"` | 绑定 PW 状态。 |
| **service** | `isPacketLoss` | 是 | 绑定的 SAP 业务 | `true` | 业务丢包。 |
| **service** | `isL3Vpn` | 否 | 全局对象 | `false` | 业务类型。 |
| **service** | `pingRstObjList` | 是 | 绑定的 SAP 业务 | `{...}` | Ping 结果超时。 |
| **pw** | `pwOperateStatus` | 是 | 绑定故障 Tunnel 的 PW | `"down"` | 底层 Tunnel Down 导致 PW 去激活。 |
| **pw** | `pwOamStatus` | 是 | 绑定故障 Tunnel 的 PW | `"defect"` | OAM 缺陷。 |
| **pw** | `pwFaultType` | 是 | 绑定故障 Tunnel 的 PW | `"TUNNEL_DOWN"` | 明确 PW 故障原因。 |
| **pw** | `currentAlarms` | 是 | 绑定故障 Tunnel 的 PW | `["PW_DOWN"]` | PW 告警。 |
| **pw** | `bindingTunnelStatus` | 是 | 绑定故障 Tunnel 的 PW | `"down"` | 绑定隧道状态。 |

---

## 5. Agent 诊断 SOP 与推理逻辑

期望大模型 Agent 在接收到“业务丢包”初始 Prompt 后，遵循以下标准作业程序（SOP）：

1. **业务层触发与定界 (Service/SAP)**
   * **动作**：调用 `service` API。
   * **逻辑**：发现 `isPacketLoss: true` 且 `sapStatus: down`。提取绑定的 PW 和 Tunnel 信息，确认故障发生在承载层，而非单纯的用户侧 CE 问题。
2. **隧道层追踪与断点定位 (Tunnel)**
   * **动作**：调用 `tunnel` API，重点查看 `traceRstObjList`。
   * **逻辑**：发现 Tunnel Down。遍历 Trace 结果，发现首跳 `errorCode: 1`。提取 `nodeDiagnoseInfo` 中的 `portName` (GE6/0/3)，将排查视角从逻辑隧道下钻至物理端口。
3. **逻辑与物理端口排查 (Port) - 防幻觉核心**
   * **动作**：调用 `port` API 查询 Eth-Trunk66 和 GE6/0/3。
   * **逻辑**：
     * 查 Eth-Trunk66 时，识别到 `isPhysical: false`，**立即停止**分析光功率，转而查看 `activeMemberCount: 0`。
     * 查物理口 GE6/0/3 时，发现 `portOperateStatus: down`。此时**关键判断**：查看 `portOpticalPowerErrCode`。若为 `BOARD_STATUS_ABNORMAL`，则排除光纤断裂，直接定性为“单板硬件异常”。
4. **硬件层根因锁定 (Card)**
   * **动作**：根据端口的父级关系，调用 `card` API 查询 CR57L5XFB 6/0。
   * **逻辑**：确认 `cardStatus: FAULT`，且 `currentAlarms` 包含 `BOARD_FAULT`。物理层根因锁定。
5. **告警时间序验证 (Alarm)**
   * **动作**：调用全局 `alarm` API，按 `occurUtc` 排序。
   * **逻辑**：验证 `BOARD_FAULT` (T0) 发生时间早于 `PORT_DOWN` (T0+2s)。通过时间相关性彻底排除并发故障可能，输出最终诊断报告。
