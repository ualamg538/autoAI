from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field
from pydantic.json_schema import SkipJsonSchema


class TextBlock(BaseModel):
    type: Literal["text"]
    content: str


class ChartBlock(BaseModel):
    type: Literal["chart"]
    variant: Literal["bar", "radar"]
    title: str | None = None
    data: list[dict[str, Any]]
    keys: list[str] | None = None
    x_key: str | None = None
    # Metadatos de PRESENTACIÓN (no de datos): solo afectan al texto que el
    # frontend renderiza en leyenda/tooltip/ejes; nunca mutan `data`. Mantener
    # la invariante "datos de la BD" intacta: estas etiquetas no inventan cifras.
    # `unit` = unidad de la serie ("€", "CV", "l/100 km"); `x_label` = nombre
    # legible del eje X ("Marca"). Opcionales para no romper bloques existentes.
    unit: str | None = None
    x_label: str | None = None


class TableBlock(BaseModel):
    type: Literal["table"]
    title: str | None = None
    columns: list[str]
    rows: list[dict[str, Any]]


class ImageBlock(BaseModel):
    type: Literal["image"]
    car_id: int
    caption: str | None = None
    foto_url: SkipJsonSchema[str | None] = None


Block = Annotated[
    TextBlock | ChartBlock | TableBlock | ImageBlock,
    Field(discriminator="type"),
]


class ChatResponse(BaseModel):
    blocks: list[Block]
