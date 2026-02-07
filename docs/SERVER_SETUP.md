# 服务器部署指南

## 快速开始

### 1. 服务器准备
- Ubuntu 20.04/22.04/24.04 操作系统
- 创建专用用户：`sudo adduser spharx`
- 将用户加入docker组：`sudo usermod -aG docker spharx`

### 2. 一键部署（推荐）
```bash
# 登录服务器
ssh spharx@your_server_ip

# 下载部署脚本
curl -O https://gitee.com/spharx/toolchain/raw/master/scripts/setup_server.sh
chmod +x setup_server.sh

# 运行部署脚本
./setup_server.sh
```
### 3. 手动部署

# 1. 创建目录结构
mkdir -p /home/spharx/SpharxWorkshop
cd /home/spharx/SpharxWorkshop

# 2. 克隆仓库
git clone git@gitee.com:spharx/toolchain.git
git clone git@gitee.com:spharx/library.git

# 3. 运行目录初始化
./toolchain/scripts/setup_server.sh