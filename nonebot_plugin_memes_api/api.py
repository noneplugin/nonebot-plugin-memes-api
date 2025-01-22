import base64
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from hashlib import md5
from typing import Any, Literal, Optional, Union, cast, overload

import httpx
from nonebot.compat import model_dump, type_validate_python
from pydantic import BaseModel

from .config import memes_config
from .exception import (
    DeserializeError,
    ImageAssetMissing,
    ImageDecodeError,
    ImageEncodeError,
    ImageNumberMismatch,
    MemeFeedback,
    MemeGeneratorException,
    TextNumberMismatch,
    TextOverLength,
)

BASE_URL = memes_config.meme_generator_base_url


@overload
async def send_request(
    router: str,
    request_type: Literal["POST", "GET"],
    response_type: Literal["JSON"],
    **kwargs,
) -> Union[dict[str, Any], list[Any]]: ...


@overload
async def send_request(
    router: str,
    request_type: Literal["POST", "GET"],
    response_type: Literal["BYTES"],
    **kwargs,
) -> bytes: ...


@overload
async def send_request(
    router: str,
    request_type: Literal["POST", "GET"],
    response_type: Literal["TEXT"],
    **kwargs,
) -> str: ...


async def send_request(
    router: str,
    request_type: Literal["POST", "GET"],
    response_type: Literal["JSON", "BYTES", "TEXT"],
    **kwargs,
):
    async with httpx.AsyncClient(timeout=60) as client:
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

        elif status_code == 500:
            result = resp.json()
            code = result["code"]
            message = result["message"]
            data = result["data"]
            if code == 510:
                error = data["error"]
                raise ImageDecodeError(error)
            elif code == 520:
                error = data["error"]
                raise ImageEncodeError(error)
            elif code == 530:
                path = data["path"]
                raise ImageAssetMissing(path)
            elif code == 540:
                error = data["error"]
                raise DeserializeError(error)
            elif code == 550:
                min = data["min"]
                max = data["max"]
                actual = data["actual"]
                raise ImageNumberMismatch(min, max, actual)
            elif code == 551:
                min = data["min"]
                max = data["max"]
                actual = data["actual"]
                raise TextNumberMismatch(min, max, actual)
            elif code == 560:
                text = data["text"]
                raise TextOverLength(text)
            elif code == 570:
                feedback = data["feedback"]
                raise MemeFeedback(feedback)
            else:
                raise MemeGeneratorException(message)


async def get_version() -> str:
    return cast(str, await send_request("/meme/version", "GET", "TEXT"))


async def get_meme_keys() -> list[str]:
    return cast(list[str], await send_request("/meme/keys", "GET", "JSON"))


async def search_memes(query: str, include_tags: bool = False) -> list[str]:
    return cast(
        list[str],
        await send_request(
            "/meme/search",
            "GET",
            "JSON",
            params={"query": query, "include_tags": include_tags},
        ),
    )


class MemeProperties(BaseModel):
    disabled: bool = False
    hot: bool = False
    new: bool = False


class RenderMemeListParams(BaseModel):
    meme_properties: dict[str, MemeProperties]
    exclude_memes: list[str]
    sort_by: Literal[
        "key", "keywords", "keywords_pinyin", "date_created", "date_modified"
    ]
    sort_reverse: bool
    text_template: str
    add_category_icon: bool


async def render_meme_list(
    meme_properties: dict[str, MemeProperties] = {},
    exclude_memes: list[str] = [],
    sort_by: Literal[
        "key", "keywords", "keywords_pinyin", "date_created", "date_modified"
    ] = "keywords_pinyin",
    sort_reverse: bool = False,
    text_template: str = "{index}. {keywords}",
    add_category_icon: bool = True,
) -> bytes:
    return await send_request(
        "/meme/tools/render_list",
        "POST",
        "BYTES",
        json=model_dump(
            RenderMemeListParams(
                meme_properties=meme_properties,
                exclude_memes=exclude_memes,
                sort_by=sort_by,
                sort_reverse=sort_reverse,
                text_template=text_template,
                add_category_icon=add_category_icon,
            )
        ),
    )


