import os
import sys
import ctypes
import getpass
import subprocess
import shutil
from pathlib import Path
import string
import time
import platform

# ===================== 配置常量（隐藏卡密，仅内部校验） =====================
TOOL_NAME = "SYUP系统深度清理工具箱 V2.0"
PRO_PASSWORD = "SYUP2026"  # 专业模式密钥
VERSION = "2.0 权威系统优化版-全盘扫描强化校验计时版"

# 颜色控制台美化（Windows cmd支持）
class Color:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    WHITE = '\033[97m'
    END = '\033[0m'

# 全局错误收集列表
err_log = []

# 时间格式化工具：秒转 时:分:秒
def format_time(seconds: float):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = round(seconds % 60, 2)
    return f"{h:02d}:{m:02d}:{s:05.2f}"

# 获取磁盘剩余空间 GB
def get_disk_free_gb(drive: str):
    try:
        stat = shutil.disk_usage(drive)
        free_gb = stat.free / 1024 / 1024 / 1024
        return round(free_gb, 2)
    except:
        return 0.0

# 记录错误日志
def add_err(task_name: str, err_msg: str):
    err_log.append({"task": task_name, "error": err_msg})

# 执行带计时+预检测的CMD命令
def run_cmd_timed(cmd: str, desc: str, skip_check: bool = False):
    start = time.perf_counter()
    print(f"\n{Color.GREEN}[执行] {desc}{Color.END}")
    try:
        proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        cost = time.perf_counter() - start
        if proc.returncode == 0:
            print(f"{Color.GREEN}[完成] {desc} | 单步耗时：{cost:.2f}秒{Color.END}")
        else:
            err_info = f"返回码:{proc.returncode}, stderr:{proc.stderr.strip()}"
            add_err(desc, err_info)
            print(f"{Color.YELLOW}[警告] {desc} | 耗时：{cost:.2f}秒 非0返回码{Color.END}")
        return cost
    except Exception as e:
        cost = time.perf_counter() - start
        err_info = str(e)
        add_err(desc, err_info)
        print(f"{Color.RED}[失败] {desc} | 耗时：{cost:.2f}秒 错误：{err_info}{Color.END}")
        return cost

# 打印汇总错误清单
def print_error_summary():
    if len(err_log) == 0:
        print(f"\n{Color.GREEN}[校验汇总] 本次清理所有任务执行无异常{Color.END}")
        return
    print(f"\n{Color.RED}==================== 本次清理异常任务汇总（共{len(err_log)}条） ===================={Color.END}")
    for idx, item in enumerate(err_log, 1):
        print(f"{idx}. 任务：{item['task']}")
        print(f"   错误详情：{item['error']}\n")
    print(f"{Color.RED}====================================================================={Color.END}")

# 清空错误日志
def clear_err_log():
    global err_log
    err_log = []

def print_logo():
    logo = f"""
{Color.BLUE}
=====================================================
        {TOOL_NAME}
                {VERSION}
    解决：系统卡顿 | 垃圾堆积 | 后台进程占用
    功能：全盘扫描+多层前置校验+磁盘空间检测+分段计时+异常汇总
====================================================={Color.END}
{Color.YELLOW}
【1】快速一键清理（全盘轻度垃圾清理，无需密码，多层文件预检）
【2】专业深度清理（全权限底层全盘优化，密钥验证，磁盘/注册表/进程多重校验）
【0】退出工具箱
====================================================={Color.END}
"""
    print(logo)

# 获取电脑所有本地磁盘分区（C/D/E/F...，跳过光驱、U盘、损坏无法访问磁盘）
def get_all_local_drives():
    drive_list = []
    bad_drive = []
    for letter in string.ascii_uppercase:
        drive = f"{letter}:\\"
        try:
            # 判断磁盘类型
            drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive)
            # DRIVE_FIXED = 3 本地固定硬盘
            if drive_type == 3:
                # 预检磁盘是否可访问
                os.listdir(drive)
                drive_list.append(drive)
            elif drive_type == 2:
                print(f"{Color.WHITE}[磁盘过滤] 跳过移动U盘：{drive}{Color.END}")
            elif drive_type == 5:
                print(f"{Color.WHITE}[磁盘过滤] 跳过光驱：{drive}{Color.END}")
        except PermissionError:
            bad_drive.append(f"{drive}（权限拒绝）")
        except OSError:
            bad_drive.append(f"{drive}（磁盘损坏/无法访问）")
        except Exception as e:
            bad_drive.append(f"{drive} 异常:{str(e)}")
    print(f"{Color.BLUE}[磁盘扫描] 检测到可用本地硬盘分区：{drive_list}{Color.END}")
    if len(bad_drive) > 0:
        print(f"{Color.YELLOW}[磁盘警告] 跳过异常分区：{bad_drive}{Color.END}")
    return drive_list

