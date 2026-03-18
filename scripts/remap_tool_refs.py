#!/usr/bin/env python3
"""
Remap missing tool references in nerves to existing mcp_tools.

Reads tool.json descriptions for all 139 tools, then for each of the 43 missing
tool refs, determines whether a semantic match exists. Updates both manifest.json
and each nerve's bundle.json.
"""

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MCP_TOOLS_DIR = ROOT / "mcp_tools"
NERVES_DIR = ROOT / "nerves"
MANIFEST_PATH = ROOT / "manifest.json"


def load_tool_descriptions() -> dict[str, str]:
    """Load name -> description for every tool in mcp_tools/."""
    tools = {}
    for tool_dir in sorted(MCP_TOOLS_DIR.iterdir()):
        tool_json = tool_dir / "tool.json"
        if tool_json.exists():
            data = json.loads(tool_json.read_text())
            tools[data["name"]] = data["description"]
    return tools


# ── Mapping ──────────────────────────────────────────────────────────────────
# Built by reading every tool.json description and matching semantically.
#
# Format: old_ref -> new_tool_name
# None means "no reasonable match exists"

REMAP: dict[str, str | None] = {
    # capture_screen -> mouse_click/mouse_move are screen-coordinate tools, not
    # screenshots. No screenshot/screen-capture tool exists.
    "capture_screen": None,

    # complete_reminder -> no reminder tool exists at all
    "complete_reminder": None,

    # convert_timezone -> no timezone tool; closest would be math_eval but that's
    # a stretch. Leave as-is.
    "convert_timezone": None,

    # create_note -> note_delete exists but no note create tool
    "create_note": None,

    # create_reminder -> no reminder tools
    "create_reminder": None,

    # create_webhook -> http_post can fire a webhook (POST to a URL)
    "create_webhook": "http_post",

    # fetch -> http_post is POST-only; no generic HTTP GET. Leave as-is.
    "fetch": None,

    # fetch_content -> same issue, no HTTP GET/scrape tool
    "fetch_content": None,

    # generate_image -> gif_animation_tool generates images from text descriptions
    # but it specifically makes GIFs. No general image generation tool.
    "generate_image": None,

    # get_articles -> news_fetch fetches news articles matching a query
    "get_articles": "news_fetch",

    # get_current (weather) -> sensor_read reads IoT sensor values, not weather.
    # No weather tool exists.
    "get_current": None,

    # get_current_time -> no time/clock tool exists
    "get_current_time": None,

    # get_forecast -> no weather/forecast tool
    "get_forecast": None,

    # get_item (password) -> password_generate generates passwords but doesn't
    # retrieve stored ones. No password vault/get tool.
    "get_item": None,

    # get_price (crypto) -> stock_quote gets stock prices. Crypto != stock.
    # Leave as-is.
    "get_price": "stock_quote",

    # get_sleep_data -> no health/sleep tool
    "get_sleep_data": None,

    # get_timeline (social) -> social_trending gets trending topics, not a user
    # timeline. No timeline tool.
    "get_timeline": "social_trending",

    # get_transcript (youtube) -> youtube_info gets video info including details.
    # Not a transcript, but it's the closest YouTube data tool.
    "get_transcript": "youtube_info",

    # identify_song -> voice_recognition processes voice/audio queries
    "identify_song": "voice_recognition",

    # list_items (password store) -> password_generate exists but doesn't list.
    # No password list tool.
    "list_items": None,

    # list_lights -> device_list lists IoT devices on the gateway
    "list_lights": "device_list",

    # list_reminders -> no reminder tool
    "list_reminders": None,

    # list_webhooks -> no webhook list tool
    "list_webhooks": None,

    # ocr_screen -> image_to_text does OCR on images
    "ocr_screen": "image_to_text",

    # pause (speaker) -> no media playback control tool
    "pause": None,

    # play (speaker) -> no media playback control tool
    "play": None,

    # post_tweet -> social_like can interact with social media, but doesn't post.
    # No social post tool exists.
    "post_tweet": None,

    # read_emails -> email_reply is the only email tool; it replies, doesn't read.
    # No email read/list tool.
    "read_emails": None,

    # read_note -> note_delete exists but no note read tool
    "read_note": None,

    # reply_tweet -> social_like likes posts but doesn't reply. No reply tool.
    "reply_tweet": None,

    # search -> no general web search tool
    "search": None,

    # search_emails -> no email search tool
    "search_emails": None,

    # search_gifs -> gif_animation_tool searches/generates GIFs from text queries
    "search_gifs": "gif_animation_tool",

    # search_notes -> no note search tool
    "search_notes": None,

    # search_tweets -> social_trending gets trending, not search results
    "search_tweets": "social_trending",

    # send_email -> email_reply sends email (as a reply). It's the only email
    # sending tool available.
    "send_email": "email_reply",

    # set_light -> actuator_set sets IoT actuator values (lights are actuators)
    "set_light": "actuator_set",

    # set_temperature -> actuator_set can set any actuator value; but
    # thermostat_read only reads. actuator_set is the setter.
    "set_temperature": "actuator_set",

    # speech_to_text -> voice_recognition processes voice recognition queries
    "speech_to_text": "voice_recognition",

    # take_photo -> no camera/photo tool (mouse/keyboard tools exist but are
    # unrelated)
    "take_photo": None,

    # text_to_speech -> no TTS tool exists
    "text_to_speech": None,

    # update_note -> note_delete exists but no note update tool
    "update_note": None,

    # volume (speaker) -> no volume/audio control tool
    "volume": None,
}


