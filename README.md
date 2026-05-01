# Perfect Media

Standalone app/project/URL/natural-language video generator.

This folder is separate from `master-architect-fixer`. It uses the local Remotion repo and FFmpeg video resources as one system, but it does not require `master-architect-output`.

## Command

```bash
perfect-media [filepath-or-app-name-with-extension]
perfect-media /Applications/FileSmith-May-01.app --kind walkthrough
perfect-media FileSmith-May-01.app --all
perfect-media https://example.com --kind marketing
perfect-media "create a up-like character that is as cute and goofy but if it was zootopia and make it as a trailer for 2 mins"
```

If the argument is not a real path or URL and reads like a creative sentence,
`perfect-media` treats it as a natural-language brief. It will infer whether the
brief is a trailer, ad, concept film, how-to, or marketing piece, then produce a
storyboard, captions, reasoning notes, upgrade ideas, and a real MP4 motion edit.

## Output

Outputs go into `perfect-media-output`, not `master-architect-output`.

Examples:

```text
/Applications/perfect-media-output/FileSmith-May-01-May-01/videos/
/path/to/project/perfect-media-output/MyProject-May-01/videos/
```

Each run can create:

- `walkthrough.mp4`
- `how-to.mp4`
- `marketing.mp4`
- `ad.mp4`
- `launch.mp4`
- `workflow.mp4`
- `trailer.mp4`
- `concept.mp4`
- matching `.srt` captions
- matching storyboard `.md` and `.json`
- `VIDEO-BUILD-REPORT.md`

For creative briefs, outputs are saved under:

```text
./perfect-media-output/<prompt-slug>-May-01/videos/
```

Use `--output /some/folder` to control where the package is written.

## Reasoning And Ideas

Every build report includes a reasoning section that explains:

- whether the tool used source-derived, layout-derived, URL-derived, or prompt-derived input
- how the storyboard was chosen
- what would improve the next generation
- what external video model or renderer could be used for higher fidelity

Prompt mode is intentionally model-agnostic. It can be called by Codex, Claude,
OpenAI API agents, Gemini, DeepSeek, OpenRouter models, local LLM agents, MCP
agents, shell automation, or a human in Terminal.

## Smoke Test

```bash
PYTHONPYCACHEPREFIX=/private/tmp/perfect-media-pycache python3 -m py_compile src/perfect_media.py
./perfect-media --help
./perfect-media "create a cute goofy city-animal trailer for 20 seconds" --dry-run
./perfect-media "create a cute goofy city-animal trailer for 20 seconds"
ffprobe perfect-media-output/*/videos/trailer.mp4
```

## Video Resources

- Official Remotion repo: `/Users/sgkrishna/MasterBase/projects/external-integrations/remotion`
- Local Remotion skill: `/Users/sgkrishna/.codex/skills/remotion/SKILL.md`
- FFmpeg analysis skill: `/Users/sgkrishna/.codex/skills/ffmpeg-video-analysis/SKILL.md`
- Screenshot skill: `/Users/sgkrishna/.codex/skills/screenshot/SKILL.md`
- Playwright skill: `/Users/sgkrishna/.codex/skills/playwright/SKILL.md`
- Speech/transcribe skills: `/Users/sgkrishna/.codex/skills/speech`, `/Users/sgkrishna/.codex/skills/transcribe`

## Model-Agnostic

Any AI model or automation can call this command:

- Codex
- Claude
- ChatGPT/OpenAI API agents
- Gemini
- DeepSeek
- OpenRouter-routed models
- local LLM agents
- MCP agents
- shell automation

## Install

```bash
mkdir -p ~/.local/bin
ln -sf /Users/sgkrishna/MasterBase/projects/external-integrations/perfect-media/shell/perfect-media.sh ~/.local/bin/perfect-media
```

Make sure `~/.local/bin` is on `PATH`.