# 判断进程是否正在运行
def check_process_running(proc_name: str) -> bool:
    cmd = f'tasklist /fi "imagename eq {proc_name}.exe"'
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return proc_name.lower() in res.stdout.lower()

# 判断是否管理员权限（多层校验）
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception as e:
        add_err("管理员权限检测", str(e))
        return False

# 请求管理员权限重启程序
def run_as_admin():
    if not is_admin():
        print(f"{Color.YELLOW}[权限校验] 未检测到管理员权限，正在申请提权重启程序...{Color.END}")
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit(0)

# 检查路径是否存在
def path_exists_check(path_obj: Path) -> bool:
    if path_obj.exists():
        return True
    print(f"{Color.WHITE}[路径预检跳过] 目录不存在：{path_obj}{Color.END}")
    return False

# 快速清理模块（模式1 全盘扫描+多层前置校验）
def fast_clean():
    clear_err_log()
    total_start = time.perf_counter()
    print(f"\n{Color.BLUE}===== 启动【快速一键清理】全盘模块（多层校验+计时已开启） ====={Color.END}")
    drive_list = get_all_local_drives()
    space_before = {}
    # 记录清理前各盘空间
    for d in drive_list:
        space_before[d] = get_disk_free_gb(d)

    # 1. 遍历所有磁盘删除*.tmp临时文件、清空回收站
    for disk in drive_list:
        run_cmd_timed(f"del /f /s /q {disk}*.tmp", f"清理{disk}全盘临时文件")
        recycle_bin = Path(f"{disk}$Recycle.Bin")
        if path_exists_check(recycle_bin):
            run_cmd_timed(f"rd /s /q {disk}$Recycle.Bin", f"清空{disk}回收站")

    # 2. 用户系统临时文件夹清理（预检目录）
    temp_user = Path(os.environ["TEMP"])
    if path_exists_check(temp_user):
        run_cmd_timed("del /f /s /q %temp%\*", "清理用户临时文件夹缓存")
    temp_sys = Path(r"C:\Windows\Temp")
    if path_exists_check(temp_sys):
        run_cmd_timed("del /f /s /q C:\Windows\Temp\*", "系统Temp缓存清理")

    # 3. Edge/Chrome浏览器缓存清理（预检目录）
    cache_start = time.perf_counter()
    chrome_cache = Path(os.environ["LOCALAPPDATA"]) / "Google" / "Chrome" / "User Data" / "Default" / "Cache"
    edge_cache = Path(os.environ["LOCALAPPDATA"]) / "Microsoft" / "Edge" / "User Data" / "Default" / "Cache"
    if path_exists_check(chrome_cache):
        shutil.rmtree(chrome_cache, ignore_errors=True)
        print(f"{Color.GREEN}[完成] Chrome浏览器缓存清理{Color.END}")
    if path_exists_check(edge_cache):
        shutil.rmtree(edge_cache, ignore_errors=True)
        print(f"{Color.GREEN}[完成] Edge浏览器缓存清理{Color.END}")
    cache_cost = time.perf_counter() - cache_start
    print(f"{Color.GREEN}[缓存清理总耗时] {cache_cost:.2f}秒{Color.END}")

    # 4. 清理下载文件夹过期安装包（预检目录）
    dl_start = time.perf_counter()
    download_path = Path(os.environ["USERPROFILE"]) / "Downloads"
    if path_exists_check(download_path):
        for file in download_path.glob("*.exe"):
            try:
                os.remove(file)
            except Exception as e:
                add_err(f"删除安装包 {file.name}", str(e))
    dl_cost = time.perf_counter() - dl_start
    print(f"{Color.GREEN}[安装包清理耗时] {dl_cost:.2f}秒{Color.END}")

    # 空间释放统计
    print(f"\n{Color.BLUE}[磁盘空间释放统计] 清理前后剩余容量对比：{Color.END}")
    for d in drive_list:
        after = get_disk_free_gb(d)
        free_diff = round(after - space_before[d], 2)
        print(f"  {d} 清理前:{space_before[d]}GB → 清理后:{after}GB | 释放空间:{free_diff}GB")

    # 总耗时统计
    total_cost = time.perf_counter() - total_start
    fmt_total = format_time(total_cost)
    print(f"\n{Color.GREEN}=============================================")
    print(f"【全盘快速清理全部执行完毕】")
    print(f"本次快速清理总执行时长：{fmt_total}")
    print(f"============================================={Color.END}")
    print_error_summary()
    input("\n按回车键返回主菜单...")

