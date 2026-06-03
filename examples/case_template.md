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

| 对象层级 | 受影响范围界定规则 (查找逻辑) | 具体枚举对象 | 证据链 / 权威参考依据 |
|---------|---------------------------|-------------|-------------------|
| **故障单板** | 根因对象本身 | `TPA2EG24 24` (resId: `68ae10be-235d-11ea-b4b3-286ed4a6f283`) | **ITU-T X.731** / **TMF SID** (共享信息数据模型)：硬件故障是物理层最底层的 Root Cause，状态机进入 `FAULT` 态。<br>[ITU-T X.731 链接](https://www.itu.int/rec/T-REC-X.731/en) \| [TMF SID 链接](https://www.tmforum.org/resources/sid/) |
| **同板物理端口** | `refParentCard == 故障单板.resId` 且 `isPhysical == true` | `24-槽位-各物理端口` (如 24-1, 24-2 等) | **IEEE 802.3 (Clause 30 MAU/PHY)**：单板管理芯片检测到硬件不可恢复故障时，会向端口驱动下发 `FORCE_DOWN` 指令，隔离该板卡下所有 LTP，光模块 TX 关闭。<br>[IEEE 802.3 链接](https://standards.ieee.org/ieee/802.3/4393/)  |
| **对端互联端口** | 通过 `FixedNetworkLink` 关联查找 `refAEndLTP/refZEndLTP` | 链路对端端口 (未纳管则标记 `Unknown`) | **ITU-T G.698.1** (光接口) / **IETF RFC 2790** (RMON MIB)：本端 TX 关闭导致光纤无光信号传递，对端 RX 模块检测不到有效光功率，触发 LOS 告警并 Down。<br>[G.698.1 链接](https://www.itu.int/rec/T-REC-G.698.1) \| [RFC 2790 链接](https://datatracker.ietf.org/doc/html/rfc2790) |
| **逻辑聚合口** | `refTrunkLTP` 包含故障物理端口的 Eth-Trunk | `Eth-TrunkXXX` (若配置) | **IEEE 802.1AX** (Link Aggregation)：物理成员口 Down 导致聚合组 (LAG) 重新计算活动链路数。若低于最小阈值或无成员存活，逻辑 Trunk 口状态翻转为 Down。<br>[IEEE 802.1AX 链接](https://standards.ieee.org/ieee/802.1AX/4321/) |
| **关联链路** | `FixedNetworkLink` 绑定上述物理口或逻辑口 | `link-xxx` | **ITU-T Y.1731** (以太网 OAM)：物理层中断直接导致链路可用性归零，链路协议状态机翻转，故障等级升级为 Critical。<br>[Y.1731 链接](https://www.itu.int/rec/T-REC-Y.1731) |
| **承载隧道** | `TunnelHop` 经过故障端口/链路的 Tunnel | `Tunnel0/0/2786` (若路径经过) |  **IETF RFC 4379** (MPLS LSP Ping/Trace) / **ITU-T G.8113.1** (MPLS-TP OAM)：MPLS-TP 隧道依赖逐跳转发。底层出端口 Down 导致 OAM 连续性检测 (CCM) 超时或 Trace 探测报文无法封装发送。<br>[RFC 4379 链接](https://datatracker.ietf.org/doc/html/rfc4379) \| [G.8113.1 链接](https://www.itu.int/rec/T-REC-G.8113.1) |
| **承载伪线/业务** | `PWTrail` 绑定故障 Tunnel 的 PW 及 SAP | `PW(ETHERNET,...)`, `24-TPA2EG24-9:53` | **IETF RFC 4447** (PWE3) / **3GPP TS 28.531** (故障管理)：PW 通过 Tunnel 伪线承载。Tunnel 状态机 Down 触发 PW 去激活，SAP 绑定的业务流无法转发，导致业务面 100% 丢包。<br>[RFC 4447 链接](https://datatracker.ietf.org/doc/html/rfc4447) \| [TS 28.531 链接](https://www.3gpp.org/DynaReport/28531.htm)  |

---

## 4. 全量 API 字段受影响详细清单 (仅受影响字段)

> 基于 `api_schema.json` 定义，仅列出因本次根因导致值发生变化的字段，未受影响的字段保持默认值，不在此赘述。受影响的对象和字段应依据故障根因和传导链构造预期 Mock 值。
> 注意：受影响的字段+未列出来（即未受影响）的字段总和是 `api_schema.json` 的字段总和。

### 4.1 port 类 - 受影响字段

#### 4.1.1 本端物理端口 (故障单板下挂)
**受影响对象**：`refParentCard == '68ae10be-235d-11ea-b4b3-286ed4a6f283'` 且 `isPhysical == true` 的所有端口（如 24-1, 24-2...）

| 字段路径 | 预期 Mock 结果 | 影响说明与传导逻辑 |
|:--------|:-------------|:------------------|
| `portOperateStatus` | `"down"` | 🔴 单板驱动下发 `FORCE_DOWN`，PHY 层强制隔离 |
| `portOpticalPowerErrCode` | `"BOARD_STATUS_ABNORMAL"` | 🔑 **核心定界字段**：明确异常源于单板硬件，非光纤/对端问题 |
| `inPower` / `outPower` | `-50.0` | 实际收/发光功率跌落至底噪水平 (dBm) |
| `inPowerStatus` / `outPowerStatus` | `"无光"` | 激光器关闭，光模块驱动断电/异常 |
| `isNormal` / `isOpticalNormal` | `false` | 网络连通性与光功率指标双异常标志 |
| `currentAlarms` | `["ETH_LOS", "PORT_DOWN"]` | 硬件故障触发的本端衍生告警 |
| `aEndAlarmNames` | `"ETH_LOS,PORT_DOWN"` | 本端告警聚合字符串 |
| `portErrorDisable` / `portErrorDisableReason` | `true` / `"CARD_FAULT"` | 端口因底层错误被系统自动禁用 |
| `portUpdateTime` | `1717200002000` | 状态变更触发最后更新时间刷新 |
| `portStatistics.inOctets` / `outOctets` | `0` (停止计数) | 物理层 Down 后流量统计冻结 |

#### 4.1.2 对端互联端口 (光纤直连对端)
**受影响对象**：`FixedNetworkLink` 中 `refAEndLTP/refZEndLTP` 关联的对端物理端口（若对端设备已纳管）

| 字段路径 | 预期 Mock 结果 | 影响说明与传导逻辑 |
|:--------|:-------------|:------------------|
| `inPower` / `inPowerStatus` | `-50.0` / `"无光"` | 本端停止发光，导致对端 RX 侧光功率丢失 |
| `portOpticalPowerErrCode` | `"NONE"` 或 `"RX_LOS"` | ⚠️ **关键差异**：对端无单板故障码，仅表现为光路中断 |
| `isOpticalNormal` | `false` | 光功率指标异常 |
| `currentAlarms` | `["ETH_LOS"]` | 仅触发接收侧 LOS 告警，无 `PORT_DOWN`（协议层可能保持 up） |
| `zEndAlarmNames` | `"ETH_LOS"` | 对端告警聚合字符串 |
| `portOperateStatus` | `"down"` (视协议而定) | 若配置了光功率联动 Down，则状态翻转；否则可能保持 `up` 但业务中断 |

#### 4.1.3 逻辑聚合端口 (Eth-Trunk)
**受影响对象**：`refTrunkLTP` 包含上述故障物理端口的 `Eth-TrunkXXX` 逻辑口

| 字段路径 | 预期 Mock 结果 | 影响说明与传导逻辑 |
|:--------|:-------------|:------------------|
| `activeMemberCount` | `0` | 物理成员口全部失效，活跃链路数归零 |
| `portOperateStatus` | `"down"` | 低于最小活跃链路阈值（或唯一成员失效），逻辑口状态翻转 |
| `currentAlarms` | `["PORT_DOWN"]` | 逻辑口状态异常触发告警 |
| `isPhysical` | `false` (固有) | 标识为逻辑口，**不参与光功率字段查询**（防幻觉校验点） |

---

### 4.2 link 类 - 受影响字段 (4/4)
**受影响对象**：`refAEndLTP` 或 `refZEndLTP` 绑定故障端口的 `FixedNetworkLink` 对象

| 字段路径 | 预期 Mock 结果 | 影响说明与传导逻辑 |
|:--------|:-------------|:------------------|
| `localPortFaultType` | `"Critical"` | 🔴 本端物理层硬故障导致链路等级紧急 |
| `localPortDetailInfo` | `"单板FAULT导致端口强制Down"` | 携带根因归因描述，辅助诊断引擎 |
| `remotePortFaultType` | `"Major"` (若纳管) / `"Unknown"` (若未纳管) | 对端故障等级，未纳管拓扑必须返回 `Unknown` |
| `remotePortDetailInfo` | `"对端收无光"` / `"对端设备未纳管/不在拓扑范围内"` | 对端状态透传描述 |

---

### 4.3 card 类 - 受影响字段 (2/5)
**受影响对象**：根因单板 `TPA2EG24 24` (resId: `68ae10be-235d-11ea-b4b3-286ed4a6f283`)

| 字段路径 | 预期 Mock 结果 | 影响说明与传导逻辑 |
|:--------|:-------------|:------------------|
| `cardStatus` | `"FAULT"` | 🔴 **根因字段**：硬件状态机进入故障隔离态 |
| `currentAlarms` | `["BOARD_FAULT"]` | 🔴 单板级根源告警，时间序列最早 |

---

### 4.4 tunnel 类 - 受影响字段 (11/47)
**受影响对象**：`TunnelHop` 中 `refAEndLTP/refZEndLTP` 经过故障端口/链路的隧道（如 `Tunnel0/0/2786`）

| 字段路径 | 预期 Mock 结果 | 影响说明与传导逻辑 |
|:--------|:-------------|:------------------|
| `tunnelOperateStatus` | `"down"` | 🔴 OAM 连续性检测中断 |
| `tunnelOamStatus` | `"timeout"` | CCM 报文超时未收到响应 |
| `currentAlarms` | `["TUNNEL_DOWN"]` | 隧道级衍生告警 |
| `faultCardResIdList` | `["68ae10be-235d-11ea-b4b3-286ed4a6f283"]` | 🔑 关联的故障单板 resId 列表 |
| `traceRstObjList[*].traceRstList.errorCode` | `1` | 🔴 Trace 探测失败错误码（首跳失败） |
| `traceRstObjList[*].traceRstList.reason` | `"端口Down"` | 🔴 失败原因描述 |
| `traceRstObjList[*].traceRstList.nodeDiagnoseInfo.portName` | `"24-1"` / `"24-2"` | 🔑 故障端口名称，用于下钻定位 |
| `traceRstObjList[*].traceRstList.nodeDiagnoseInfo.operateStatus` | `"down"` | 🔴 透传故障端口操作状态 |
| `traceRstObjList[*].traceRstList.nodeDiagnoseInfo.powerStatus` | `"异常"` | 🔴 光功率状态异常 |
| `traceRstObjList[*].traceRstList.tracerHop[*].min/max/avgDelay` | `-1` | 失败跳点无有效时延数据 |
| `pingRstObjList` / `notPingReachableTunnelObjList` | `{result: "timeout", loss: 100}` | 隧道 Ping 探测 100% 丢包 |

---

### 4.5 pw 类 - 受影响字段 (5/5)
**受影响对象**：`refTunnelList` 绑定故障隧道的伪线对象（如 `PW(ETHERNET,174691,45.64.191.144)`）

| 字段路径 | 预期 Mock 结果 | 影响说明与传导逻辑 |
|:--------|:-------------|:------------------|
| `pwOperateStatus` | `"down"` | 🔴 底层 Tunnel Down 导致伪线去激活 |
| `pwOamStatus` | `"defect"` | PW OAM 检测到缺陷状态 |
| `pwFaultType` | `"TUNNEL_DOWN"` | 🔑 明确 PW 故障的根本原因（非 PW 配置问题） |
| `currentAlarms` | `["PW_DOWN"]` | PW 级衍生告警 |
| `bindingTunnelStatus` | `"down"` | 绑定隧道的状态透传 |

---

### 4.6 service 类 - 受影响字段 (4/5)
**受影响对象**：`bindingPw` 关联故障伪线的 SAP 业务接入点（如 `24-TPA2EG24-9:53`）

| 字段路径 | 预期 Mock 结果 | 影响说明与传导逻辑 |
|:--------|:-------------|:------------------|
| `sapStatus` | `"down"` | 🔴 业务接入点状态随底层中断而 Down |
| `bindingPwStatus` | `"down"` | 绑定 PW 状态透传 |
| `isPacketLoss` | `true` | 🔴 业务面 100% 丢包，用户可感知 |
| `pingRstObjList` | `{result: "timeout", lossRate: 100}` | 业务面 Ping 测试结果：超时/丢包 |

---

### 4.7 alarm 类 - 受影响字段 (6/9)
**受影响对象**：全局告警流水 (`alarms` 数组)，按 `resourceType` 区分

| 字段路径 | 预期 Mock 结果 | 影响说明与传导逻辑 |
|:--------|:-------------|:------------------|
| `alarms[*].alarmName` | `"BOARD_FAULT"` → `"PORT_DOWN"` → `"TUNNEL_DOWN"` → `"PW_DOWN"` | 🔴 告警名称，按因果时间序列依次生成 |
| `alarms[*].occurUtc` | `T0` → `T0+2s` → `T0+3s` → `T0+5s` | 🔑 发生时间戳，用于根因时序排序（最早者为根因） |
| `alarms[*].resourceResId` | `"68ae10be-..."` (Card) → 端口 resId → 隧道 resId → PW resId | 🔑 锚定具体资源对象，构建关联图谱 |
| `alarms[*].resourceType` | `"Card"` → `"Port"` → `"Tunnel"` → `"PW"` | 资源类型，用于分层定界 |
| `alarms[*].extParam` (仅 BOARD_FAULT) | `"0x0102 0x0304"` | 硬件错误码扩展参数，辅助研发分析根因 |
| `alarms[*].alarmSeverity` | `"Critical"` (Board) → `"Major"` (Port/Tunnel) → `"Minor"` (PW) | 告警严重程度，按故障传导衰减定义 |

---

### 4.8 ne 类 - 受影响字段 (4/38)
**受影响对象**：故障网元 `BR-CityB-ACC-54` (resId: `ad86ee9a-235e-11ea-b3e4-286ed4a6f27b`)

| 字段路径 | 预期 Mock 结果 | 影响说明与传导逻辑 |
|:--------|:-------------|:------------------|
| `currentAlarms` | `["BOARD_FAULT"]` | 网元级告警聚合，仅包含根源告警 |
| `faultCardResIdList` | `["68ae10be-235d-11ea-b4b3-286ed4a6f283"]` | 🔴 网元维度故障单板清单 |
| `faultPortResIdList` | `["779671f6-...", "779671f7-...", ...]` | 网元维度故障物理端口清单 |
| `downAndDcnEnabledPortResIds` | `["779671f6-...", ...]` | Down 且使能 DCN 的端口清单（影响网管通道监控） |

---

### 4.9 其他类型 (无受影响字段)
| 类型 | 受影响对象 | 说明 |
|:----|:---------|:----|
| `base_station` (4 字段) | 无 | 单板级硬件故障未波及环网拓扑和基站接入层，全部保持默认值 |
| `clock` (3 字段) | 无 | 时钟同步通道独立于业务 LPU 单板，未受故障波及 |
| `ring` (5 字段) | 无 | 环网级保护/故障检测不感知单板级硬件故障，列表为空 |

---

### 📊 API 字段受影响统计汇总表

| 类型 | 总属性数量 | 受影响属性数量 | 不受影响属性数量 | 受影响比例 | 核心受影响对象 |
|:----|:----------:|:-------------:|:---------------:|:---------:|:-------------|
| **port** | 27 | 23 | 4 | 85.2% | 本端物理口、对端互联口、逻辑聚合口 |
| **link** | 4 | 4 | 0 | 100% | 故障端口绑定的物理/逻辑链路 |
| **card** | 5 | 2 | 3 | 40.0% | 故障单板 `TPA2EG24 24` 本身 |
| **tunnel** | 47 | 11 | 36 | 23.4% | 路径经过故障端口的业务隧道 |
| **pw** | 5 | 5 | 0 | 100% | 绑定故障隧道的伪线实例 |
| **service** | 5 | 4 | 1 | 80.0% | 绑定故障 PW 的 SAP 业务面 |
| **alarm** | 9 | 6 | 3 | 66.7% | 全局告警流水 (按时间序排列) |
| **ne** | 38 | 4 | 34 | 10.5% | 故障网元 `BR-CityB-ACC-54` |
| **base_station** | 4 | 0 | 4 | 0% | 无 |
| **clock** | 3 | 0 | 3 | 0% | 无 |
| **ring** | 5 | 0 | 5 | 0% | 无 |
| **📈 合计** | **152** | **54** | **98** | **35.5%** | - |

> **注**：为保证评测集完整性，Mock 数据应包含单板下**所有**受影响端口及其对端、所属聚合组、隧道、PW、SAP 的对应字段，而非仅一个示例。
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
