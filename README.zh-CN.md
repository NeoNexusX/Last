# Last

[English](README.md) | [简体中文](README.zh-CN.md)

## 项目介绍：

一个基于 FastAPI 构建的服务器监控与管理工具，通过 SSH 协议远程监控和管理中小规模 Linux【已支持】/MacOS【将会支持】/Windows 【可能会支持，欢迎贡献】 服务器，提供全面的硬件监控和账户管理功能。

## ✨ 核心功能

### 🖥️ **服务器监控**

- **CPU**：使用率、核心数、负载状态
- **内存**：实时用量、缓存、交换空间
- **磁盘**：存储空间、读写速度、挂载点
- **GPU**（NVIDIA，目前仅有，无其他设备）：显存占用、利用率

### 🔐 **安全管理**

- **SSH 密钥管理**
- **登录审计日志** 
- **服务器账户管理**
- **账户密码修改**（支持 `passwd` ）
- **一键统一账户密码**【正在开发】
- **批量服务器账户注销** 【正在开发】
- **个性化命令批量服务器账户注册** 【正在开发】
- **加密算法数据库保护** 【正在开发】

### ⚙️ **运维工具**

- **服务状态检查**（`systemd`/`service`）
- **日志文件查看**（`tail`/`grep` 集成）【正在开发】
- **批量执行命令**（支持 `sudo`）【正在开发】

### 📊 **数据可视化**

- 右转前端项目

  BioSerWeb： https://github.com/NeoNexusX/BioSerWeb 

- **RESTful API** 数据接口

## 技术栈 🛠️

|   类别   |      技术选型       |
| :------: | :-----------------: |
| 后端框架 |       FastAPI       |
|  数据库  |  SQLite (SQLModel)  |
| SSH连接  |  Paramiko//fabric   |
| 数据模型 | Pydantic + SQLModel |
| 异步支持 | Python async/await  |
| 日志系统 |   Python logging    |

## 快速开始 🚀

1. **安装依赖**

   bash

   ```bash
   pip install -r requirements.txt
   ```

2. **配置环境**
   复制`.env.example`为`.env`并填写您的服务器信息

3. **启动服务**

   bash

   ```bash
   uvicorn main:app --reload
   ```

4. **访问API文档**
   浏览器打开 `http://localhost:8000/docs`

### 目录介绍

```bash
# 项目根目录
├── LICENSE # 开源许可证文件（如MIT/GPL协议）
├── README.md # 项目说明文档
├── api/ # API接口模块
│ ├── init.py # Python包初始化文件
│ ├── auth_api.py # 认证相关API（基于令牌的认证等）
│ ├── serverapi.py # 服务器管理API
│ └── userapi.py # 用户管理API（包含登录/注销功能）
├── database/ # 数据库相关文件
│ ├── bionet.db # SQLite数据库文件（自动生成于此）
│ └── db.py # 数据库连接与操作
├── logger.py # 日志系统配置
├── logs/ # 日志存储目录
│ ├── app.log # 应用程序运行日志
│ └── error.log # 错误日志
├── main.py # 程序主入口文件
├── models/ # 数据模型目录
│ ├── init.py
│ ├── auth.py # 认证相关数据模型
│ ├── server_models.py # 服务器数据模型
│ └── user_models.py # 用户数据模型
├── requirements.txt # Python依赖包列表
└── ssh/ # SSH功能模块
├── init.py
└── ssh_manager.py # SSH连接池管理
```

## 

##  🌟使用场景示例

- **IT运维团队**：集中监控中小企业所有开发服务器的健康状态
- **研究人员**：实时跟踪科研中小规模GPU服务器的计算资源使用情况
- **个人开发者**：管理自己的多台VPS和云主机

## 🤝 贡献指南

### 如何参与？

1. **报告问题**：提交详细的 Bug 报告
2. **开发功能**：认领 `Good First Issue`
3. **改进文档**：优化 README 或翻译

### 代码要求

- 符合 **GPL-3.0** 传染性条款
- 通过 `pre-commit` 代码检查
- 添加单元测试（`pytest`）【将会支持】目前暂时不需要

## 📜 许可证

**GNU General Public License v3.0 (GPL-3.0)**

- ✅ 允许自由使用、修改和分发
- ✅ 要求开源衍生作品
- ❌ 禁止闭源商业化
