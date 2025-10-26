import os
import json
import asyncio
import logging
import argparse
from typing import Optional

from fastapi import FastAPI, WebSocket, BackgroundTasks, Request
from fastapi.responses import JSONResponse, Response
from fastapi.websockets import WebSocketDisconnect
from twilio.rest import Client
import websockets
from dotenv import load_dotenv
import uvicorn
import re

load_dotenv()

# Configuration
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
PHONE_NUMBER_FROM = os.getenv('PHONE_NUMBER_FROM')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
raw_domain = os.getenv('DOMAIN', '')
DOMAIN = re.sub(r'(^\w+:|^)\/\/|\/+$', '', raw_domain) # Strip protocols and trailing slashes from DOMAIN

PORT = int(os.getenv('PORT', 6060))
OPENAI_REALTIME_MODEL = os.getenv('OPENAI_REALTIME_MODEL', 'gpt-4o-realtime-preview-2024-10-01')
SYSTEM_MESSAGE = (
    "Você é o assistente de voz oficial da plataforma (nome a definir), criada para facilitar o acesso de pessoas trans a serviços públicos. "
    "Durante a ligação, colete apenas informações essenciais para entender a situação da pessoa, avalie a elegibilidade para serviços como retificação de nome e gênero, "
    "atendimentos especializados no SUS, programas de proteção social e apoio psicossocial, e recomende orientações práticas com tutoriais passo a passo. "
    "Seja acolhedor, use linguagem inclusiva, valide sentimentos quando apropriado e ofereça caminhos seguros para quem busca apoio. "
    "Quando uma informação não estiver clara na base, explique a limitação e indique órgãos ou canais oficiais confiáveis."
)
VOICE = 'alloy'
TEMPERATURE = float(os.getenv('TEMPERATURE', 0.8))
LOG_EVENT_TYPES = [
    'error', 'response.content.done', 'rate_limits.updated', 'response.done',
    'input_audio_buffer.committed', 'input_audio_buffer.speech_stopped',
    'input_audio_buffer.speech_started', 'session.created'
]

app = FastAPI()

if not (TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and PHONE_NUMBER_FROM and OPENAI_API_KEY):
    raise ValueError('Missing Twilio and/or OpenAI environment variables. Please set them in the .env file.')

# Initialize Twilio client
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s"
)
logger = logging.getLogger("voice-assistant")

OPENAI_REALTIME_URL = f"wss://api.openai.com/v1/realtime?model={OPENAI_REALTIME_MODEL}"
OPENAI_HEADERS = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "OpenAI-Beta": "realtime=v1",
}

def twiml_response() -> str:
    stream_url = f"wss://{DOMAIN}/media-stream" if DOMAIN else "wss://localhost/media-stream"
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Response>'
        '  <Connect>'
        f'    <Stream url="{stream_url}" />'
        '  </Connect>'
        '</Response>'
    )


def build_error_response(message: str, status_code: int = 400) -> JSONResponse:
    logger.error(message)
    return JSONResponse({"error": message}, status_code=status_code)


@app.post("/outbound-call")
async def create_outbound_call(request: Request, background_tasks: BackgroundTasks):
    payload = await request.json()
    to_number: Optional[str] = payload.get("to")

    if not to_number:
        return build_error_response("Missing destination number 'to'.")

    if not DOMAIN:
        return build_error_response("DOMAIN must be set so Twilio can reach your webhook.")

    logger.info("Starting outbound call to %s", to_number)

    def start_call():
        try:
            client.calls.create(
                to=to_number,
                from_=PHONE_NUMBER_FROM,
                url=f"https://{DOMAIN}/outbound-twiml",
                status_callback=f"https://{DOMAIN}/call-status",
                status_callback_event=["initiated", "ringing", "answered", "completed"],
                machine_detection="DetectMessageEnd"
            )
        except Exception as exc:
            logger.exception("Failed to start call: %s", exc)

    background_tasks.add_task(start_call)
    return JSONResponse({"message": "Call request queued."})


