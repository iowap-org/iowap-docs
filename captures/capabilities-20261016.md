# capabilities — real capture

captured_at: 2026-10-16T15:45:24Z
command: `node-cli capabilities server`
anonymized: IPs RFC 5737, tokens redacted, own domains example.com

```
Server capabilities (55 total):

  ✅ flow.catalog         v1.0.0     [flow-runner (MWCJKYHE)]
     Flow catalog/history management (T-231b): list_flows, list_history, show_history, save_flow, define_flow — payload['mode'] selects the operation.
     Input: {
      "fields": {
            "mode": {
                  "name": "mode",
                  "type": "string",
                  "required": true,
                  "description": "One of: list_flows | list_history | show_history | save_flow | define_flow."
            },
            "history_id": {
                  "name": "history_id",
                  "type": "string",
                  "required": false,
                  "description": "History record id (show_history/save_flow)."
            },
            "limit": {
                  "name": "limit",
                  "type": "integer",
                  "required": false,
                  "description": "Max records for list_history (default 20, cap 100)."
            },
            "name": {
                  "name": "name",
                  "type": "string",
                  "required": false,
                  "description": "Catalog name for define_flow."
            },
            "plan": {
                  "name": "plan",
                  "type": "object",
                  "required": false,
                  "description": "Plan JSON for define_flow (version/name/summary/tasks)."
            }
      }
}

  ✅ flow.run             v1.0.0     [flow-runner (MWCJKYHE)]
     Accepts a planned flow and executes it as plain tasks. Input: original_request (verbatim task); optional mode=run_flow (prebuilt catalog flow, skips agent.ai). Management (history/catalog) lives in flow.catalog.
     Input: {
      "fields": {
            "original_request": {
                  "name": "original_request",
                  "type": "string",
                  "required": true,
                  "description": "The original task verbatim. Example: 'Create 3 product images and zip them'."
            },
            "mode": {
                  "name": "mode",
                  "type": "string",
                  "required": false,
                  "description": "Optional execution mode: run (default, classic plan run via agent.ai) or run_flow (prebuilt catalog flow via 'flow' + 'input')."
            },
            "flow": {
                  "name": "flow",
                  "type": "string",
                  "required": false,
                  "description": "Catalog flow name (run_flow only)."
            },
            "input": {
                  "name": "input",
                  "type": "object",
                  "required": false,
                  "description": "Input parameters for the catalog flow (run_flow only, ${input.x} templates)."
            },
            "options": {
                  "name": "options",
                  "type": "object",
                  "required": false,
                  "description": "Optional: {max_flow_seconds: 14400}."
            }
      }
}

  ✅ ha.climate.set_temperature.native v1.0.0     [ha-app-node (T4AYHMN4)]
     Set the target temperature of a climate/thermostat entity.
     Input: {
      "fields": {
            "entity_id": {
                  "name": "entity_id",
                  "type": "string",
                  "required": true,
                  "description": "Target HA entity_id '<domain>.<name>'; must match the capability's domain."
            },
            "temperature": {
                  "name": "temperature",
                  "type": "number",
                  "ge": 5,
                  "le": 35,
                  "description": "Target temperature in degrees Celsius (climate)."
            }
      }
}

  ✅ ha.fan.toggle.native v1.0.0     [ha-app-node (T4AYHMN4)]
     Toggle a fan entity.
     Input: {
      "fields": {
            "entity_id": {
                  "name": "entity_id",
                  "type": "string",
                  "required": true,
                  "description": "Target HA entity_id '<domain>.<name>'; must match the capability's domain."
            }
      }
}

  ✅ ha.humidifier.toggle.native v1.0.0     [ha-app-node (T4AYHMN4)]
     Toggle a humidifier/dehumidifier entity.
     Input: {
      "fields": {
            "entity_id": {
                  "name": "entity_id",
                  "type": "string",
                  "required": true,
                  "description": "Target HA entity_id '<domain>.<name>'; must match the capability's domain."
            }
      }
}

  ✅ ha.light.off.native  v1.0.0     [ha-app-node (T4AYHMN4)]
     Turn a light entity OFF, optionally with a transition ramp.
     Input: {
      "fields": {
            "entity_id": {
                  "name": "entity_id",
                  "type": "string",
                  "required": true,
                  "description": "Target HA entity_id '<domain>.<name>'; must match the capability's domain."
            },
            "transition": {
                  "name": "transition",
                  "type": "number",
                  "ge": 0,
                  "le": 60,
                  "description": "Seconds to ramp to the new state."
            }
      }
}

  ✅ ha.light.on.native   v1.0.0     [ha-app-node (T4AYHMN4)]
     Turn a light entity ON, optionally with brightness, color temperature and transition ramp.
     Input: {
      "fields": {
            "entity_id": {
                  "name": "entity_id",
                  "type": "string",
                  "required": true,
                  "description": "Target HA entity_id '<domain>.<name>'; must match the capability's domain."
            },
            "brightness_pct": {
                  "name": "brightness_pct",
                  "type": "number",
                  "ge": 0,
                  "le": 100,
                  "description": "Brightness in percent (0-100)."
            },
            "color_temp_kelvin": {
                  "name": "color_temp_kelvin",
                  "type": "number",
                  "ge": 1500,
                  "le": 6500,
                  "description": "Color temperature in Kelvin (only for mired-capable lights)."
            },
            "transition": {
                  "name": "transition",
                  "type": "number",
                  "ge": 0,
                  "le": 60,
                  "description": "Seconds to ramp to the new state."
            }
      }
}

  ✅ ha.light.toggle.native v1.0.0     [ha-app-node (T4AYHMN4)]
     Toggle a light entity between on and off.
     Input: {
      "fields": {
            "entity_id": {
                  "name": "entity_id",
                  "type": "string",
                  "required": true,
                  "description": "Target HA entity_id '<domain>.<name>'; must match the capability's domain."
            }
      }
}

  ✅ ha.media.play_pause.native v1.0.0     [ha-app-node (T4AYHMN4)]
     Toggle play/pause on a media player entity.
     Input: {
      "fields": {
            "entity_id": {
                  "name": "entity_id",
                  "type": "string",
                  "required": true,
                  "description": "Target HA entity_id '<domain>.<name>'; must match the capability's domain."
            }
      }
}

  ✅ ha.scene.activate.native v1.0.0     [ha-app-node (T4AYHMN4)]
     Activate a saved Home Assistant scene.
     Input: {
      "fields": {
            "entity_id": {
                  "name": "entity_id",
                  "type": "string",
                  "required": true,
                  "description": "Target HA entity_id '<domain>.<name>'; must match the capability's domain."
            }
      }
}

  ✅ ha.state.get.native  v1.0.0     [ha-app-node (T4AYHMN4)]
     Read the current state and attributes of one entity (read-only, all domains).
     Input: {
      "fields": {
            "entity_id": {
                  "name": "entity_id",
                  "type": "string",
                  "required": true,
                  "description": "Target HA entity_id '<domain>.<name>'; must match the capability's domain."
            }
      }
}

  ✅ ha.switch.toggle.native v1.0.0     [ha-app-node (T4AYHMN4)]
     Toggle a switch entity (plugs, relays).
     Input: {
      "fields": {
            "entity_id": {
                  "name": "entity_id",
                  "type": "string",
                  "required": true,
                  "description": "Target HA entity_id '<domain>.<name>'; must match the capability's domain."
            }
      }
}

  ✅ ha.vacuum.return_to_base.native v1.0.0     [ha-app-node (T4AYHMN4)]
     Send the vacuum back to its dock.
     Input: {
      "fields": {
            "entity_id": {
                  "name": "entity_id",
                  "type": "string",
                  "required": true,
                  "description": "Target HA entity_id '<domain>.<name>'; must match the capability's domain."
            }
      }
}

  ✅ ha.vacuum.start.native v1.0.0     [ha-app-node (T4AYHMN4)]
     Start the vacuum's cleaning run.
     Input: {
      "fields": {
            "entity_id": {
                  "name": "entity_id",
                  "type": "string",
                  "required": true,
                  "description": "Target HA entity_id '<domain>.<name>'; must match the capability's domain."
            }
      }
}

  ✅ backup.create        v1.0.0     [storage (BPV83C9X)]
     Declare an upload as a versioned backup (full or incremental).
     Input: {
      "fields": {
            "mode": {
                  "name": "mode",
                  "type": "string",
                  "required": false,
                  "description": "inline (default) | bridge. 'bridge' opens a temp upload route so the caller streams the large backup straight to backups/<id>/data.bin (no artifact staging)."
            },
            "source": {
                  "name": "source",
                  "type": "string",
                  "required": true,
                  "description": "Logical source name, e.g. 'projects' or 'photos'."
            },
            "type": {
                  "name": "type",
                  "type": "string",
                  "required": true,
                  "description": "full or incremental."
            },
            "base_backup_id": {
                  "name": "base_backup_id",
                  "type": "string",
                  "required": false,
                  "description": "For incremental: the base backup it builds on."
            },
            "data_base64": {
                  "name": "data_base64",
                  "type": "string",
                  "required": false,
                  "description": "Backup payload as base64 (small backups)."
            },
            "artifact_id": {
                  "name": "artifact_id",
                  "type": "string",
                  "required": false,
                  "description": "Relay artifact ID to stream down (large backups)."
            }
      }
}

  ✅ backup.delete        v1.0.0     [storage (BPV83C9X)]
     Mark a backup deleted (manifest kept for audit, data removed).
     Input: {
      "fields": {
            "backup_id": {
                  "name": "backup_id",
                  "type": "string",
                  "required": true,
                  "description": "The backup id (bk_...)."
            }
      }
}

  ✅ backup.info          v1.0.0     [storage (BPV83C9X)]
     Return the manifest of a single backup.
     Input: {
      "fields": {
            "backup_id": {
                  "name": "backup_id",
                  "type": "string",
                  "required": true,
                  "description": "The backup id (bk_...)."
            }
      }
}

  ✅ backup.list          v1.0.0     [storage (BPV83C9X)]
     List backups, optionally filtered by source/type.
     Input: {
      "fields": {
            "source": {
                  "name": "source",
                  "type": "string",
                  "required": false,
                  "description": "Filter by source name."
            },
            "type": {
                  "name": "type",
                  "type": "string",
                  "required": false,
                  "description": "Filter by type (full/incremental)."
            }
      }
}

  ✅ backup.restore       v1.0.0     [storage (BPV83C9X)]
     Return a backup's data — inline base64 for small backups, or a temp bridge download_url for large ones (>10MB).
     Input: {
      "fields": {
            "backup_id": {
                  "name": "backup_id",
                  "type": "string",
                  "required": true,
                  "description": "The backup id (bk_...)."
            }
      }
}

  ✅ backup.retention     v1.0.0     [storage (BPV83C9X)]
     Apply a retention policy to a source (keep_last / max_age_days / GFS).
     Input: {
      "fields": {
            "source": {
                  "name": "source",
                  "type": "string",
                  "required": true,
                  "description": "Source name to apply the policy to."
            },
            "policy": {
                  "name": "policy",
                  "type": "object",
                  "required": true,
                  "description": "Retention policy: {keep_last: N}, {max_age_days: N}, or GFS {keep_daily, keep_weekly, keep_monthly}."
            }
      }
}

  ✅ storage.archive      v1.0.0     [storage (BPV83C9X)]
     Pack a directory into a .tar.gz (T-135). Reports progress via task notes (T-160).
     Input: {
      "fields": {
            "path": {
                  "name": "path",
                  "type": "string",
                  "required": true,
                  "description": "Source directory to pack, relative to the storage root."
            },
            "target": {
                  "name": "target",
                  "type": "string",
                  "required": true,
                  "description": "Destination .tar.gz path, relative to the storage root."
            }
      }
}

  ✅ storage.delete       v1.0.0     [storage (BPV83C9X)]
     Delete a file or directory (recursive).
     Input: {
      "fields": {
            "path": {
                  "name": "path",
                  "type": "string",
                  "required": true,
                  "description": "Path to delete, relative to the storage root."
            }
      }
}

  ✅ storage.download_channel v1.0.0     [storage (BPV83C9X)]
     Open a temp bridge route so a caller can stream a large file FROM the NAS through the relay.
     Input: {
      "fields": {
            "channel_id": {
                  "name": "channel_id",
                  "type": "string",
                  "required": false,
                  "description": "Optional channel id; minted when absent."
            }
      }
}

  ✅ storage.extract      v1.0.0     [storage (BPV83C9X)]
     Unpack a stored .tar.gz into a directory (T-135).
     Input: {
      "fields": {
            "path": {
                  "name": "path",
                  "type": "string",
                  "required": true,
                  "description": "Path of the .tar.gz to unpack, relative to the storage root."
            }
      }
}

  ✅ storage.fetch        v1.0.0     [storage (BPV83C9X)]
     Read a file back from the NAS as base64 (small files).
     Input: {
      "fields": {
            "path": {
                  "name": "path",
                  "type": "string",
                  "required": true,
                  "description": "Path of the file to read, relative to the storage root."
            }
      }
}

  ✅ storage.list         v1.0.0     [storage (BPV83C9X)]
     List files under a prefix.
     Input: {
      "fields": {
            "prefix": {
                  "name": "prefix",
                  "type": "string",
                  "required": false,
                  "description": "Prefix to list under (empty = whole storage root)."
            }
      }
}

  ✅ storage.move         v1.0.0     [storage (BPV83C9X)]
     Rename/move a file or directory.
     Input: {
      "fields": {
            "from": {
                  "name": "from",
                  "type": "string",
                  "required": true,
                  "description": "Source path, relative to the storage root."
            },
            "to": {
                  "name": "to",
                  "type": "string",
                  "required": true,
                  "description": "Destination path, relative to the storage root."
            }
      }
}

  ✅ storage.quota        v1.0.0     [storage (BPV83C9X)]
     Report disk usage + threshold (RELAY_STORAGE_QUOTA_THRESHOLD, default 0.9).
     Input: {
      "fields": {}
}

  ✅ storage.stat         v1.0.0     [storage (BPV83C9X)]
     Stat a single path (size, mtime, is_dir).
     Input: {
      "fields": {
            "path": {
                  "name": "path",
                  "type": "string",
                  "required": true,
                  "description": "Path to stat, relative to the storage root."
            }
      }
}

  ✅ storage.store        v1.0.0     [storage (BPV83C9X)]
     Write a file to the NAS. Supports inline base64 data or streaming a relay artifact. Optionally unpack a .tar.gz (action: extract).
     Input: {
      "fields": {
            "path": {
                  "name": "path",
                  "type": "string",
                  "required": true,
                  "description": "Target path relative to the storage root, e.g. 'projects/2026/file.png'."
            },
            "data_base64": {
                  "name": "data_base64",
                  "type": "string",
                  "required": false,
                  "description": "File content as base64 (small files). Mutually exclusive with artifact_id."
            },
            "artifact_id": {
                  "name": "artifact_id",
                  "type": "string",
                  "required": false,
                  "description": "Relay artifact ID to stream down (large files). Mutually exclusive with data_base64."
            },
            "action": {
                  "name": "action",
                  "type": "string",
                  "required": false,
                  "description": "store_as_is (default) or extract (unpack a .tar.gz into a directory)."
            }
      }
}

  ✅ storage.upload_channel v1.0.0     [storage (BPV83C9X)]
     Open a temp bridge route so a caller can stream a large file TO the NAS through the relay.
     Input: {
      "fields": {
            "channel_id": {
                  "name": "channel_id",
                  "type": "string",
                  "required": false,
                  "description": "Optional channel id; minted when absent."
            }
      }
}

  ✅ ct.update            v1.1.0     [bot-desktop (XMYTFTA7)]
     Fährt Updates auf diesem CT (bot-desktop): sudo apt update + upgrade + autoremove. Rückgabe: ok, rc, upgraded_packages, errors, reboot_required.
     Input: {
      "fields": {
            "reboot": {
                  "name": "reboot",
                  "type": "boolean",
                  "required": false,
                  "description": "Reserviert \u2014 wird noch nicht unterst\u00fctzt."
            }
      }
}

  ✅ desktop.ctl          v1.1.0     [bot-desktop (XMYTFTA7)]
     Generischer cua-driver Dispatcher auf dem Bot-Desktop (Xfce :99, 1920x1080). Payload: {"tool": "<cua-tool>", "args": {...}}. Erlaubt: Maus/Tastatur (click, type_text, press_key, hotkey, drag, scroll...), Apps/Fenster (launch_app, list_windows, get_window_state...), Screen (get_desktop_state liefert PNG als data_base64, get_screen_size, zoom), Clipboard, Recording/Session. Mit get_desktop_state -> get_window_state -> click(element_index) bekommt man vollständige Desktop-Automation.
     Input: {
      "fields": {
            "tool": {
                  "name": "tool",
                  "type": "string",
                  "required": true,
                  "description": "cua-driver Tool-Name (z.B. click, type_text, launch_app, get_desktop_state)."
            },
            "args": {
                  "name": "args",
                  "type": "object",
                  "required": false,
                  "description": "Argumente des Tools als Objekt, z.B. {\"pid\": 1234, \"element_index\": 3} oder {\"text\": \"hallo\"}."
            }
      }
}

  ✅ desktop.screenshot   v1.1.0     [bot-desktop (XMYTFTA7)]
     Screenshot des XFCE-Desktops (:99, 1920x1080) via cua-driver. Rückgabe: PNG als base64 (data_base64, mime_type image/png).
     Input: {
      "fields": {}
}

  ✅ mc.console.log       v1.0.0     [mc-node (AMKJA9AE)]
     Fetch the last log lines (JSON-decoded) of a Minecraft container. Example: 'target: lobby, lines: 50' for the latest lobby logs including player chat and joins.
     Input: {
      "fields": {
            "target": {
                  "name": "target",
                  "type": "string",
                  "required": false,
                  "description": "Server name: 'lobby' (default), 'survival' or 'creative'. Example: 'lobby'."
            },
            "lines": {
                  "name": "lines",
                  "type": "number",
                  "required": false,
                  "description": "How many tail lines to fetch, default 40, max 400. Example: 100."
            }
      }
}

  ✅ mc.list.players      v1.0.0     [mc-node (AMKJA9AE)]
     List currently online players on all three servers (lobby, survival, creative) with counts. Example: '{}' — no parameters needed.
     Input: {
      "fields": {}
}

  ✅ mc.rcon.command      v1.0.0     [mc-node (AMKJA9AE)]
     Execute a Minecraft RCON command on lobby, survival or creative. Example: 'command: list', 'command: say Hallo vom Relay', 'command: fill 0 6 0 5 6 5 minecraft:stone', 'command: gamerule doDaylightCycle false', 'target: survival'.
     Input: {
      "fields": {
            "command": {
                  "name": "command",
                  "type": "string",
                  "required": true,
                  "description": "The Minecraft command without leading slash. Example: 'list' or 'say Hi' or 'fill 0 6 0 5 6 5 minecraft:stone'."
            },
            "target": {
                  "name": "target",
                  "type": "string",
                  "required": false,
                  "description": "Server name: 'lobby' (default), 'survival' or 'creative'. Example: 'survival'."
            }
      }
}

  ✅ firecrawl.scrape     v1.0.0     [webstack (4W8EATRW)]
     Volltext-Scrape einer URL via lokalem Firecrawl (192.0.2.1:3002, JS-Rendering). Beispiel: {"url":"https://example.com","max_chars":"4000"}
     Input: {
      "fields": {
            "url": {
                  "name": "url",
                  "type": "string",
                  "required": true,
                  "description": "Zu scrapende URL. Beispiel: \"https://www.heise.de/newsticker/heise-aktuell-987654.html\"."
            },
            "max_chars": {
                  "name": "max_chars",
                  "type": "string",
                  "required": false,
                  "description": "Markdown-Kappung als Zahl, 100-50000. Beispiel: \"4000\"."
            }
      }
}

  ✅ searxng.search       v1.0.0     [webstack (4W8EATRW)]
     Metasuche ueber lokales SearXNG (192.0.2.1:8888). Beispiel: {"query":"leipzig wetter","category":"news","max_results":8}
     Input: {
      "fields": {
            "query": {
                  "name": "query",
                  "type": "string",
                  "required": true,
                  "description": "Suchanfrage. Beispiel: \"leipzig wetter\" oder \"iowap release notes\"."
            },
            "category": {
                  "name": "category",
                  "type": "string",
                  "required": false,
                  "description": "SearXNG-Kategorie. Werte: general, news, images, science, it, files. Default: general."
            },
            "max_results": {
                  "name": "max_results",
                  "type": "string",
                  "required": false,
                  "description": "Anzahl Ergebnisse als Zahl, 1-25. Beispiel: \"5\"."
            }
      }
}

  ✅ agent.ai             v1.2.0     [NovaForge (RYBFNMET), felix-cyberfox (E4W3CBWQ)]
     Full Hermes agent with tools, memory and skills — via API Server (Gateway). Can read/write files, run shell commands, search the web, generate images, write code. Runs fully autonomously - no user interaction possible (no clarify, no follow-up questions); the task must be self-contained, missing info is resolved with documented assumptions or a clear error report.
     Input: {
      "fields": {
            "task": {
                  "name": "task",
                  "type": "string",
                  "required": true,
                  "description": "The task for the agent - write it fully self-contained (paths, constraints, expected output); the agent runs autonomously with NO follow-up questions and cannot ask the user anything. Examples: 'Read /home/user/config.json and summarize it', 'Search the web for latest AI news and save to /tmp/news.md', 'Create a Python script that sorts a CSV by date'"
            },
            "question": {
                  "name": "question",
                  "type": "string",
                  "required": false,
                  "description": "Alternative to task \u2014 a direct question. Examples: 'How much free disk space?', 'What processes are running?'"
            }
      }
}

  ✅ chat.ai              v1.0.0     [NovaForge (RYBFNMET), felix-cyberfox (E4W3CBWQ)]
     Lightweight chat — answers questions via hermes -z (no tools, no session). Good for simple questions, fact checks, translations.
     Input: {
      "fields": {
            "question": {
                  "name": "question",
                  "type": "string",
                  "required": true,
                  "description": "The question or prompt. Examples: 'What is the capital of France?', 'Translate Hello into German', 'Who discovered relativity?'"
            },
            "prompt": {
                  "name": "prompt",
                  "type": "string",
                  "required": false,
                  "description": "Alternative to question. Examples: 'Tell me a joke', 'Summarize the moon landing'"
            }
      }
}

  ✅ classify.ai          v1.1.0     [NovaForge (RYBFNMET)]
     Klassifikation/Routing via Ollama System-One Decision-Endpoint (POST /v1/systemone, TypeSafe-Jev-kompatibel). Das Modell generiert nicht, es scort: Du schickst einen state (zu bewertenden Text) plus benannte questions mit vorgegebenen Optionen und bekommst in EINEM Request typisierte Antworten mit Wahrscheinlichkeiten pro Option — kein Reasoning, keine Prosa, output_tokens=1. Antworttypen: choice ({choice, probabilities, confidence}), noul (Wahrscheinlichkeit fuer true), score ({score, legend, probabilities}). Anwendungsfaelle: Ticket-Triage/Routing, Labels, Moderation, Ja/Nein-Entscheidungen, Skalen-Bewertungen. Deutsch funktioniert direkt (kein Sprach-Workaround noetig). Wichtig: bei Off-Topic-Input IMMER eine 'nichts davon'-Option in den criteria aufnehmen, sonst waehlt das Modell das am wenigsten falsche Label. choice ist deutlich zuverlaessiger als score — besser choice mit klaren Stufenbeschreibungen statt score nutzen (Benchmark: choice ~82 %, score ~54 %). confidence ist nur der Konzentrationsgrad der Verteilung, nicht die Wahrscheinlichkeit 'korrekt'. Nicht geeignet fuer: Erklaerungen, Zusammenfassungen, freie Generierung, lange Dokumente.
     Input: {
      "fields": {
            "state": {
                  "name": "state",
                  "type": "string",
                  "required": true,
                  "description": "Der zu bewertende Text. Beispiele: 'Kunde: Ich habe heute dreimal abgebucht bekommen und eine E-Mail mit doppeltem Betrag erhalten, bitte um Rueckzahlung, Ticket 40281' (kategorie=billing, p>0.95), 'Seit dem gestrigen Update stuerzt die App sofort beim Start ab' (kategorie=bug, p>0.97), 'Ich komme nicht mehr in mein Konto, Passwort vergessen' (kategorie=account). Deutsch funktioniert direkt. Bei moeglichem Off-Topic-Input eine 'nichts davon'-Option in den criteria vorsehen, sonst wird das am wenigsten falsche Label gewaehlt."
            },
            "questions": {
                  "name": "questions",
                  "type": "object",
                  "required": true,
                  "description": "Benannte Fragen, die in EINEM Request mit dem kompletten state beantwortet werden. Drei Typen: choice (Multiple Choice mit Optionen in criteria), noul (ja/nein), score (Skala, criteria aufsteigend). Komplettes Beispiel fuer ein Support-Triage: {\"kategorie\":{\"type\":\"choice\",\"instructions\":\"Zu welcher Kategorie gehoert das Ticket?\",\"criteria\":{\"billing\":\"Rechnung, Zahlung, R\u00fcckerstattung, doppelte Abbuchung\",\"bug\":\"Technischer Fehler, Absturz, Funktion geht nicht\",\"account\":\"Login, Passwort, Konto\",\"nichts_davon\":\"Keines der Themen\"}},\"rueckerstattung\":{\"type\":\"noul\",\"instructions\":\"True, wenn der Kunde sein Geld zurueck haben will.\"},\"dringlichkeit\":{\"type\":\"score\",\"instructions\":\"Wie dringend ist die Anfrage?\",\"criteria\":[\"niedrig\",\"mittel\",\"hoch\",\"kritisch\"]}}. Regeln: Bei choice MUSS criteria ein Objekt sein (Option -> Beschreibung oder null), bei score ein aufsteigendes Array; instructions ist bei allen drei Typen Pflicht (Objekt statt String beim choice-criteria gibt HTTP 400). Das komplette Frageset + state muessen ins Kontextfenster passen: Tev1 ~2000 Token, Nimble 8192, Clef:27b-cloud 65536 \u2014 zu grosser Input scheitert hart (kein Kuerzen)."
            },
            "model": {
                  "name": "model",
                  "type": "string",
                  "required": false,
                  "description": "Allowed values: tev1:0.8b / nimble:9b-nvfp4 / clef:27b-cloud. Default: tev1:0.8b. Bewertungsmodell (Scoring, KEIN Chat-Modell). tev1:0.8b = Standard: 1,5 GB, warm ~0,15-0,3 s pro Entscheidung, Kontext ~2000 Token. nimble:9b-nvfp4 = hoechste Genauigkeit: 6,9 GB MLX (nvfp4), 100% GPU, Kontext 8192, warm ~1,2 s pro Request (kalt ~11 s inkl. Laden), RAM-nomadisch unproblematisch (32% frei waehrend geladen). Repariert 2026-10-14 nach Ollama-0.40-Format-Migration \u2014 das alte Custom-GGUF 'nimble:latest' bleibt defekt, NICHT mehr benutzen. clef:27b-cloud = Cloud-Decision-Model (Cloudflare Clef, 27B, Qwen3.8-Finetune), 64K Kontext (65536 Token), multimodal (Text+Images), KEIN lokaler RAM-Verbrauch (kein GGUF/MLX-Laden \u2014 die RAM-Kollision mit mflux entfaellt fuer dieses Modell), Latenz netzabhaengig, typisch wenige Sekunden; Alias: clef:cloud (beide Tags rufen den Endpoint original auf). clef-flash:9b-q8_0 ist seit 2026-10-16 aus dem Enum (RAM-eng, 10-GB-GGUF) \u2014 die lokalen Gewichte bleiben am Ollama installiert, werden aber nicht mehr angeboten. Cloud-Models brauchen Ollama >= 0.35.1 und laufen durch denselben Endpoint (live verifiziert 2026-10-15 nach der 0.40-Migration). Die Capability laeuft mit max_parallel 1: dieser Hinweis bleibt \u2014 er schuetzt tev1/nimble gegen gleichzeitige GPU-Lasten (16 GB RAM, mflux Bild/Video, strikt nacheinander); clef:27b-cloud selbst verbraucht keinen lokalen RAM."
            }
      }
}

  ✅ file.ai              v1.0.0     [NovaForge (RYBFNMET)]
     File operations (read, write) via Hermes. Access to the entire filesystem. Runs autonomously - no user interaction, no follow-up questions.
     Input: {
      "fields": {
            "path": {
                  "name": "path",
                  "type": "string",
                  "required": true,
                  "description": "Absolute file path. Examples: '/home/user/config.json', '/tmp/report.txt', '/var/log/system.log'"
            },
            "content": {
                  "name": "content",
                  "type": "string",
                  "required": false,
                  "description": "Content to write (write operations only). Examples: '{\"name\": \"Test\", \"version\": 1}', 'Hello World\\nLine 2'"
            }
      }
}

  ✅ image.gen.ai         v1.1.0     [NovaForge (RYBFNMET)]
     Image generation via Hermes API Server with mflux-mlx skill. Uses FLUX.2 Klein 4B q8 or ERNIE-Image Turbo q6. Supports format and style hints in the prompt.
     Input: {
      "fields": {
            "prompt": {
                  "name": "prompt",
                  "type": "string",
                  "required": true,
                  "description": "The image description with optional parameters. Examples: 'A red fox in the snow, photorealistic, 512x512', 'Book cover with dragon, fantasy style, 512x768', 'A cute dog, cartoon style, 768x512', 'A banner with text READING IS FUN, ERNIE model, 1024x576'"
            }
      }
}

  ✅ image.generate.ernie v1.0.0     [NovaForge (RYBFNMET)]
     Direct image generation with ERNIE-Image-Turbo (q6) including artifact upload. ERNIE is the best choice for readable text rendering (titles, author names, banner text, book covers, portraits). Choose format: quadrat (512×512), hochformat (512×768, default), breitformat (768×512) or wallpaper (1024×576, 16:9).
     Input: {
      "fields": {
            "prompt": {
                  "name": "prompt",
                  "type": "string",
                  "required": true,
                  "description": "The image description, especially for text elements (titles, names, banners). Examples: 'Book cover with the title DIE VERBORGENEN REICHE and author Elena Mondstein, fantasy style', 'Portrait of a woman named LI WEI, dramatic lighting', 'Cinematic banner that reads LESEN MACHT SPASS'"
            },
            "format": {
                  "name": "format",
                  "type": "string",
                  "required": false,
                  "description": "Allowed values: quadrat, hochformat, breitformat, wallpaper. Default: hochformat. Image format: quadrat (512\u00d7512, ~53s, 9.5 GB), hochformat (512\u00d7768, ~1:25 min, 10.5 GB \u2014 best for covers/portraits), breitformat (768\u00d7512, ~1:25 min, 10.5 GB), wallpaper (1024\u00d7576, ~2:14 min, 12.4 GB, 16:9)"
            }
      }
}

  ✅ image.generate.mflux v1.1.0     [NovaForge (RYBFNMET)]
     Direct image generation with mflux (FLUX.2 Klein 4B q8, 4 steps) including artifact upload. Choose format: quadrat (512×512), hochformat (512×768) or breitformat (768×512).
     Input: {
      "fields": {
            "prompt": {
                  "name": "prompt",
                  "type": "string",
                  "required": true,
                  "description": "The image description. Examples: 'A red fox in the snow, photorealistic', 'Book cover with dragon and castle, fantasy style', 'A cute dog, cartoon style'"
            },
            "format": {
                  "name": "format",
                  "type": "string",
                  "required": false,
                  "description": "Allowed values: quadrat, hochformat, breitformat. Default: quadrat. Image format: quadrat (512\u00d7512, ~18s, 10.4 GB), hochformat (512\u00d7768, ~33s, 13.5 GB), breitformat (768\u00d7512, ~33s, 13.5 GB)"
            }
      }
}

  ✅ stt.ai               v1.0.0     [NovaForge (RYBFNMET)]
     Speech-to-Text via local macos-speech-server (OpenAI-compatible, whisper-1). Transcribes a WAV/MP3/M4A audio file on this machine into text.
     Input: {
      "fields": {
            "audio_path": {
                  "name": "audio_path",
                  "type": "string",
                  "required": true,
                  "description": "Absolute path to a WAV/MP3/M4A audio file on this machine. Examples: '/tmp/test.wav', '/Users/autologin/projectspiel/tts_1750000000.wav'"
            },
            "language": {
                  "name": "language",
                  "type": "string",
                  "required": false,
                  "description": "Optional ISO-639-1 language code to hint the model. Examples: 'de', 'en'. Omit for auto-detect."
            }
      }
}

  ✅ terminal.ai          v1.0.0     [NovaForge (RYBFNMET), felix-cyberfox (E4W3CBWQ)]
     Executes shell commands via Hermes. Access to bash, python3, git, curl and all standard system tools. Runs autonomously - no user interaction, no follow-up questions.
     Input: {
      "fields": {
            "command": {
                  "name": "command",
                  "type": "string",
                  "required": true,
                  "description": "The command to execute. Examples: 'ls -la /home/user/', 'df -h', 'ps aux | grep python', 'git status', 'curl -s https://api.example.com/status'"
            }
      }
}

  ✅ tts.ai               v1.0.0     [NovaForge (RYBFNMET)]
     Text-to-Speech via local macos-speech-server (OpenAI-compatible, tts-1). Synthesizes speech from text, saves a WAV to projectspiel and uploads it as an artifact.
     Input: {
      "fields": {
            "text": {
                  "name": "text",
                  "type": "string",
                  "required": true,
                  "description": "The text to speak. Examples: 'Hallo von NovaForge', 'Willkommen auf der Lesen-Lernspiel Seite'"
            },
            "voice": {
                  "name": "voice",
                  "type": "string",
                  "required": false,
                  "description": "Default: Anna. Voice name. Default: Anna. Examples: 'Anna', 'Markus', 'Klaus'"
            }
      }
}

  ✅ video.gen.ai         v2.0.0     [NovaForge (RYBFNMET)]
     Video generation via MiniMax H3 (h3.c, native Metal, BF16) on the M4 Mac mini 16GB. ~5x faster than h3stream (~40s/step). Supports T2V, I2V (first/last-frame), and Ref2V (reference images). Long-running. Outputs an MP4 as an artifact.
     Input: {
      "fields": {
            "prompt": {
                  "name": "prompt",
                  "type": "string",
                  "required": true,
                  "description": "The video description. Examples: 'A red fox hacker typing on a holographic keyboard in a cyberpunk command center', 'Cinematic close-up of a fox speaking to camera'. German speech works if requested in the prompt."
            },
            "width": {
                  "name": "width",
                  "type": "number",
                  "required": false,
                  "description": "Default: 512. Video width. Must be a multiple of 16. 512 is RAM-friendly on 16GB."
            },
            "height": {
                  "name": "height",
                  "type": "number",
                  "required": false,
                  "description": "Default: 512. Video height. Must be a multiple of 16."
            },
            "frames": {
                  "name": "frames",
                  "type": "number",
                  "required": false,
                  "description": "Default: 22. Frame count (H3: 5+17n). Max 362 (~15s). ~1s=22 frames. No 30s videos."
            },
            "seconds": {
                  "name": "seconds",
                  "type": "number",
                  "required": false,
                  "description": "Default: 0. Duration in seconds instead of frames (max ~15s). Set 0 to use frames instead."
            },
            "steps": {
                  "name": "steps",
                  "type": "number",
                  "required": false,
                  "description": "Default: 20. Denoise passes. More = better quality but slower (~40s/step on M4 16GB). 20 steps ~13 min; 8 steps ~5 min."
            },
            "layers": {
                  "name": "layers",
                  "type": "number",
                  "required": false,
                  "description": "Default: 45. DiT blocks: 50 exact, 45 fast, 40 aggressive."
            },
            "reuse": {
                  "name": "reuse",
                  "type": "number",
                  "required": false,
                  "description": "Default: 2. Denoiser reuse: 1 close, 2 fast, 3 aggressive."
            },
            "seed": {
                  "name": "seed",
                  "type": "number",
                  "required": false,
                  "description": "Default: 42. Random seed for reproducibility."
            },
            "audio": {
                  "name": "audio",
                  "type": "boolean",
                  "required": false,
                  "description": "Default: True. Generate the video with an audio track (h3.c always produces one)."
            },
            "first_frame": {
                  "name": "first_frame",
                  "type": "string",
                  "required": false,
                  "description": "I2V: path to the start image. Animates from this frame. Mutually exclusive with ref_images."
            },
            "last_frame": {
                  "name": "last_frame",
                  "type": "string",
                  "required": false,
                  "description": "I2V: path to the end image. Animates to this frame. Requires first_frame."
            },
            "ref_images": {
                  "name": "ref_images",
                  "type": "array",
                  "required": false,
                  "description": "Ref2VA: ordered list of reference image paths (max 12). Mutually exclusive with first/last_frame."
            }
      }
}

  ✅ video.gen.ltx        v1.0.0     [NovaForge (RYBFNMET)]
     Native video generation with LTX-2 (MLX, int4) on the M4 Mac mini 16GB — second video backend with NATIVELY GENERATED stereo 48kHz audio (no ffmpeg audio overlay, no click-crackle). Runs ltx-2-mlx generate --one-stage directly (no AI/agent layer) at native 704x480 max resolution. int4 pack + --low-ram block streaming ALWAYS (16GB hard limit). Frame count must satisfy (frames-1)%8==0, max 161. fps: LTX-2.3 was trained at 24. I2V via image path. Output MP4 as artifact. Typical time: ~35min for 25 frames, ~2.5h for 97 frames (one-stage, 30 steps CFG). Examples: prompt='A calm blue lake at golden hour, slow camera glide, birds calling' frames=25; (frames-1)%8==0 -> 25/33/41/65/81/97/121/161; width/height multiples of 32.
     Input: {
      "fields": {
            "prompt": {
                  "name": "prompt",
                  "type": "string",
                  "required": true,
                  "description": "The video description. Examples: 'A red fox walking through a misty pine forest at dawn, birds calling, ambient forest soundscape', 'Close-up of waves breaking on volcanic rocks at sunset, seagulls in the distance'. German speech/sfx on request."
            },
            "frames": {
                  "name": "frames",
                  "type": "number",
                  "required": false,
                  "description": "Default: 97. Frame count. MUST satisfy (frames-1)%8==0 (8k+1 constraint). Max 161 on 16GB. 97 = ~4s at 24fps and ~2.5h runtime; 25 ~1s and ~35min."
            },
            "width": {
                  "name": "width",
                  "type": "number",
                  "required": false,
                  "description": "Default: 704. Video width, multiple of 32, max 704 (one-stage native)."
            },
            "height": {
                  "name": "height",
                  "type": "number",
                  "required": false,
                  "description": "Default: 480. Video height, multiple of 32, max 480 (one-stage native)."
            },
            "fps": {
                  "name": "fps",
                  "type": "number",
                  "required": false,
                  "description": "Default: 24. Output frame rate (8..32). LTX-2.3 was trained at 24; values far from 24 drift out of distribution."
            },
            "image": {
                  "name": "image",
                  "type": "string",
                  "required": false,
                  "description": "Optional: path to a reference image -> image-to-video (frame 0 anchor). Local path on the NovaForge worker."
            },
            "low_ram": {
                  "name": "low_ram",
                  "type": "boolean",
                  "required": false,
                  "description": "Default: True. Block streaming (--low-ram): stream transformer blocks from disk. Keep true on the 16GB node. false would render without streaming and can OOM."
            }
      }
}

  ✅ video.gen.native     v2.0.0     [NovaForge (RYBFNMET)]
     Direct video generation with MiniMax H3 (h3.c, native Metal, BF16) on the M4 Mac mini 16GB. No AI/agent layer — runs h3.c directly. ~5x faster than h3stream. Supports T2V, I2V, Ref2V. Outputs an MP4 as an artifact.
     Input: {
      "fields": {
            "prompt": {
                  "name": "prompt",
                  "type": "string",
                  "required": true,
                  "description": "The video description. Examples: 'A red fox hacker typing on a holographic keyboard in a cyberpunk command center', 'Cinematic close-up of a fox speaking to camera'. German speech works if requested in the prompt."
            },
            "width": {
                  "name": "width",
                  "type": "number",
                  "required": false,
                  "description": "Default: 512. Video width. Must be a multiple of 16."
            },
            "height": {
                  "name": "height",
                  "type": "number",
                  "required": false,
                  "description": "Default: 512. Video height. Must be a multiple of 16."
            },
            "frames": {
                  "name": "frames",
                  "type": "number",
                  "required": false,
                  "description": "Default: 22. Frame count (H3: 5+17n). Max 362 (~15s). No 30s videos."
            },
            "seconds": {
                  "name": "seconds",
                  "type": "number",
                  "required": false,
                  "description": "Default: 0. Duration in seconds instead of frames (max ~15s)."
            },
            "steps": {
                  "name": "steps",
                  "type": "number",
                  "required": false,
                  "description": "Default: 20. Denoise passes (~40s/step on M4 16GB)."
            },
            "layers": {
                  "name": "layers",
                  "type": "number",
                  "required": false,
                  "description": "Default: 45. DiT blocks: 50 exact, 45 fast, 40 aggressive."
            },
            "reuse": {
                  "name": "reuse",
                  "type": "number",
                  "required": false,
                  "description": "Default: 2. Denoiser reuse: 1 close, 2 fast, 3 aggressive."
            },
            "seed": {
                  "name": "seed",
                  "type": "number",
                  "required": false,
                  "description": "Default: 42. Random seed for reproducibility."
            },
            "audio": {
                  "name": "audio",
                  "type": "boolean",
                  "required": false,
                  "description": "Default: True. Generate the video with an audio track."
            },
            "first_frame": {
                  "name": "first_frame",
                  "type": "string",
                  "required": false,
                  "description": "I2V: path to the start image."
            },
            "last_frame": {
                  "name": "last_frame",
                  "type": "string",
                  "required": false,
                  "description": "I2V: path to the end image."
            },
            "ref_images": {
                  "name": "ref_images",
                  "type": "array",
                  "required": false,
                  "description": "Ref2VA: ordered reference image paths (max 12)."
            }
      }
}

  ✅ web.ai               v1.0.0     [NovaForge (RYBFNMET), felix-cyberfox (E4W3CBWQ)]
     Fetches URLs and summarizes content via Hermes. Can scrape web pages and query API endpoints. Runs autonomously - no user interaction, no follow-up questions.
     Input: {
      "fields": {
            "url": {
                  "name": "url",
                  "type": "string",
                  "required": true,
                  "description": "The URL or search query to fetch. Examples: 'https://example.com', 'https://news.ycombinator.com', 'https://api.github.com/repos/nousresearch/hermes-agent'"
            }
      }
}

  ✅ code.ai              v1.0.0     [felix-cyberfox (E4W3CBWQ)]
     Code generation and review — writes, reviews, and debugs code in any language.
     Input: {
      "fields": {
            "prompt": {
                  "name": "prompt",
                  "type": "string",
                  "required": true,
                  "description": "The coding task or question. Example: 'Write a Python function that sorts a list of dicts by a nested key' or 'Review this TypeScript: const x: any = fetch(...)'."
            }
      }
}

  ✅ hermes-test.ai       v1.0.0     [felix-cyberfox (E4W3CBWQ)]
     Hermes connectivity test — sends a simple ping to verify the handler works.
     Input: {
      "fields": {
            "prompt": {
                  "name": "prompt",
                  "type": "string",
                  "required": false,
                  "description": "Optional test message (default: 'ping'). Example: 'ping' or 'Hallo Welt'."
            }
      }
}
```
