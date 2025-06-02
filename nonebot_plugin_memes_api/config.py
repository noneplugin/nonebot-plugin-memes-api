from datetime import timedelta
from typing import Literal, Optional

from nonebot import get_plugin_config
from pydantic import BaseModel


class MemeListImageConfig(BaseModel):
    sort_by: Literal["key", "keywords", "date_created", "date_modified"] = "keywords"
    sort_reverse: bool = False
    text_template: str = "{keywords}"
    add_category_icon: bool = True
    label_new_timedelta: timedelta = timedelta(days=30)
    label_hot_threshold: int = 21
    label_hot_days: int = 7


class MemeParamsMismatchPolicy(BaseModel):
    too_much_text: Literal["ignore", "prompt", "drop"] = "ignore"
    too_few_text: Literal["ignore", "prompt", "get"] = "ignore"
    too_much_image: Literal["ignore", "prompt", "drop"] = "ignore"
    too_few_image: Literal["ignore", "prompt", "get"] = "ignore"


class MultipleImageConfig(BaseModel):
    direct_send_threshold: int = 10
    send_zip_file: bool = True
    send_forward_msg: bool = False


class Config(BaseModel):
    meme_generator_base_url: str = "http://127.0.0.1:2234"
    memes_command_prefixes: Optional[list[str]] = None
    memes_disabled_list: list[str] = []
    memes_check_resources_on_startup: bool = True
    memes_params_mismatch_policy: MemeParamsMismatchPolicy = MemeParamsMismatchPolicy()
    # memes_prompt_params_error: bool = False
    memes_use_sender_when_no_image: bool = False
    memes_use_default_when_no_text: bool = False
    memes_random_meme_show_info: bool = True
    memes_list_image_config: MemeListImageConfig = MemeListImageConfig()
    memes_multiple_image_config: MultipleImageConfig = MultipleImageConfig()


memes_config = get_plugin_config(Config)
ban_path = ".."  # 默认在Bot文件夹外 可改为 ./data/ban
use_gif = False  # 是否使用gif表情
resize_image = True  # 是否缩放图片
resize_image_size = 360  # 缩放图片的最大尺寸

assert use_gif or resize_image, "use_gif和resize_image不能同时启用"
