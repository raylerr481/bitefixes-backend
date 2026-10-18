from app.ai.bitey_core_fallback import fallback_answer


def test_accented_spanish_computer_question_uses_local_knowledge_fallback():
    result = fallback_answer("¿Qué es una computadora?", language="es")

    assert result is not None
    assert result["mode"] == "basic_knowledge_fallback"
    assert result["provider"] == "bitey-core-local"
    assert "dispositivo electrónico" in result["answer"]
    assert result["business_context_applied"] is False


def test_computer_question_with_followup_words_is_answered():
    result = fallback_answer("Que es una computadora y para que sirve?", language="es")

    assert result is not None
    assert result["mode"] == "basic_knowledge_fallback"
    assert "almacena información" in result["answer"]


def test_portuguese_computer_question_uses_portuguese_answer():
    result = fallback_answer("O que é um computador?", language="pt-BR")

    assert result is not None
    assert result["mode"] == "basic_knowledge_fallback"
    assert "Um computador" in result["answer"]


def test_english_computer_question_uses_english_answer():
    result = fallback_answer("What is a computer?", language="en")

    assert result is not None
    assert result["mode"] == "basic_knowledge_fallback"
    assert "A computer" in result["answer"]
