import paramiko
import argparse

# 解析命令行参数
parser = argparse.ArgumentParser(description="远程修改文件内容并记录上一次的值，然后重启 Caddy 服务。")
parser.add_argument('new_text', type=str, help="新的替换值")
args = parser.parse_args()

# 远程服务器信息
hostname = '8.134.95.36'
port = 22  # 默认 SSH 端口
username = 'root'
password = 'Bruce1227Nancy'

# 要修改的文件路径
remote_file_path = '/home/web/caddy/Caddyfile'

# 本地存储上一次值的文件路径
local_value_file = '/mnt/mmcblk0p3/last_value.txt'

# 新的替换值（从命令行参数获取）
new_text = args.new_text

# 创建 SSH 客户端
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    # 连接到远程服务器
    ssh.connect(hostname, port, username, password)
    print("成功连接到远程服务器！")

    # 读取上一次的值
    try:
        with open(local_value_file, 'r') as f:
            old_text = f.read().strip()
            print(f"读取上一次的值: {old_text}")
    except FileNotFoundError:
        old_text = None
        print("未找到上一次的值，首次运行。")

    # 如果存在上一次的值，执行替换
    if old_text:
        # 读取远程文件的当前内容
        stdin, stdout, stderr = ssh.exec_command(f"cat {remote_file_path}")
        current_content = stdout.read().decode()
        stderr.close()
        stdout.close()
        stdin.close()

        # 替换内容
        new_content = current_content.replace(old_text, new_text)

        # 对比修改前后的内容
        if current_content == new_content:
            print("文件内容未发生变化，跳过修改和重启。")
        else:
            # 将新内容写入远程文件
            stdin, stdout, stderr = ssh.exec_command(f"echo '{new_content}' > {remote_file_path}")
            error_output = stderr.read().decode()
            if error_output:
                print(f"错误: {error_output}")
            else:
                print(f"文件 {remote_file_path} 修改成功！")

            # 将新的值写入本地文件
            with open(local_value_file, 'w') as f:
                f.write(new_text)
            print(f"已将新值 '{new_text}' 写入本地文件。")

            # 重启 Caddy 服务
            restart_command = "docker restart caddy"
            stdin, stdout, stderr = ssh.exec_command(restart_command)

            # 检查重启命令执行结果
            restart_error = stderr.read().decode()
            if restart_error:
                print(f"重启 Caddy 服务时出错: {restart_error}")
            else:
                print("Caddy 服务重启成功！")

            # 显式关闭 stdin, stdout, stderr
            stdin.close()
            stdout.close()
            stderr.close()
    else:
        print("未找到上一次的值，跳过替换。")

finally:
    # 关闭 SSH 连接
    ssh.close()
    print("SSH 连接已关闭。")
