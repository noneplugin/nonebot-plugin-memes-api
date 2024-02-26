<div align="center">

  <a href="https://nonebot.dev/">
    <img src="https://nonebot.dev/logo.png" width="200" height="200" alt="nonebot">
  </a>

# nonebot-plugin-memes-api

_✨ [Nonebot2](https://github.com/nonebot/nonebot2) 表情包制作插件 调用 api 版本 ✨_

<p align="center">
  <img src="https://img.shields.io/github/license/noneplugin/nonebot-plugin-memes-api" alt="license">
  <img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/nonebot-2.2.0+-red.svg" alt="NoneBot">
  <a href="https://pypi.org/project/nonebot-plugin-memes-api">
    <img src="https://badgen.net/pypi/v/nonebot-plugin-memes-api" alt="pypi">
  </a>
  <a href="https://jq.qq.com/?_wv=1027&k=wDVNrMdr">
    <img src="https://img.shields.io/badge/QQ%E7%BE%A4-682145034-orange" alt="qq group">
  </a>
</p>

</div>

> 本插件为 [nonebot-plugin-memes](https://github.com/noneplugin/nonebot-plugin-memes) 调用 api 版本
>
> 可以将本插件与 [meme-generator](https://github.com/MeetWq/meme-generator) 分开部署

### 安装

- 使用 nb-cli

```
nb plugin install nonebot_plugin_memes_api
```

- 使用 pip

```
pip install nonebot_plugin_memes_api
```

并按照 [NoneBot 加载插件](https://nonebot.dev/docs/tutorial/create-plugin#加载插件) 加载插件

#### meme-generator 部署

按照 [meme-generator 安装](https://github.com/MeetWq/meme-generator#安装) 中的说明安装，并下载图片、安装字体等

之后通过 `meme run` 启动 web server

### 配置项

> 以下配置项可在 `.env.*` 文件中设置，具体参考 [NoneBot 配置方式](https://nonebot.dev/docs/appendices/config)

#### `meme_generator_base_url`

- 类型：`str`
- 默认：`http://127.0.0.1:2233`
- 说明：meme-generator web server 地址

#### `memes_command_start`

- 类型：`List[str]`
- 默认：`[]`
- 说明：命令前缀，若不配置则使用 [NoneBot 命令前缀](https://nonebot.dev/docs/appendices/config#command-start-和-command-separator)

#### `memes_command_force_whitespace`

- 类型：`bool`
- 默认：`True`
- 说明：是否强制要求命令后加空格（仅当命令后是文本时需要加空格）

#### `memes_disabled_list`

- 类型：`List[str]`
- 默认：`[]`
- 说明：禁用的表情包列表，需填写表情的`key`，可在 [meme-generator 表情列表](https://github.com/MeetWq/meme-generator/blob/main/docs/memes.md) 中查看。若只是临时关闭，可以用下文中的“表情包开关”

#### `memes_prompt_params_error`

- 类型：`bool`
- 默认：`False`
- 说明：是否在图片/文字数量不符或参数解析错误时提示（若没有设置命令前缀不建议开启，否则极易误触发）

#### `memes_use_sender_when_no_image`

- 类型：`bool`
- 默认：`False`
- 说明：在表情需要至少1张图且没有输入图片时，是否使用发送者的头像（谨慎使用，容易误触发）

#### `memes_use_default_when_no_text`

- 类型：`bool`
- 默认：`False`
- 说明：在表情需要至少1段文字且没有输入文字时，是否使用默认文字（谨慎使用，容易误触发）

### 使用

使用方式与 [nonebot-plugin-memes](https://github.com/noneplugin/nonebot-plugin-memes) 基本一致
