from typing import List

from nonebot import get_plugin_config
from pydantic import BaseModel


class Config(BaseModel):
    meme_generator_base_url: str = "http://127.0.0.1:2233"
    memes_command_start: List[str] = []
    memes_command_force_whitespace: bool = True
    memes_disabled_list: List[str] = []
    memes_prompt_params_error: bool = False
    memes_use_sender_when_no_image: bool = False
    memes_use_default_when_no_text: bool = False


memes_config = get_plugin_config(Config)