@app.post("/call-status")
async def call_status(request: Request):
    form = await request.form()
    call_sid = form.get("CallSid")
    call_status = form.get("CallStatus")
    logger.info("Call %s status update: %s", call_sid, call_status)
    return JSONResponse({"status": "received"})


@app.post("/outbound-twiml")
async def outbound_twiml():
    if not DOMAIN:
        return build_error_response("DOMAIN must be set so Twilio can reach your webhook.")
    xml = twiml_response()
    logger.info("Serving TwiML to connect media stream.")
    return Response(content=xml, media_type="application/xml")


async def send_initial_conversation_item(session_ws: websockets.WebSocketClientProtocol):
    """Send initial conversation item to make AI speak first when call connects."""
    initial_conversation_item = {
        "type": "conversation.item.create",
        "item": {
            "type": "message",
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": (
                        "Cumprimente o usuário com: 'Olá! Aqui é a Lua, assistente virtual da plataforma de apoio à população trans. "
                        "Estou aqui para te ajudar com informações sobre serviços públicos, como retificação de nome e gênero, "
                        "atendimento no SUS e programas de apoio. Com quem eu tenho o prazer de falar?' "
                        "Por favor, seja caloroso e acolhedor, não se extenda por muito tempo, mas forneca as informacoes pedidas pelo usuário."
                    )
                }
            ]
        }
    }
    await session_ws.send(json.dumps(initial_conversation_item))
    logger.info("Sent initial conversation item")

    # Trigger the AI to respond
    await session_ws.send(json.dumps({"type": "response.create"}))
    logger.info("Triggered initial AI response")


async def configure_openai_session(session_ws: websockets.WebSocketClientProtocol):
    """Configure OpenAI Realtime session with system instructions and audio settings."""
    session_payload = {
        "type": "session.update",
        "session": {
            "voice": VOICE,
            "instructions": SYSTEM_MESSAGE,
            "temperature": TEMPERATURE,
            "modalities": ["text", "audio"],
            "turn_detection": {
                "type": "server_vad",
                "threshold": 0.5,
                "prefix_padding_ms": 300,
                "silence_duration_ms": 500
            },
            "input_audio_format": "g711_ulaw",
            "output_audio_format": "g711_ulaw",
            "input_audio_transcription": {
                "model": "whisper-1"
            }
        },
    }
    await session_ws.send(json.dumps(session_payload))
    logger.info("Configured OpenAI session")


async def forward_openai_events_to_twilio(
    openai_ws: websockets.WebSocketClientProtocol,
    twilio_ws: WebSocket,
    stream_sid_holder: dict,
):
    """Forward audio and events from OpenAI to Twilio."""
    try:
        async for message in openai_ws:
            try:
                event = json.loads(message)
                event_type = event.get("type")

                if event_type in LOG_EVENT_TYPES:
                    logger.info("OpenAI event: %s", event_type)

                if event_type == "response.audio.delta":
                    audio_chunk = event.get("delta")
                    if audio_chunk and stream_sid_holder.get("sid"):
                        payload = {
                            "event": "media",
                            "streamSid": stream_sid_holder["sid"],
                            "media": {"payload": audio_chunk},
                        }
                        await twilio_ws.send_text(json.dumps(payload))

                elif event_type == "response.audio_transcript.delta":
                    # Log transcript for debugging
                    transcript = event.get("delta", "")
                    if transcript:
                        logger.info("AI transcript: %s", transcript)

                elif event_type == "response.done" or event_type == "response.completed":
                    if stream_sid_holder.get("sid"):
                        await twilio_ws.send_text(json.dumps({
                            "event": "mark",
                            "streamSid": stream_sid_holder["sid"],
                            "mark": {"name": "response_done"}
                        }))

                elif event_type == "conversation.item.input_audio_transcription.completed":
                    # Log user's speech for debugging
                    transcript = event.get("transcript", "")
                    if transcript:
                        logger.info("User said: %s", transcript)

                elif event_type == "error":
                    error_details = event.get("error", {})
                    logger.error("OpenAI error: type=%s, message=%s",
                               error_details.get("type"),
                               error_details.get("message"))

            except json.JSONDecodeError as e:
                logger.error("Failed to parse OpenAI message: %s", e)
            except Exception as e:
                logger.error("Error processing OpenAI event: %s", e)

    except websockets.exceptions.ConnectionClosed as e:
        logger.info("OpenAI WebSocket closed: code=%s, reason=%s", e.code, e.reason)
        raise
    except Exception as e:
        logger.exception("Unexpected error in OpenAI event forwarding: %s", e)
        raise


