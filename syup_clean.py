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

TOOL_NAME = "SYUP系统清理工具箱 V2.0"
PRO_PASSWORD = "SYUP2026"
VERSION = "2.0"

class Color:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    WHITE = '\033[97m'
    END = '\033[0m'

def print_logo():
    print(Color.BLUE + "=" * 50)
    print(f"{TOOL_NAME}  {VERSION}")
    print("=" * 50 + Color.END)

def format_second(sec: float):
    hour = int(sec // 3600)
    minute = int((sec % 3600) // 60)
    second = round(sec % 60, 2)
    return f"{hour:02d}:{minute:02d}:{second:05.2f}"

def get_disk_free(disk: str):
    try:
        usage = shutil.disk_usage(disk)
        free_gb = usage.free / 1024 / 1024 / 1024
        return round(free_gb, 2)
    except Exception:
        return 0.0

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception as err:
        print(f"{Color.RED}权限检测异常：{str(err)}{Color.END}")
        return False

def run_silent_cmd(cmd: str):
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        returncode = result.returncode
        stderr_msg = result.stderr.strip()
        if returncode != 0 and stderr_msg:
            return False, stderr_msg
        return True, ""
    except Exception as err:
        return False, str(err)

def get_all_local_disk():
    disk_list = []
    abnormal_disk = []
    system_ver = int(platform.win32_ver()[0])
    for char in string.ascii_uppercase:
        target_disk = f"{char}:\\"
        try:
            disk_type = ctypes.windll.kernel32.GetDriveTypeW(target_disk)
            if disk_type == 3:
                os.listdir(target_disk)
                disk_list.append(target_disk)
            elif disk_type == 2:
                print(f"{Color.WHITE}跳过移动存储设备：{target_disk}{Color.END}")
            elif disk_type == 5:
                print(f"{Color.WHITE}跳过光驱设备：{target_disk}{Color.END}")
        except PermissionError:
            abnormal_disk.append(f"{target_disk} 无法访问，权限不足")
        except OSError:
            abnormal_disk.append(f"{target_disk} 磁盘损坏或不存在")
        except Exception as err:
            abnormal_disk.append(f"{target_disk} 未知异常：{str(err)}")
    print(f"{Color.YELLOW}已识别本地磁盘：{disk_list}{Color.END}")
    if abnormal_disk:
        print(f"{Color.RED}异常磁盘列表：{abnormal_disk}{Color.END}")
    return disk_list

def check_process_exist(process_name: str):
    flag, _ = run_silent_cmd(f'tasklist /fi "imagename eq {process_name}.exe"')
    return flag

def clean_recycle_bin(disk: str):
    state, msg = run_silent_cmd(f"rd /s /q {disk}$Recycle.Bin 2>nul")
    if not state and msg:
        print(f"{Color.YELLOW}{disk}回收站清理警告：{msg}{Color.END}")

def clean_user_temp():
    temp_path = Path(os.environ.get("TEMP", ""))
    if temp_path.exists():
        state, msg = run_silent_cmd(f"del /f /s /q {temp_path}\\* 2>nul")
        if not state and msg:
            print(f"{Color.YELLOW}用户临时目录清理警告：{msg}{Color.END}")

def clean_system_temp():
    sys_temp = Path(r"C:\Windows\Temp")
    if sys_temp.exists():
        state, msg = run_silent_cmd(f"del /f /s /q {sys_temp}\\* 2>nul")
        if not state and msg:
            print(f"{Color.YELLOW}系统临时目录清理警告：{msg}{Color.END}")

def clean_browser_cache():
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if not local_app_data:
        print(f"{Color.YELLOW}未读取到本地应用数据目录，跳过浏览器缓存清理{Color.END}")
        return
    chrome_cache = Path(local_app_data) / "Google" / "Chrome" / "User Data" / "Default" / "Cache"
    edge_cache = Path(local_app_data) / "Microsoft" / "Edge" / "User Data" / "Default" / "Cache"
    for cache_dir in [chrome_cache, edge_cache]:
        if cache_dir.exists():
            try:
                shutil.rmtree(cache_dir, ignore_errors=True)
                print(f"{Color.GREEN}已清理缓存目录：{cache_dir}{Color.END}")
            except Exception as err:
                print(f"{Color.RED}缓存目录清理失败 {cache_dir}：{str(err)}{Color.END}")

def clean_download_exe():
    download_dir = Path(os.path.expanduser("~/Downloads"))
    if not download_dir.exists():
        print(f"{Color.YELLOW}下载目录不存在，跳过安装包清理{Color.END}")
        return
    try:
        file_list = list(download_dir.glob("*.exe"))
        for file in file_list:
            try:
                os.remove(file)
            except Exception as err:
                print(f"{Color.YELLOW}文件删除失败 {file.name}：{str(err)}{Color.END}")
    except Exception as err:
        print(f"{Color.RED}读取下载目录失败：{str(err)}{Color.END}")

def quick_clean_task():
    total_start = time.perf_counter()
    disk_arr = get_all_local_disk()
    space_record = {}
    for d in disk_arr:
        space_record[d] = get_disk_free(d)
    print(f"\n{Color.BLUE}开始执行基础清理流程{Color.END}")
    for disk in disk_arr:
        print(f"处理 {disk} 回收站")
        clean_recycle_bin(disk)
    clean_user_temp()
    clean_system_temp()
    clean_browser_cache()
    clean_download_exe()
    print(f"\n{Color.BLUE}磁盘空间变化统计{Color.END}")
    for d in disk_arr:
        after_free = get_disk_free(d)
        release = round(after_free - space_record[d], 2)
        print(f"{d} 清理前 {space_record[d]}GB → 清理后 {after_free}GB，释放空间 {release}GB")
    total_cost = time.perf_counter() - total_start
    time_text = format_second(total_cost)
    print(f"\n{Color.GREEN}基础清理流程执行完成，总耗时 {time_text}{Color.END}")

def professional_clean_task():
    input_key = getpass.getpass("请输入访问密钥：")
    if input_key != PRO_PASSWORD:
        print(f"{Color.RED}密钥校验不通过，终止操作{Color.END}")
        return
    if not is_admin():
        print(f"{Color.RED}当前权限不足，需要管理员身份运行{Color.END}")
        return
    confirm = input("确认执行深度清理操作？(Y/N)").strip().upper()
    if confirm != "Y":
        print("已取消本次操作")
        return
    total_start = time.perf_counter()
    disk_arr = get_all_local_disk()
    space_record = {}
    for d in disk_arr:
        space_record[d] = get_disk_free(d)
    print(f"\n{Color.RED}开始执行深度系统清理流程{Color.END}")
    # 全盘日志、崩溃转储清理
    for disk in disk_arr:
        run_silent_cmd(f"del /f /s /q {disk}*.log 2>nul")
        run_silent_cmd(f"del /f /s /q {disk}*.dmp 2>nul")
    # 系统磁盘清理
    run_silent_cmd("cleanmgr /sageset:1 && cleanmgr /sagerun:1")
    # Windows更新缓存清理
    run_silent_cmd("net stop wuauserv")
    dist_folder = Path(r"C:\Windows\SoftwareDistribution")
    if dist_folder.exists():
        run_silent_cmd("rd /s /q C:\Windows\SoftwareDistribution")
    run_silent_cmd("net start wuauserv")
    # 关闭休眠
    run_silent_cmd("powercfg -h off")
    # DISM系统组件清理
    win_version = int(platform.win32_ver()[0])
    if win_version >= 10:
        run_silent_cmd("DISM /Online /Cleanup-Image /StartComponentCleanup")
        run_silent_cmd("DISM /Online /Cleanup-Image /ResetBase")
    else:
        print(f"{Color.YELLOW}当前系统版本较低，跳过系统组件精简{Color.END}")
    # 后台进程终止
    target_process = ["Thunder", "QQProtect", "WeChat", "AliYunPan", "KuGou", "PotPlayer", "360tray"]
    for proc in target_process:
        if check_process_exist(proc):
            run_silent_cmd(f"taskkill /f /im {proc}.exe 2>nul")
    # 社交软件缓存清理
    app_data = Path(os.environ["APPDATA"])
    local_app = Path(os.environ["LOCALAPPDATA"])
    cache_target = [
        app_data / "Tencent" / "WeChat" / "Cache",
        app_data / "Tencent" / "QQ" / "Cache",
        local_app / "DingTalk" / "Cache",
        local_app / "Lark" / "Cache"
    ]
    for cache_dir in cache_target:
        if cache_dir.exists():
            try:
                shutil.rmtree(cache_dir, ignore_errors=True)
                print(f"{Color.GREEN}已清理软件缓存：{cache_dir}{Color.END}")
            except Exception as err:
                print(f"{Color.RED}缓存清理失败 {cache_dir}：{str(err)}{Color.END}")
    # 磁盘优化
    if win_version >= 8:
        for disk in disk_arr:
            run_silent_cmd(f"defrag {disk} /O /H 2>nul")
    else:
        print(f"{Color.YELLOW}系统版本不支持自动磁盘优化，跳过该步骤{Color.END}")
    # 注册表冗余清理
    run_silent_cmd('reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Installer" >nul 2>&1 && reg delete HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Installer /f')
    run_silent_cmd('reg query "HKCU\Software\Classes\Local Settings\Software" >nul 2>&1 && reg delete HKCU\Software\Classes\Local Settings\Software /f')
    # 空间统计
    print(f"\n{Color.BLUE}磁盘空间变化统计{Color.END}")
    for d in disk_arr:
        after_free = get_disk_free(d)
        release = round(after_free - space_record[d], 2)
        print(f"{d} 清理前 {space_record[d]}GB → 清理后 {after_free}GB，释放空间 {release}GB")
    total_cost = time.perf_counter() - total_start
    time_text = format_second(total_cost)
    print(f"\n{Color.GREEN}深度清理流程执行完成，总耗时 {time_text}{Color.END}")

def launch_admin():
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit(0)

def main():
    launch_admin()
    while True:
        os.system("cls")
        print_logo()
        print("1. 基础快速清理")
        print("2. 深度系统清理")
        print("3. 退出程序")
        user_input = input("请输入功能序号：").strip()
        if user_input == "1":
            quick_clean_task()
        elif user_input == "2":
            professional_clean_task()
        elif user_input == "3":
            print(f"{Color.GREEN}程序正常退出{Color.END}")
            sys.exit(0)
        else:
            print(f"{Color.RED}输入内容无效，请选择1、2、3{Color.END}")
        input("\n按下回车键返回主菜单")

if __name__ == "__main__":
    main()
