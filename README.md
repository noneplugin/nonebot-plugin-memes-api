<div align="center">

  <a href="https://nonebot.dev/">
    <img src="https://nonebot.dev/logo.png" width="200" height="200" alt="nonebot">
  </a>

# nonebot-plugin-memes-api

_✨ [Nonebot2](https://github.com/nonebot/nonebot2) 表情包制作插件 调用 api 版本 ✨_

<p align="center">
  <img src="https://img.shields.io/github/license/noneplugin/nonebot-plugin-memes-api" alt="license">
  <img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/nonebot-2.3.0+-red.svg" alt="NoneBot">
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
> 可以将本插件与 [meme-generator](https://github.com/MemeCrafters/meme-generator-rs) 分开部署

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

#### 配置驱动器 ​

插件需要“客户端型驱动器”（如 httpx）来下载图片等，驱动器安装和配置参考 [NoneBot 选择驱动器](https://nonebot.dev/docs/advanced/driver)

同时需要在 `.env.*` 配置文件中启用对应的驱动器，例如：

```
DRIVER=~fastapi+~httpx+~websockets
```

### 配置项

> 以下配置项可在 `.env.*` 文件中设置，具体参考 [NoneBot 配置方式](https://nonebot.dev/docs/appendices/config)

#### `meme_generator_base_url`

- 类型：`str`
- 默认：`http://127.0.0.1:2233`
- 说明：`meme-generator` web server 地址

#### `memes_command_prefixes`

- 类型：`List[str] | None`
- 默认：`None`
- 说明：命令前缀（仅作用于制作表情的命令）；如果不设置默认使用 [NoneBot 命令前缀](https://nonebot.dev/docs/appendices/config#command-start-和-command-separator)

#### `memes_disabled_list`

- 类型：`List[str]`
- 默认：`[]`
- 说明：禁用的表情包列表，需填写表情的`key`，可在 [meme-generator 表情列表](https://github.com/MeetWq/meme-generator/blob/main/docs/memes.md) 中查看。若只是临时关闭，可以用下文中的“表情包开关”

#### `memes_params_mismatch_policy`

- 类型：`MemeParamsMismatchPolicy`
- 说明：图片/文字数量不符时的处理方式，其中具体设置项如下：
  - `too_much_text`
    - 类型：`str`
    - 默认：`"ignore"`
    - 可选项：`"ignore"`（忽略本次命令）、 `"prompt"`（发送提示）, `"drop"`（去掉多余的文字）
  - `too_few_text`
    - 类型：`str`
    - 默认：`"ignore"`
    - 可选项：`"ignore"`（忽略本次命令）、 `"prompt"`（发送提示）, `"get"`（交互式获取所需的文字）
  - `too_much_image`
    - 类型：`str`
    - 默认：`"ignore"`
    - 可选项：`"ignore"`（忽略本次命令）、 `"prompt"`（发送提示）, `"drop"`（去掉多余的图片）
  - `too_few_image`
    - 类型：`str`
    - 默认：`"ignore"`
    - 可选项：`"ignore"`（忽略本次命令）、 `"prompt"`（发送提示）, `"get"`（交互式获取所需的图片）
- `memes_params_mismatch_policy` 在 `.env` 文件中的设置示例如下：

```
memes_params_mismatch_policy='
{
  "too_much_text": "drop",
  "too_few_text": "get",
  "too_much_image": "drop",
  "too_few_image": "get"
}
'
```

#### `memes_use_sender_when_no_image`

- 类型：`bool`
- 默认：`False`
- 说明：在表情需要至少 1 张图且没有输入图片时，是否使用发送者的头像

#### `memes_use_default_when_no_text`

- 类型：`bool`
- 默认：`False`
- 说明：在表情需要至少 1 段文字且没有输入文字时，是否使用默认文字

#### `memes_random_meme_show_info`

- 类型：`bool`
- 默认：`True`
- 说明：使用“随机表情”时是否同时发出表情关键词

#### `memes_list_image_config`

- 类型：`MemeListImageConfig`
- 说明：表情列表图相关设置，其中具体设置项如下：
  - `sort_by`
    - 类型：`str`
    - 默认：`"keywords"`
    - 说明：表情排序方式，可用值：`"key"`（按表情 `key` 排序）、`"keywords"`（按表情首个关键词排序）、`"date_created"`（按表情添加时间排序）、`"date_modified"`（按表情修改时间排序）
  - `sort_reverse`
    - 类型：`bool`
    - 默认：`False`
    - 说明：是否倒序排序
  - `text_template`
    - 类型：`str`
    - 默认：`"{keywords}"`
    - 说明：表情显示文字模板，可用变量：`"{index}"`（序号）、`"{key}"`（表情名）、`"{keywords}"`（关键词）、`"{shortcuts}"`（快捷指令）、`"{tags}"`（标签）
  - `add_category_icon`
    - 类型：`bool`
    - 默认：`True`
    - 说明：是否添加图标以表示类型，即“图片表情包”和“文字表情包”
  - `label_new_timedelta`
    - 类型：`timedelta`
    - 默认：`timedelta(days=30)`
    - 说明：表情添加时间在该时间间隔以内时，添加 `new` 图标
  - `label_hot_threshold`
    - 类型：`int`
    - 默认：`21`
    - 说明：单位：次；表情在 `label_hot_days` 内的调用次数超过该阈值时，添加 `hot` 图标
  - `label_hot_days`
    - 类型：`int`
    - 默认：`7`
    - 说明：单位：天；表情调用次数统计周期
- `memes_list_image_config` 在 `.env` 文件中的设置示例如下：

```
memes_list_image_config='
{
  "sort_by": "keywords",
  "sort_reverse": false,
  "text_template": "{keywords}",
  "add_category_icon": true,
  "label_new_timedelta": "P30D",
  "label_hot_threshold": 21,
  "label_hot_days": 7
}
'
```

### 使用

使用方式与 [nonebot-plugin-memes](https://github.com/noneplugin/nonebot-plugin-memes) 基本一致