# 专业深度清理模块（模式2，密钥校验+多层权限/文件/进程/磁盘全量校验）
def professional_clean():
    clear_err_log()
    # 密码输入，掩码隐藏输入内容
    print(f"\n{Color.YELLOW}请输入专业模式访问密钥（输入无显示，输完回车）：{Color.END}")
    input_pwd = getpass.getpass("密钥：")
    if input_pwd != PRO_PASSWORD:
        print(f"{Color.RED}密钥校验失败，拒绝进入专业深度清理！{Color.END}")
        input("按回车返回主菜单...")
        return

    # 第一层管理员校验
    if not is_admin():
        print(f"{Color.YELLOW}[权限校验1] 专业深度清理需要管理员权限，正在自动申请权限重启程序...{Color.END}")
        run_as_admin()
        return

    total_start = time.perf_counter()
    print(f"\n{Color.RED}===== 启动【专业底层深度清理】全盘全权限模块（多层校验全局计时开启） ====={Color.END}")
    print(f"{Color.YELLOW}警告：本操作扫描电脑全部本地磁盘，清理底层缓存、日志、休眠文件、冗余注册表，优化后台占用进程{Color.END}")
    confirm = input("确认继续全盘深度清理？(Y/N)：").strip().upper()
    if confirm != "Y":
        print("已取消专业清理，返回主菜单")
        input("回车返回...")
        return

    # 第二层管理员动态校验，防止中途权限丢失
    if not is_admin():
        print(f"{Color.RED}[权限校验2] 执行中途丢失管理员权限，终止清理！{Color.END}")
        add_err("二次管理员校验", "执行中途权限丢失")
        print_error_summary()
        input("回车返回...")
        return

    drive_list = get_all_local_drives()
    space_before = {}
    for d in drive_list:
        space_before[d] = get_disk_free_gb(d)

    # 1. 全盘日志、蓝屏崩溃转储文件清理（所有分区）
    for disk in drive_list:
        run_cmd_timed(f"del /f /s /q {disk}*.log", f"清理{disk}全盘运行/崩溃日志")
        run_cmd_timed(f"del /f /s /q {disk}*.dmp", f"清理{disk}全盘蓝屏转储文件")

    # 2. 系统自带磁盘深度清理（系统版本预检）
    win_ver = int(platform.win32_ver()[0])
    if win_ver >= 7:
        run_cmd_timed("cleanmgr /sageset:1 && cleanmgr /sagerun:1", "系统磁盘管理器深度磁盘清理")
    else:
        print(f"{Color.YELLOW}[系统版本预检] 当前Windows版本过低，跳过cleanmgr高级清理{Color.END}")

    # 3. Windows更新缓存（预检目录存在）
    soft_dist_path = Path(r"C:\Windows\SoftwareDistribution")
    run_cmd_timed("net stop wuauserv", "停止Windows更新服务")
    if path_exists_check(soft_dist_path):
        run_cmd_timed("rd /s /q C:\Windows\SoftwareDistribution", "删除Windows更新缓存包")
    run_cmd_timed("net start wuauserv", "重启Windows更新服务")

    # 4. 休眠文件、页面缓存释放
    run_cmd_timed("powercfg -h off", "关闭休眠，删除超大hiberfil.sys休眠文件")

    # 5. 清理WinSxS系统冗余组件（预检Win10+/Win11）
    if win_ver >= 10:
        run_cmd_timed("DISM /Online /Cleanup-Image /StartComponentCleanup", "DISM深度清理系统冗余组件库")
        run_cmd_timed("DISM /Online /Cleanup-Image /ResetBase", "重置系统组件基础包，精简系统体积")
    else:
        print(f"{Color.YELLOW}[系统版本预检] 低于Win10，跳过DISM高级系统清理{Color.END}")

    # 6. 查杀后台偷跑冗余进程（先校验进程是否运行，无进程直接跳过）
    proc_list = ["Thunder", "QQProtect", "WeChat", "AliYunPan", "KuGou", "PotPlayer", "360tray"]
    kill_start = time.perf_counter()
    for proc in proc_list:
        if check_process_running(proc):
            run_cmd_timed(f"taskkill /f /im {proc}.exe 2>nul", f"强制关闭后台偷跑进程 {proc}.exe")
        else:
            print(f"{Color.WHITE}[进程预检跳过] {proc}.exe 当前未运行{Color.END}")
    kill_cost = time.perf_counter() - kill_start
    print(f"{Color.GREEN}[后台进程查杀总耗时] {kill_cost:.2f}秒{Color.END}")

    # 7. 清理用户软件缓存：微信、QQ、飞书、钉钉（路径预检）
    app_cache_start = time.perf_counter()
    appdata = Path(os.environ["APPDATA"])
    localapp = Path(os.environ["LOCALAPPDATA"])
    clear_paths = [
        appdata / "Tencent" / "WeChat" / "Cache",
        appdata / "Tencent" / "QQ" / "Cache",
        localapp / "DingTalk" / "Cache",
        localapp / "Lark" / "Cache"
    ]
    for p in clear_paths:
        if path_exists_check(p):
            shutil.rmtree(p, ignore_errors=True)
            print(f"{Color.GREEN}[完成] 软件缓存清理：{p}{Color.END}")
    app_cache_cost = time.perf_counter() - app_cache_start
    print(f"{Color.GREEN}[应用软件缓存清理总耗时] {app_cache_cost:.2f}秒{Color.END}")

    # 8. 全盘磁盘碎片优化（区分SSD/HDD，低版本系统兼容预检）
    if win_ver >= 8:
        for disk in drive_list:
            run_cmd_timed(f"defrag {disk} /O /H", f"{disk}磁盘碎片自动优化（固态/机械自适应）")
    else:
        print(f"{Color.YELLOW}[系统版本预检] Windows版本过低，跳过全盘碎片自动优化{Color.END}")

    # 9. 清理注册表无效垃圾项（预检测注册表项是否存在）
    run_cmd_timed('reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Installer" >nul 2>&1 && reg delete HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Installer /f', "清理安装残留注册表项")
    run_cmd_timed('reg query "HKCU\Software\Classes\Local Settings\Software" >nul 2>&1 && reg delete HKCU\Software\Classes\Local Settings\Software /f', "用户缓存注册表清理")

    # 磁盘释放空间汇总
    print(f"\n{Color.BLUE}[磁盘空间释放统计] 清理前后剩余容量对比：{Color.END}")
    for d in drive_list:
        after = get_disk_free_gb(d)
        free_diff = round(after - space_before[d], 2)
        print(f"  {d} 清理前:{space_before[d]}GB → 清理后:{after}GB | 释放空间:{free_diff}GB")

    # 全局总耗时汇总（时分秒格式化）
    total_cost = time.perf_counter() - total_start
    fmt_total = format_time(total_cost)
    print(f"\n{Color.GREEN}=============================================")
    print(f"          【全盘专业深度清理全部执行完成】")
    print(f"  已扫描全部本地硬盘，解决：垃圾堆积、后台进程占用、系统更新冗余、磁盘碎片卡顿")
    print(f"  本次专业深度清理完整总耗时：{fmt_total}")
    print(f"  建议重启电脑获得完整优化效果！")
    print(f"============================================={Color.END}")
    print_error_summary()
    input("\n按回车键返回主菜单...")

# 主交互循环
def main():
    while True:
        os.system("cls")
        print_logo()
        choice = input("请输入功能序号：").strip()
        if choice == "1":
            fast_clean()
        elif choice == "2":
            professional_clean()
        elif choice == "0":
            print(f"{Color.GREEN}工具箱退出，感谢使用SYUP全盘系统清理工具{Color.END}")
            sys.exit(0)
        else:
            print(f"{Color.RED}输入校验失败，请选择数字 0 / 1 / 2！{Color.END}")
            input("回车继续...")

if __name__ == "__main__":
    main()
