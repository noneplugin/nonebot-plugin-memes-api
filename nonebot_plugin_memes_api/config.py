from typing import List

from nonebot import get_driver
from pydantic import BaseModel, Extra


class Config(BaseModel, extra=Extra.ignore):
    meme_generator_base_url: str = "http://127.0.0.1:2233"
    memes_command_start: List[str] = []
    memes_command_force_whitespace: bool = True
    memes_disabled_list: List[str] = []
    memes_prompt_params_error: bool = False
    memes_use_sender_when_no_image: bool = False
    memes_use_default_when_no_text: bool = False


memes_config = Config.parse_obj(get_driver().config.dict())
