from skyweaver.core.bus.observability.renderer import EventRenderer
from skyweaver.core.bus.publisher_manager import PublisherID, PublisherManager


def test_renderer_fallback_does_not_emit_unknown_label() -> None:
    renderer = EventRenderer(PublisherManager())

    rendered = renderer._resolve_id(PublisherID(999))

    assert "UNKNOWN" not in rendered.plain
    assert "Publisher#p:999" == rendered.plain
