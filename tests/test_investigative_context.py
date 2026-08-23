from __future__ import annotations

from app.ai.contextual_message_resolver import resolve_contextual_message


def test_followup_keeps_active_entity_goal_and_research_signal():
    result = resolve_contextual_message(
        "evalualo",
        history=[
            {"role": "user", "content": "puedes analizar mi sitio www.bitefixes.com y darme ideas"},
            {"role": "assistant", "content": "Voy a analizar BiteFixes y su sitio para detectar oportunidades."},
        ],
        active_entity="BiteFixes",
        active_goal="diagnostico de marketing para atraer clientes",
    )
    assert result["resolved_message"]
    assert "BiteFixes" in result["resolved_message"]
    assert "diagnostico de marketing para atraer clientes" in result["resolved_message"]
    assert result["needs_clarification"] is False
    assert result["research_candidate"] is True


def test_unknown_public_entity_is_researchable_even_when_lowercase():
    result = resolve_contextual_message(
        "puedes decirme algo de viezzer supermercados",
        history=[],
        active_entity=None,
        active_goal=None,
    )
    assert result["needs_clarification"] is False
    assert result["research_candidate"] is True


def test_short_followup_preserves_subject():
    result = resolve_contextual_message(
        "y cuanto cuesta?",
        history=[
            {"role": "user", "content": "necesito actualizar el SSD de mi notebook"},
            {"role": "assistant", "content": "Podemos revisar el upgrade del SSD."},
        ],
        active_entity="upgrade de SSD",
        active_goal="resolver el problema del notebook",
    )
    assert "upgrade de SSD" in result["resolved_message"]
    assert result["needs_clarification"] is False
