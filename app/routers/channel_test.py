"""Zero-cost local test endpoints for Bitey channel integrations."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.outbound_channel_adapter import send_message

router = APIRouter(prefix="/channel-test", tags=["channel-test"])


class ChannelTestRequest(BaseModel):
    channel: str = Field(pattern="^(whatsapp|telegram|messenger)$")
    recipient: str
    message: str = Field(min_length=1, max_length=4000)


@router.post("/send")
def test_channel(req: ChannelTestRequest):
    """Exercise the outbound path. Safety Gate keeps default mode mock-only."""
    try:
        result = send_message(req.channel, req.recipient, req.message)
        return {"ok": True, "channel": req.channel, "result": result}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
