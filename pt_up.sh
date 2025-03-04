#!/bin/sh

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# 更新 qBittorrent 端口
update_qbittorrent() {
    local port=$1
    local qb_cookie
    
    log "正在更新 qBittorrent 监听端口为 $port..."
    
    qb_cookie=$(curl -s -i --header "Referer: http://$qb_web_host:$qb_web_port" \
                --data "username=$qb_username&password=$qb_password" \
                "http://$qb_web_host:$qb_web_port/api/v2/auth/login" | \
                grep -i set-cookie | cut -c13-48)
    
    if [ -z "$qb_cookie" ]; then
        log "错误：无法获取 qBittorrent 认证信息"
        return 1
    fi
    
    curl -X POST -b "$qb_cookie" \
         -d 'json={"listen_port":"'$port'"}' \
         "http://$qb_web_host:$qb_web_port/api/v2/app/setPreferences"
    
    if [ $? -ne 0 ]; then
        log "错误：更新 qBittorrent 端口失败"
        return 1
    fi
}

# 更新防火墙规则
update_firewall() {
    local port=$1
    
    log "正在更新防火墙规则..."
    
    sed -i "/23888/{nn;s/.*/        option dest_port '$port'/;}" /etc/config/firewall
    sed -i "/IPV6_PT/{nnn;s/.*/        option dest_port '$port'/;}" /etc/config/firewall
    
    /etc/init.d/firewall reload > /mnt/mmcblk0p3/firewall.log 2>&1
    if [ $? -ne 0 ]; then
        log "错误：重载防火墙失败"
        return 1
    fi
}

# qBittorrent 配置
qb_web_host="10.8.1.5"
qb_web_port="8085"
qb_username="admin"
qb_password="bruce1227nancy"

# 参数验证
if [ -z "$1" ]; then
    log "错误：未指定端口号"
    exit 1
fi

if ! echo "$1" | grep -q '^[0-9]\+$'; then
    log "错误：端口号必须为数字"
    exit 1
fi

if [ "$1" -lt 1024 ] || [ "$1" -gt 65535 ]; then
    log "错误：端口号必须在 1024-65535 之间"
    exit 1
fi

public_port=$1

# 执行更新操作
if ! update_qbittorrent "$public_port"; then
    exit 1
fi

if ! update_firewall "$public_port"; then
    exit 1
fi

log "所有操作已完成"
