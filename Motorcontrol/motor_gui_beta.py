import tkinter as tk
from tkinter import messagebox
from pymodbus.client import ModbusSerialClient
import time

# ------------------- RTU 客户端配置 -------------------
client = ModbusSerialClient(
    port='COM4',  # 根据你实际串口号修改
    baudrate=9600,
    parity='N',
    stopbits=1,
    bytesize=8,
    timeout=1
)

# 当前方向（1 = 正转，-1 = 反转）
direction = 1


# ------------------- 写寄存器函数 -------------------
def send_write_single(address, value):
    result = client.write_register(address=address, value=value, slave=1)
    if result.isError():
        print(f"❌ 写入失败: Addr 0x{address:04X}, Value 0x{value:04X}")
    else:
        print(f"✅ 写入成功: Addr 0x{address:04X}, Value 0x{value:04X}")

def send_write_multiple(start_address, values):
    result = client.write_registers(address=start_address, values=values, slave=1)
    if result.isError():
        print(f"❌ 多寄存器写入失败: Start 0x{start_address:04X}, Values: {values}")
    else:
        print(f"✅ 多寄存器写入成功: Start 0x{start_address:04X}, Values: {values}")

# ------------------- 控制函数 -------------------
def initialize_drive():
    global direction
    try:
        torque_percent = float(torque_entry.get())     # 目标转矩 %
        speed_rpm = float(speed_entry.get())           # 目标速度 rpm
        slope_percent = float(slope_entry.get())       # 转矩斜率 %

        # 单位换算
        torque = int(torque_percent * 10)              # % → ‰
        slope = int(slope_percent * 10)                # % → ‰
        speed = int(speed_rpm * 10)                    # rpm → 0.1rps
    except ValueError:
        messagebox.showerror("输入错误", "请填写有效数字")
        return

    if not client.connect():
        messagebox.showerror("连接失败", "无法连接驱动器，请检查串口")
        return

    try:
        # 设置转矩模式
        send_write_single(0x6060, 0x0004)
        time.sleep(0.1)

        # 写目标速度（单位0.1rps），2个寄存器
        speed_high = (speed >> 16) & 0xFFFF
        speed_low = speed & 0xFFFF
        send_write_multiple(0x6081, [speed_high, speed_low])
        time.sleep(0.1)

        # 写目标转矩（单位‰），支持正/负转向
        torque_signed = torque * direction
        if torque_signed < 0:
            torque_signed = 0x10000 + torque_signed  # 转为16位补码
        send_write_single(0x6071, torque_signed)
        time.sleep(0.1)

        # 写转矩斜率（单位‰）
        send_write_single(0x6087, slope)
        time.sleep(0.1)

        start_button.config(state="normal")
        stop_button.config(state="normal")
        messagebox.showinfo("初始化完成", "参数设置成功，请点击“启动”运行电机。")

    except Exception as e:
        messagebox.showerror("初始化失败", str(e))


def start_motor():
    try:
        send_write_single(0x6040, 0x0001)
        time.sleep(0.1)
        send_write_single(0x6040, 0x0003)
        time.sleep(0.1)
        send_write_single(0x6040, 0x000F)
        time.sleep(0.1)
        send_write_single(0x6040, 0x001F)
        messagebox.showinfo("运行中", "电机已启动")
    except Exception as e:
        messagebox.showerror("启动失败", str(e))

def stop_motor():
    try:
        send_write_single(0x6040, 0x011F)
        messagebox.showinfo("停止", "电机已停止")
    except Exception as e:
        messagebox.showerror("停止失败", str(e))

def quit_program():
    try:
        send_write_single(0x6040, 0x0000)
        time.sleep(0.1)
    except:
        pass
    try:
        client.close()
    except:
        pass
    root.destroy()

# 切换方向函数
def toggle_direction():
    global direction
    direction *= -1
    dir_label.config(text="方向：正转" if direction == 1 else "方向：反转")

# ------------------- GUI -------------------
root = tk.Tk()
root.title("伺服驱动器转矩控制器")
root.geometry("400x350")

tk.Label(root, text="目标转矩 (%):").grid(row=0, column=0, padx=10, pady=10, sticky='e')
torque_entry = tk.Entry(root)
torque_entry.grid(row=0, column=1)

tk.Label(root, text="目标速度 (rps):").grid(row=1, column=0, padx=10, pady=10, sticky='e')
speed_entry = tk.Entry(root)
speed_entry.grid(row=1, column=1)

tk.Label(root, text="转矩斜率 (%):").grid(row=2, column=0, padx=10, pady=10, sticky='e')
slope_entry = tk.Entry(root)
slope_entry.grid(row=2, column=1)

init_button = tk.Button(root, text="初始化", width=12, command=initialize_drive)
init_button.grid(row=3, column=0, pady=20)

start_button = tk.Button(root, text="启动", width=12, command=start_motor, state="disabled")
start_button.grid(row=3, column=1)

stop_button = tk.Button(root, text="停止", width=12, command=stop_motor, state="disabled")
stop_button.grid(row=4, column=0)

exit_button = tk.Button(root, text="退出", width=12, command=quit_program)
exit_button.grid(row=4, column=1)

dir_button = tk.Button(root, text="切换方向", width=12, command=toggle_direction)
dir_button.grid(row=5, column=0, pady=10)

dir_label = tk.Label(root, text="方向：正转")
dir_label.grid(row=5, column=1)

root.mainloop()
