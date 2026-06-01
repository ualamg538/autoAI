"""Tests del pipeline de /chat con OpenAI mockeado (sin red ni BD).

Punto de monkeypatch: chat.py hace `from ..services import ai_service`, así que
se parchea `src.api.chat.ai_service.chat_completion`. La hidratación de imágenes
usa cars_repository.obtener_coche_por_id vía el mismo módulo, luego se parchea
`src.api.chat.cars_repository.obtener_coche_por_id`.

Se cubren las cuatro piezas del plan: validación del envelope, reintento,
fallback e hidratación de ImageBlock; en aislamiento y end-to-end vía TestClient.
"""

import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from src.api import chat as chat_module
from src.api.chat import (
    ChatResponse,
    _envelope_fallback,
    _hidratar_image_blocks,
    _validar_con_reintento,
    _validar_envelope,
)
from src.main import app
from src.models.chat import ImageBlock, TextBlock
from src.models.normalized import Version


# --- Helpers ---------------------------------------------------------------


def _completion(content):
    """Respuesta tipo OpenAI sin tool_calls (el bucle de tools sale enseguida).

    `content` es el string que el modelo "devuelve" (JSON del envelope o basura).
    """
    message = SimpleNamespace(tool_calls=None, content=content)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def _envelope_json(blocks: list[dict]) -> str:
    return json.dumps({"blocks": blocks})


def _version(**overrides) -> Version:
    base = dict(
        id=1,
        marca="toyota",
        modelo="corolla",
        submodelo="",
        nombre="Corolla Hybrid",
        foto_url="https://example.test/foto.jpg",
        plazas=5,
        longitud=4630.0,
        anchura=1780.0,
        altura=1435.0,
        capacidad_maletero=471.0,
        carroceria="berlina",
        puertas=5,
        precio=28500.0,
        fecha_inicio=None,
        fecha_fin=None,
        combustible="hev_gasolina",
        potencia=140.0,
        aceleracion=9.2,
        velocidad_maxima=180.0,
        peso=1395.0,
        consumo_medio=4.5,
        traccion="delantera",
        transmision="automático",
        numero_marchas=None,
        capacidad_deposito=43.0,
        url="https://example.test/ficha",
    )
    base.update(overrides)
    return Version(**base)


def _mock_completions(monkeypatch, *contents):
    """Parchea chat_completion con un side_effect que recorre `contents`.

    Cada llamada a chat_completion (bucle de tools y/o envelope) consume el
    siguiente elemento. Devuelve la lista de llamadas para inspección.
    """
    calls = {"n": 0}
    seq = list(contents)

    def fake(*args, **kwargs):
        i = calls["n"]
        calls["n"] += 1
        content = seq[i] if i < len(seq) else seq[-1]
        return _completion(content)

    monkeypatch.setattr(chat_module.ai_service, "chat_completion", fake)
    return calls


# --- _validar_envelope (unidad) --------------------------------------------


def test_validar_envelope_valido():
    raw = _envelope_json([{"type": "text", "content": "ok"}])
    env = _validar_envelope(raw)
    assert isinstance(env, ChatResponse)
    assert len(env.blocks) == 1
    assert isinstance(env.blocks[0], TextBlock)


def test_validar_envelope_vacio_lanza():
    with pytest.raises(ValueError):
        _validar_envelope(None)
    with pytest.raises(ValueError):
        _validar_envelope("")


def test_validar_envelope_json_invalido_lanza():
    with pytest.raises(json.JSONDecodeError):
        _validar_envelope("{no es json")


def test_validar_envelope_schema_invalido_lanza():
    from pydantic import ValidationError

    # type desconocido -> no casa con el discriminador de Block.
    raw = _envelope_json([{"type": "desconocido", "content": "x"}])
    with pytest.raises(ValidationError):
        _validar_envelope(raw)


# --- _validar_con_reintento (unidad) ---------------------------------------


def test_reintento_tiene_exito_en_segunda(monkeypatch):
    # La llamada de reintento (_llamar_para_envelope) devuelve un envelope válido.
    valido = _envelope_json([{"type": "text", "content": "recuperado"}])
    calls = _mock_completions(monkeypatch, valido)

    messages: list[dict] = []
    # raw inicial inválido -> entra al reintento.
    env = _validar_con_reintento(messages, "{no es json", "reqid")

    assert env is not None
    assert env.blocks[0].content == "recuperado"
    # Hizo exactamente una llamada extra (el reintento).
    assert calls["n"] == 1
    # Y dejó en messages el turno inválido + la instrucción de corrección.
    assert any(m["role"] == "user" and "schema" in m["content"] for m in messages)


def test_reintento_falla_devuelve_none(monkeypatch):
    # El reintento también devuelve basura -> None (gatillo del fallback).
    calls = _mock_completions(monkeypatch, "sigue sin ser json")

    env = _validar_con_reintento([], "{invalido", "reqid")
    assert env is None
    assert calls["n"] == 1


