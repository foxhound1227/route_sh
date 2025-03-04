#!/bin/sh

# Natter/NATMap
public_port=$1 # Natter: $5; NATMap: $2

# qBittorrent.
qb_web_host="10.8.1.5"
qb_web_port="8085"
qb_username="admin"
qb_password="bruce1227nancy"

echo "Update qBittorrent listen port to $public_port..."

# Update qBittorrent listen port.
qb_cookie=$(curl -s -i --header "Referer: http://$qb_web_host:$qb_web_port" --data "username=$qb_username&password=$qb_password" http://$qb_web_host:$qb_web_port/api/v2/auth/login | grep -i set-cookie | cut -c13-48)
curl -X POST -b "$qb_cookie" -d 'json={"listen_port":"'$public_port'"}' "http://$qb_web_host:$qb_web_port/api/v2/app/setPreferences"

echo "Update iptables..."
sed -i "/23888/{nn;s/.*/        option dest_port '$public_port'/;}" /etc/config/firewall
sed -i "/IPV6_PT/{nnn;s/.*/        option dest_port '$public_port'/;}" /etc/config/firewall
/etc/init.d/firewall reload > /mnt/mmcblk0p3/firewall.log

echo "Done."