async def forward_twilio_events_to_openai(
    twilio_ws: WebSocket,
    openai_ws: websockets.WebSocketClientProtocol,
    stream_sid_holder: dict,
):
    try:
        while True:
            message = await twilio_ws.receive_text()
            data = json.loads(message)
            event_type = data.get("event")

            if event_type == "start":
                stream_sid_holder["sid"] = data["start"]["streamSid"]
                logger.info("Twilio stream started: %s", stream_sid_holder["sid"])
            elif event_type == "media":
                audio_payload = data["media"]["payload"]
                await openai_ws.send(json.dumps({
                    "type": "input_audio_buffer.append",
                    "audio": audio_payload,
                }))
            elif event_type == "stop":
                logger.info("Twilio stream stopped.")
                break
    except WebSocketDisconnect:
        logger.info("Twilio websocket disconnected.")
    finally:
        try:
            await openai_ws.send(json.dumps({"type": "input_audio_buffer.commit"}))
            await openai_ws.send(json.dumps({"type": "response.create"}))
        except Exception:
            logger.debug("OpenAI session already closed or could not finalize input.")


@app.websocket("/media-stream")
async def media_stream(websocket: WebSocket):
    await websocket.accept()
    logger.info("Twilio media stream connected.")

    openai_ws = None
    try:
        logger.info("Connecting to OpenAI Realtime API...")
        openai_ws = await websockets.connect(
            OPENAI_REALTIME_URL,
            additional_headers=OPENAI_HEADERS,
            ping_interval=20,
            ping_timeout=10,
        )
        logger.info("Successfully connected to OpenAI Realtime API")
    except Exception as exc:
        logger.exception("Failed to connect to OpenAI Realtime API: %s", exc)
        try:
            await websocket.close(code=1011, reason="Failed to connect to AI service")
        except Exception:
            pass
        return

    stream_sid_holder = {"sid": None}

    async def setup_and_handle_twilio():
        """Configure OpenAI session and handle Twilio events."""
        try:
            await configure_openai_session(openai_ws)
            # Wait a moment for session to be ready
            await asyncio.sleep(0.5)
            await send_initial_conversation_item(openai_ws)
            await forward_twilio_events_to_openai(websocket, openai_ws, stream_sid_holder)
        except websockets.exceptions.ConnectionClosed as exc:
            logger.error("OpenAI WebSocket closed during setup: %s", exc)
            raise
        except Exception as exc:
            logger.exception("Error in Twilio event handling: %s", exc)
            raise

    try:
        await asyncio.gather(
            setup_and_handle_twilio(),
            forward_openai_events_to_twilio(openai_ws, websocket, stream_sid_holder),
        )
    except websockets.exceptions.ConnectionClosed as exc:
        logger.warning("WebSocket connection closed: code=%s, reason=%s", exc.code, exc.reason)
    except WebSocketDisconnect:
        logger.info("Twilio disconnected")
    except Exception as exc:
        logger.exception("Error during media streaming: %s", exc)
    finally:
        logger.info("Cleaning up connections...")
        try:
            if websocket.client_state.name != "DISCONNECTED":
                await websocket.close()
        except Exception as e:
            logger.debug("Error closing Twilio websocket: %s", e)

        try:
            if openai_ws and not openai_ws.closed:
                await openai_ws.close()
        except Exception as e:
            logger.debug("Error closing OpenAI websocket: %s", e)

        logger.info("Media stream closed.")


def main():
    parser = argparse.ArgumentParser(description="Outbound Voice AI using Twilio + OpenAI Realtime API")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind the FastAPI server.")
    parser.add_argument("--port", default=PORT, type=int, help="Port to run the server.")
    args = parser.parse_args()

    uvicorn.run("main:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