# --- _envelope_fallback (unidad) -------------------------------------------


def test_envelope_fallback_contenido():
    env = _envelope_fallback()
    assert len(env.blocks) == 1
    assert isinstance(env.blocks[0], TextBlock)
    assert "No he podido formatear" in env.blocks[0].content


# --- _hidratar_image_blocks (unidad) ---------------------------------------


def test_hidratar_rellena_foto_url(monkeypatch):
    monkeypatch.setattr(
        chat_module.cars_repository,
        "obtener_coche_por_id",
        lambda cid: _version(id=cid, foto_url="https://example.test/real.jpg"),
    )
    envelope = ChatResponse(blocks=[ImageBlock(type="image", car_id=7)])
    out = _hidratar_image_blocks(envelope)
    assert len(out.blocks) == 1
    assert isinstance(out.blocks[0], ImageBlock)
    assert out.blocks[0].foto_url == "https://example.test/real.jpg"


def test_hidratar_descarta_si_coche_inexistente(monkeypatch):
    monkeypatch.setattr(
        chat_module.cars_repository, "obtener_coche_por_id", lambda cid: None
    )
    envelope = ChatResponse(
        blocks=[
            TextBlock(type="text", content="intro"),
            ImageBlock(type="image", car_id=999),
        ]
    )
    out = _hidratar_image_blocks(envelope)
    # El TextBlock se conserva; el ImageBlock huérfano se descarta.
    assert len(out.blocks) == 1
    assert isinstance(out.blocks[0], TextBlock)


def test_hidratar_descarta_si_sin_foto_url(monkeypatch):
    # Version exige foto_url:str; un coche "sin foto" se modela con "" (falsy).
    monkeypatch.setattr(
        chat_module.cars_repository,
        "obtener_coche_por_id",
        lambda cid: _version(id=cid, foto_url=""),
    )
    envelope = ChatResponse(blocks=[ImageBlock(type="image", car_id=3)])
    out = _hidratar_image_blocks(envelope)
    assert out.blocks == []


# --- End-to-end vía /chat --------------------------------------------------


def _post(body=None):
    client = TestClient(app)
    body = body or {"messages": [{"role": "user", "content": "hola"}]}
    return client.post("/chat", json=body)


def test_chat_envelope_valido_200(monkeypatch):
    valido = _envelope_json([{"type": "text", "content": "ok"}])
    # 1ª llamada: bucle de tools (sin tools, sale). 2ª: envelope válido.
    _mock_completions(monkeypatch, valido)
    res = _post()
    assert res.status_code == 200
    assert res.json() == {"blocks": [{"type": "text", "content": "ok"}]}


def test_chat_reintento_end_to_end(monkeypatch):
    valido = _envelope_json([{"type": "text", "content": "recuperado"}])
    # Llamada 1: bucle de tools (contenido irrelevante, sin tool_calls).
    # Llamada 2: envelope inválido -> dispara reintento.
    # Llamada 3: reintento devuelve válido.
    _mock_completions(monkeypatch, "ignorado", "{no es json", valido)
    res = _post()
    assert res.status_code == 200
    assert res.json() == {"blocks": [{"type": "text", "content": "recuperado"}]}


def test_chat_fallback_end_to_end(monkeypatch):
    # Tras el bucle, envelope y reintento siempre inválidos -> fallback.
    _mock_completions(monkeypatch, "basura", "tampoco json", "sigue mal")
    res = _post()
    assert res.status_code == 200
    body = res.json()
    assert len(body["blocks"]) == 1
    assert body["blocks"][0]["type"] == "text"
    assert "No he podido formatear" in body["blocks"][0]["content"]


def test_chat_hidratacion_imagen_end_to_end(monkeypatch):
    envelope = _envelope_json(
        [{"type": "image", "car_id": 5, "caption": "Corolla"}]
    )
    _mock_completions(monkeypatch, envelope)
    monkeypatch.setattr(
        chat_module.cars_repository,
        "obtener_coche_por_id",
        lambda cid: _version(id=cid, foto_url="https://example.test/hydrated.jpg"),
    )
    res = _post()
    assert res.status_code == 200
    blocks = res.json()["blocks"]
    assert len(blocks) == 1
    assert blocks[0]["type"] == "image"
    assert blocks[0]["foto_url"] == "https://example.test/hydrated.jpg"


def test_chat_hidratacion_descarta_imagen_huérfana(monkeypatch):
    envelope = _envelope_json(
        [
            {"type": "text", "content": "intro"},
            {"type": "image", "car_id": 999},
        ]
    )
    _mock_completions(monkeypatch, envelope)
    monkeypatch.setattr(
        chat_module.cars_repository, "obtener_coche_por_id", lambda cid: None
    )
    res = _post()
    assert res.status_code == 200
    blocks = res.json()["blocks"]
    assert len(blocks) == 1
    assert blocks[0]["type"] == "text"
