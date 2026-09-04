# Security and Secrets

Never commit API keys, passwords, OAuth tokens, or private runtime environment files.

Private files expected on the Raspberry Pi:

- `/home/ty/.config/legopi/openai.env`
- `/home/ty/.config/legopi/elevenlabs.env`
- `/home/ty/.config/legopi/runtime.env` (non-secret deployment settings, e.g.
  `LEGOPI_CAMERA_ROTATE` — loaded by the systemd services the same way as the two files
  above, kept alongside them for consistency, not because it holds secrets)

The repository contains only `config/runtime.env.example` as a template.

The public repository intentionally excludes the live inventory database at
`/home/ty/legopi-data/lego_inventory.db`.