class RenderMemeStatisticsParams(BaseModel):
    title: str
    statistics_type: Literal["meme_count", "time_count"]
    data: list[tuple[str, int]]


async def render_meme_statistics(
    title: str,
    statistics_type: Literal["meme_count", "time_count"],
    data: list[tuple[str, int]],
) -> bytes:
    return await send_request(
        "/meme/tools/render_statistics",
        "POST",
        "BYTES",
        json=model_dump(
            RenderMemeStatisticsParams(
                title=title, statistics_type=statistics_type, data=data
            )
        ),
    )


class ParserFlags(BaseModel):
    short: bool
    long: bool
    short_aliases: list[str]
    long_aliases: list[str]


class MemeBoolean(BaseModel):
    name: str
    type: Literal["boolean", "string", "integer", "float"]
    description: Optional[str]
    parser_flags: ParserFlags


class BooleanOption(MemeBoolean):
    type: Literal["boolean"]
    default: Optional[bool]


class StringOption(MemeBoolean):
    type: Literal["string"]
    default: Optional[str]
    choices: Optional[list[str]]


class IntegerOption(MemeBoolean):
    type: Literal["integer"]
    default: Optional[int]
    minimum: Optional[int]
    maximum: Optional[int]


class FloatOption(MemeBoolean):
    type: Literal["float"]
    default: Optional[float]
    minimum: Optional[float]
    maximum: Optional[float]


class MemeParams(BaseModel):
    min_images: int
    max_images: int
    min_texts: int
    max_texts: int
    default_texts: list[str]
    options: list[Union[BooleanOption, StringOption, IntegerOption, FloatOption]]


class MemeShortcut(BaseModel):
    pattern: str
    humanized: Optional[str]
    names: list[str]
    texts: list[str]
    options: dict[str, Union[bool, str, int, float]]


class MemeInfo(BaseModel):
    key: str
    params: MemeParams
    keywords: list[str]
    shortcuts: list[MemeShortcut]
    tags: set[str]
    date_created: datetime
    date_modified: datetime


async def get_meme_info(meme_key: str) -> MemeInfo:
    return type_validate_python(
        MemeInfo, await send_request(f"/memes/{meme_key}/info", "GET", "JSON")
    )


async def get_meme_infos() -> dict[str, MemeInfo]:
    resp = cast(
        dict[str, dict[str, Any]],
        await send_request("/meme/infos", "GET", "JSON"),
    )
    return {
        meme_key: type_validate_python(MemeInfo, resp[meme_key]) for meme_key in resp
    }


async def generate_meme_preview(meme_key: str) -> bytes:
    return await send_request(f"/memes/{meme_key}/preview", "GET", "BYTES")


@dataclass
class Image:
    name: str
    data: bytes


async def generate_meme(
    meme_key: str,
    images: list[Image],
    texts: list[str],
    options: dict[str, Union[bool, str, int, float]],
) -> bytes:
    image_ids: list[dict[str, str]] = []
    image_data: dict[str, str] = {}

    for image in images:
        image_id = md5(image.data).hexdigest()
        image_data[image_id] = base64.b64encode(image.data).decode()
        image_ids.append({"name": image.name, "id": image_id})

    payload = {
        "images": image_ids,
        "image_data": [
            {"id": image_id, "base64_data": image_data[image_id]}
            for image_id in image_data
        ],
        "texts": texts,
        "options": options,
    }

    return await send_request(f"/memes/{meme_key}", "POST", "BYTES", json=payload)


@dataclass
class Meme:
    key: str
    _info: MemeInfo

    @property
    def info(self) -> MemeInfo:
        return deepcopy(self._info)

    async def generate(
        self,
        images: list[Image],
        texts: list[str],
        options: dict[str, Union[bool, str, int, float]],
    ) -> bytes:
        return await generate_meme(self.key, images, texts, options)

    async def generate_preview(self) -> bytes:
        return await generate_meme_preview(self.key)


async def get_memes() -> list[Meme]:
    meme_infos = await get_meme_infos()
    return [Meme(key, info) for key, info in meme_infos.items()]
