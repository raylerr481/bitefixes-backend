"""Bitey Response Builder V8 - AI-primary conversational responses with guarded actions."""


def language_text(language, data):
    language = (language or "es").lower()
    if language.startswith("pt"): return data.get("pt", data.get("es"))
    if language.startswith("en"): return data.get("en", data.get("es"))
    return data.get("es")


def _customer_name(customer_name):
    name = str(customer_name or "").strip()
    if not name or name.lower() in {"customer", "cliente", "customer name"}: return ""
    return name


def build_ticket_response(ticket=None, language="es", customer_name=None):
    if not ticket or not isinstance(ticket, dict): return ""
    ticket_code = ticket.get("ticket_code") or ticket.get("codigo_ticket") or ticket.get("code") or ticket.get("id")
    name = _customer_name(customer_name)
    response = language_text(language, {
        "es": f"{name}, tu solicitud fue registrada correctamente." if name else "Tu solicitud fue registrada correctamente.",
        "pt": f"{name}, sua solicitação foi registrada corretamente." if name else "Sua solicitação foi registrada corretamente.",
        "en": f"{name}, your request has been registered successfully." if name else "Your request has been registered successfully.",
    })
    if ticket_code:
        lang = (language or "es").lower()
        response += (f"\n\nCódigo do chamado: {ticket_code}" if lang.startswith("pt") else f"\n\nTicket code: {ticket_code}" if lang.startswith("en") else f"\n\nCódigo del ticket: {ticket_code}")
    return response


def normalize_response(response):
    if response is None: return ""
    if isinstance(response, str): return response
    if isinstance(response, dict): return response.get("response") or response.get("message") or response.get("text") or ""
    return str(response)


def _ai_primary_candidate(decision):
    """Use the external model as the primary cognitive responder for safe turns.

    The model may diagnose, explain and ask questions. Bitey still owns protected
    business actions. We intentionally use only the model's explicit `reply`, not
    hidden chain-of-thought or arbitrary fields.
    """
    if not isinstance(decision, dict): return ""
    # A completed ticket/quote has an authoritative business response and must not
    # be replaced by a free-form model answer.
    if decision.get("create_ticket") or decision.get("requires_quote") or decision.get("protected_action"):
        return ""
    llm = decision.get("llm") or decision.get("llm_analysis") or {}
    if isinstance(llm, dict) and llm.get("used"):
        reply = str(llm.get("reply") or "").strip()
        if reply:
            decision["response_source"] = "external_ai_primary"
            decision.setdefault("metadata", {})
            decision["metadata"].update({"ai_response_used": True, "ai_role": "primary_cognitive", "ai_provider": llm.get("provider"), "ai_model": llm.get("model")})
            return reply
    consultation = decision.get("ai_consultation") or {}
    suggestions = consultation.get("suggestions") if isinstance(consultation, dict) else []
    if isinstance(consultation, dict) and consultation.get("used") and suggestions:
        selected = (consultation.get("evaluation") or {}).get("selected") or {}
        answer = str(selected.get("answer") or (suggestions[0] or {}).get("answer") or "").strip()
        if answer:
            decision["response_source"] = "external_ai_primary"
            decision.setdefault("metadata", {})
            decision["metadata"].update({"ai_response_used": True, "ai_role": "primary_cognitive", "ai_provider": selected.get("provider") or (suggestions[0] or {}).get("provider")})
            return answer
    return ""


def _personalize(text, language, customer_name):
    name = _customer_name(customer_name)
    if not name or not text: return text
    if text.lstrip().lower().startswith(name.lower() + ","): return text
    return f"{name}, {text[0].lower() + text[1:] if len(text) > 1 else text}"


def build_final_response(decision=None, ticket=None, knowledge=None, language="es", customer_name=None):
    if not decision:
        return language_text(language, {"es": "No pude procesar tu solicitud.", "pt": "Não consegui processar sua solicitação.", "en": "I could not process your request."})
    ai_response = _ai_primary_candidate(decision)
    response = ai_response or normalize_response(decision.get("response"))
    if not response:
        response = language_text(language, {"es": "Solicitud recibida.", "pt": "Solicitação recebida.", "en": "Request received."})
    response = _personalize(response, language, customer_name)
    ticket_text = build_ticket_response(ticket, language, customer_name)
    if ticket_text: response += "\n\n" + ticket_text
    return response


def build_response(decision=None, ticket=None, knowledge=None, language="es", customer_name=None, **kwargs):
    return build_final_response(decision=decision, ticket=ticket, knowledge=knowledge, language=language, customer_name=customer_name)
