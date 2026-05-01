# Perfect Media Resource Map

Perfect Media coordinates these local resources:

| Resource | Path | Role |
|----------|------|------|
| Perfect Media CLI | `/Users/sgkrishna/MasterBase/projects/external-integrations/perfect-media` | Standalone command and docs |
| Official Remotion repo | `/Users/sgkrishna/MasterBase/projects/external-integrations/remotion` | Source reference for React/Remotion video workflows |
| FFmpeg | `/opt/homebrew/bin/ffmpeg` | MP4 fallback rendering |
| FFprobe | `/opt/homebrew/bin/ffprobe` | Video validation |
| Remotion skill | `/Users/sgkrishna/.codex/skills/remotion/SKILL.md` | Video workflow guidance |
| FFmpeg analysis skill | `/Users/sgkrishna/.codex/skills/ffmpeg-video-analysis/SKILL.md` | QC and analysis patterns |
| Screenshot skill | `/Users/sgkrishna/.codex/skills/screenshot/SKILL.md` | Visual capture workflow |
| Playwright skill | `/Users/sgkrishna/.codex/skills/playwright/SKILL.md` | Browser/app automation |
| Speech skill | `/Users/sgkrishna/.codex/skills/speech/SKILL.md` | Voice/audio generation guidance |
| Transcribe skill | `/Users/sgkrishna/.codex/skills/transcribe/SKILL.md` | Caption/transcription workflow |

Generated media belongs beside the assigned target in `perfect-media-output`.

## Input Modes

| Mode | Example | Output Behavior |
|------|---------|-----------------|
| App bundle | `perfect-media FileSmith-May-01.app` | Resolves from `/Applications`, MasterBase, or the current folder |
| Project folder | `perfect-media /path/to/project --kind marketing` | Reads package/source hints and writes beside the project |
| URL | `perfect-media https://example.com --kind ad` | Builds a URL-derived video package |
| Creative brief | `perfect-media "create a goofy city-animal trailer for 2 mins"` | Builds prompt-derived storyboard, captions, reasoning, upgrade ideas, and MP4 |

## Reasoning Layer

The CLI writes `VIDEO-BUILD-REPORT.md` with:

- source confidence
- selected video formats
- resolved paths and resources
- generated artifacts
- reasoning and upgrade ideas
- limitations and next renderer options

This lets any AI model or human operator inspect what happened and decide how to
make the next video generation better.