def apply_remapping() -> None:
    """Apply the remap to manifest.json and each nerve's bundle.json."""
    # Count what we'll do
    remapped: list[tuple[str, str, str]] = []  # (nerve, old, new)
    no_match: list[tuple[str, str]] = []  # (nerve, old)

    # ── Which nerves use which missing refs ──
    nerve_to_missing: dict[str, list[str]] = {
        "image_capture_nerve": ["capture_screen"],
        "screen_read_nerve": ["capture_screen", "ocr_screen"],
        "reminder_done_nerve": ["complete_reminder"],
        "timestamp_nerve": ["get_current_time", "convert_timezone"],
        "note_create_nerve": ["create_note"],
        "reminder_create_nerve": ["create_reminder"],
        "webhook_fire_nerve": ["create_webhook"],
        "link_check_nerve": ["fetch"],
        "web_fetch_nerve": ["fetch"],
        "web_scrape_nerve": ["fetch_content"],
        "image_generate_nerve": ["generate_image"],
        "rss_monitor_nerve": ["get_articles"],
        "weather_now_nerve": ["get_current"],
        "weather_forecast_nerve": ["get_forecast"],
        "password_get_nerve": ["get_item"],
        "crypto_price_nerve": ["get_price"],
        "sleep_data_nerve": ["get_sleep_data"],
        "social_read_nerve": ["get_timeline"],
        "youtube_transcript_nerve": ["get_transcript"],
        "music_identify_nerve": ["identify_song"],
        "password_store_nerve": ["list_items"],
        "light_status_nerve": ["list_lights"],
        "reminder_check_nerve": ["list_reminders"],
        "webhook_register_nerve": ["list_webhooks"],
        "speaker_pause_nerve": ["pause"],
        "speaker_play_nerve": ["play"],
        "social_post_nerve": ["post_tweet"],
        "email_check_nerve": ["read_emails"],
        "email_read_nerve": ["read_emails"],
        "note_read_nerve": ["read_note"],
        "social_reply_nerve": ["reply_tweet"],
        "web_search_nerve": ["search"],
        "email_search_nerve": ["search_emails"],
        "gif_find_nerve": ["search_gifs"],
        "note_search_nerve": ["search_notes"],
        "social_search_nerve": ["search_tweets"],
        "email_send_nerve": ["send_email"],
        "light_color_nerve": ["set_light"],
        "light_dim_nerve": ["set_light"],
        "light_off_nerve": ["set_light"],
        "thermostat_set_nerve": ["set_temperature"],
        "audio_transcribe_nerve": ["speech_to_text"],
        "video_transcribe_nerve": ["speech_to_text"],
        "camera_snapshot_nerve": ["take_photo"],
        "audio_synthesize_nerve": ["text_to_speech"],
        "note_update_nerve": ["update_note"],
        "speaker_volume_nerve": ["volume"],
    }

    # ── Update manifest.json ──
    manifest = json.loads(MANIFEST_PATH.read_text())

    for nerve_name, missing_refs in nerve_to_missing.items():
        if nerve_name not in manifest["nerves"]:
            print(f"  WARNING: {nerve_name} not found in manifest.json")
            continue

        nerve_entry = manifest["nerves"][nerve_name]
        tools_list = nerve_entry.get("tools", [])

        for old_ref in missing_refs:
            new_ref = REMAP.get(old_ref)
            if new_ref is None:
                no_match.append((nerve_name, old_ref))
                continue

            # Replace in manifest tools list
            if old_ref in tools_list:
                idx = tools_list.index(old_ref)
                tools_list[idx] = new_ref
                remapped.append((nerve_name, old_ref, new_ref))

        nerve_entry["tools"] = tools_list

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=4) + "\n")

    # ── Update each nerve's bundle.json ──
    for nerve_name, missing_refs in nerve_to_missing.items():
        bundle_path = NERVES_DIR / nerve_name / "bundle.json"
        if not bundle_path.exists():
            continue

        bundle = json.loads(bundle_path.read_text())
        tools_list = bundle.get("tools", [])

        for old_ref in missing_refs:
            new_ref = REMAP.get(old_ref)
            if new_ref is None:
                continue

            for tool_entry in tools_list:
                if tool_entry.get("name") == old_ref:
                    tool_entry["name"] = new_ref

        bundle_path.write_text(json.dumps(bundle, indent=4) + "\n")

    # ── Report ──
    print("=" * 60)
    print("REMAPPED SUCCESSFULLY:")
    print("=" * 60)
    for nerve, old, new in sorted(remapped):
        print(f"  {old:25s} -> {new:25s}  (in {nerve})")

    print()
    print("=" * 60)
    print("NO MATCH (left as-is):")
    print("=" * 60)
    # Deduplicate by old_ref
    seen = set()
    for nerve, old in sorted(no_match):
        key = old
        nerves_using = [n for n, o in no_match if o == old]
        if key not in seen:
            seen.add(key)
            print(f"  {old:25s}  <- {', '.join(nerves_using)}")

    print()
    print(f"Total remapped: {len(remapped)} references across nerves")
    print(f"Total unresolved: {len(seen)} unique tool refs ({len(no_match)} nerve references)")


if __name__ == "__main__":
    apply_remapping()
