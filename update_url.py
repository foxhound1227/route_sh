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
remote_file_path = '/www/server/panel/vhost/nginx/redirect/fn.200333.xyz/ee7af3c0125a23a348f39b2c8a6d7339_fn.200333.xyz.conf'

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

        print(f"当前文件内容中的值: {old_text}")
        print("原始内容片段：")
        print(current_content[:500])

        # 修改替换逻辑，使用更精确的匹配模式
        old_pattern = f"-nas.200333.xyz:{old_text}"
        new_pattern = f"-nas.200333.xyz:{new_text}"
        new_content = current_content.replace(old_pattern, new_pattern)

        # 检查是否有修改
        if current_content == new_content:
            print(f"警告：未能找到匹配的端口号 {old_text}")
        else:
            print("检测到以下修改：")
            print(f"将替换所有 {old_pattern} 为 {new_pattern}")
            
            # 使用临时文件来确保写入正确
            temp_file = "/tmp/caddy_temp"
            stdin, stdout, stderr = ssh.exec_command(f'echo \'{new_content}\' > {temp_file} && cat {temp_file} > {remote_file_path} && rm {temp_file}')
            error_output = stderr.read().decode()
            if error_output:
                print(f"错误: {error_output}")
            else:
                print(f"文件 {remote_file_path} 修改成功！")

            # 将新的值写入本地文件
            with open(local_value_file, 'w') as f:
                f.write(new_text)
            print(f"已将新值 '{new_text}' 写入本地文件。")

            # 重新加载 Nginx 配置
            reload_command = "/etc/init.d/nginx reload"
            stdin, stdout, stderr = ssh.exec_command(reload_command)

            # 检查重载命令执行结果
            reload_error = stderr.read().decode()
            if reload_error:
                print(f"重载 Nginx 配置时出错: {reload_error}")
            else:
                print("Nginx 配置重载成功！")

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
