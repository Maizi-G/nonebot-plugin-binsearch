<div align="center">

<a href="https://v2.nonebot.dev/store">
  <img src="https://raw.githubusercontent.com/A-kirami/nonebot-plugin-template/resources/nbp_logo.png" width="180" height="180" alt="NoneBotPluginLogo">
</a>

<p>
  <img src="https://raw.githubusercontent.com/lgc-NB2Dev/readme/main/template/plugin.svg" alt="NoneBotPluginText">
</p>

# nonebot-plugin-binsearch

_✨ 一个Nonebot2插件用于查询信用卡的卡组织，卡等级，卡类型，发卡国等✨_


<a href="./LICENSE">
    <img src="https://img.shields.io/github/license/bankcarddev/nonebot-plugin-binsearch.svg" alt="license">
</a>
<a href="https://pypi.python.org/pypi/nonebot-plugin-binsearch">
    <img src="https://img.shields.io/pypi/v/nonebot-plugin-binsearch.svg" alt="pypi">
</a>
<img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="python">

</div>



</details>

## 📖 介绍

一个Nonebot2插件用于查询信用卡的卡组织，卡等级，卡类型，发卡国等

## 💿 安装

<details open>
<summary>使用 nb-cli 安装</summary>
在 nonebot2 项目的根目录下打开命令行, 输入以下指令即可安装

    nb plugin install nonebot-plugin-binsearch

</details>

<details>
<summary>使用包管理器安装</summary>
在 nonebot2 项目的插件目录下, 打开命令行, 根据你使用的包管理器, 输入相应的安装命令

<details>
<summary>pip</summary>

    pip install nonebot-plugin-binsearch
</details>
<details>
<summary>pdm</summary>

    pdm add nonebot-plugin-binsearch
</details>
<details>
<summary>poetry</summary>

    poetry add nonebot-plugin-binsearch
</details>
<details>
<summary>conda</summary>

    conda install nonebot-plugin-binsearch
</details>

打开 nonebot2 项目根目录下的 `pyproject.toml` 文件, 在 `[tool.nonebot]` 部分追加写入

    plugins = ["nonebot_plugin_binsearch"]

</details>

## ⚙️ 配置

在 nonebot2 项目的`.env`文件中添加下表中的必填配置

| 配置项 | 必填 | 默认值 | 说明 |
|:-----:|:----:|:----:|:----:|
| bin_api_key | 是 | 无 | 你的bin查询api秘钥 |
| ignore_user_ids | 否 | [3938088854] | 忽略查询的用户 ID 列表 |
| bin_user_cooldown | 否 | 10 | 单个用户查询冷却时间，单位秒；设为 0 可关闭 |
| bin_group_cooldown | 否 | 3 | 单个群查询冷却时间，单位秒；设为 0 可关闭 |
> [!NOTE]
> ### 🔑 如何获取API Key？
>
> 前往以下页面申请API Key：
> [申请页面](https://rapidapi.com/trade-expanding-llc-trade-expanding-llc-default/api/bin-ip-checker/pricing)
> 每月限制查询 **500 次**，你可以通过多账号申请轮换API Key，以避免超出查询限制。


## 🎉 使用
### 指令表
| 指令 | 权限 | 需要@ | 范围 | 说明 |
|:-----:|:----:|:----:|:----:|:----:|
| bin 6位bin | 群员 | 是 | 全局 | 查询bin |
## TODO
- [ ] **多API Key负载均衡**
- [x] **查询速度限制**
- [ ] **API响应缓存**


