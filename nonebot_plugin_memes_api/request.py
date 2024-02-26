import json
from typing import Any, Dict, List, Literal, Optional, Tuple, Union, cast, overload

import httpx
from nonebot.compat import model_dump, type_validate_python
from pydantic import BaseModel

from .config import memes_config
from .exception import (
    ArgMismatch,
    ArgModelMismatch,
    ArgParserExit,
    ImageNumberMismatch,
    MemeGeneratorException,
    NoSuchMeme,
    OpenImageFailed,
    ParamsMismatch,
    ParserExit,
    TextNumberMismatch,
    TextOrNameNotEnough,
    TextOverLength,
)

BASE_URL = memes_config.meme_generator_base_url


@overload
async def send_request(
    router: str,
    request_type: Literal["POST", "GET"],
    response_type: Literal["JSON"],
    **kwargs,
) -> Union[Dict[str, Any], List[Any]]:
    ...


@overload
async def send_request(
    router: str,
    request_type: Literal["POST", "GET"],
    response_type: Literal["BYTES"],
    **kwargs,
) -> bytes:
    ...


@overload
async def send_request(
    router: str,
    request_type: Literal["POST", "GET"],
    response_type: Literal["TEXT"],
    **kwargs,
) -> str:
    ...


async def send_request(
    router: str,
    request_type: Literal["POST", "GET"],
    response_type: Literal["JSON", "BYTES", "TEXT"],
    **kwargs,
):
    async with httpx.AsyncClient(timeout=300) as client:
        request_method = client.post if request_type == "POST" else client.get
        resp = await request_method(BASE_URL + router, **kwargs)
        status_code = resp.status_code
        if status_code == 200:
            if response_type == "JSON":
                return resp.json()
            elif response_type == "BYTES":
                return resp.content
            else:
                return resp.text
        elif 520 <= status_code < 600:
            message = resp.json()["detail"]
            if status_code == 551:
                raise ArgParserExit(message)
            elif status_code == 552:
                raise ArgModelMismatch(message)
            elif 550 <= status_code < 560:
                raise ArgMismatch(message)
            elif status_code == 541:
                raise ImageNumberMismatch(message)
            elif status_code == 542:
                raise TextNumberMismatch(message)
            elif status_code == 543:
                raise TextOrNameNotEnough(message)
            elif 540 <= status_code < 550:
                raise ParamsMismatch(message)
            elif status_code == 531:
                raise NoSuchMeme(message)
            elif status_code == 532:
                raise TextOverLength(message)
            elif status_code == 533:
                raise OpenImageFailed(message)
            elif status_code == 534:
                raise ParserExit(message)
            else:
                raise MemeGeneratorException(message)


ColorType = Union[str, Tuple[int, int, int], Tuple[int, int, int, int]]
FontStyle = Literal["normal", "italic", "oblique"]
FontWeight = Literal["ultralight", "light", "normal", "bold", "ultrabold", "heavy"]


class MemeKeyWithProperties(BaseModel):
    meme_key: str
    fill: ColorType = "black"
    style: FontStyle = "normal"
    weight: FontWeight = "normal"
    stroke_width: int = 0
    stroke_fill: Optional[ColorType] = None


class RenderMemeListRequest(BaseModel):
    meme_list: Optional[List[MemeKeyWithProperties]] = None
    order_direction: Literal["row", "column"] = "column"
    columns: int = 4
    column_align: Literal["left", "center", "right"] = "left"
    item_padding: Tuple[int, int] = (15, 6)
    image_padding: Tuple[int, int] = (50, 50)
    bg_color: ColorType = "white"
    fontsize: int = 30
    fontname: str = ""
    fallback_fonts: List[str] = []


async def render_meme_list(request: RenderMemeListRequest) -> bytes:
    return await send_request(
        "/memes/render_list", "POST", "BYTES", json=model_dump(request)
    )


async def get_meme_keys() -> List[str]:
    return cast(List[str], await send_request("/memes/keys", "GET", "JSON"))


class MemeArgs(BaseModel):
    name: str
    type: str
    description: Optional[str] = None
    default: Optional[Any] = None
    enum: Optional[List[Any]] = None


class MemeParams(BaseModel):
    min_images: int = 0
    max_images: int = 0
    min_texts: int = 0
    max_texts: int = 0
    default_texts: List[str] = []
    args: List[MemeArgs] = []


class MemeInfo(BaseModel):
    key: str
    keywords: List[str] = []
    patterns: List[str] = []
    params: MemeParams = MemeParams()


async def get_meme_info(meme_key: str) -> MemeInfo:
    return type_validate_python(
        MemeInfo, await send_request(f"/memes/{meme_key}/info", "GET", "JSON")
    )


async def generate_meme_preview(meme_key: str) -> bytes:
    return await send_request(f"/memes/{meme_key}/preview", "GET", "BYTES")


async def parse_meme_args(meme_key: str, args: List[str] = []) -> Dict[str, Any]:
    return cast(
        Dict[str, Any],
        await send_request(f"/memes/{meme_key}/parse_args", "POST", "JSON", json=args),
    )


async def generate_meme(
    meme_key: str, images: List[bytes], texts: List[str], args: Dict[str, Any]
) -> bytes:
    files = [("images", image) for image in images]
    data = {"texts": texts, "args": json.dumps(args)}
    return await send_request(
        f"/memes/{meme_key}/", "POST", "BYTES", files=files, data=data
    )
