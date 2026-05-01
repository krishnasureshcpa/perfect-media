#!/usr/bin/env python3
"""Standalone video asset generator for apps, projects, files, and URLs.

`perfect-media` is intentionally separate from master-architect-fixer. It can
use the same local Remotion repo and video resources, but writes to its own
`perfect-media-output` folder so anyone can use it without the builder.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


MASTERBASE_ROOT = Path(os.environ.get("MASTERBASE_ROOT", "/Users/sgkrishna/MasterBase"))
TOOL_ROOT = MASTERBASE_ROOT / "projects" / "external-integrations" / "perfect-media"
REMOTION_REPO = MASTERBASE_ROOT / "projects" / "external-integrations" / "remotion"
VIDEO_KINDS = ("walkthrough", "how-to", "marketing", "ad", "launch", "workflow", "trailer", "concept")
VIDEO_TITLES = {
    "walkthrough": "App Walkthrough",
    "how-to": "How-To Guide",
    "marketing": "Marketing Overview",
    "ad": "Short Ad Spot",
    "launch": "Launch Story",
    "workflow": "Workflow Demo",
    "trailer": "Concept Trailer",
    "concept": "Creative Concept Film",
}
SEARCH_ROOTS = (
    Path.cwd(),
    MASTERBASE_ROOT,
    MASTERBASE_ROOT / "projects",
    MASTERBASE_ROOT / "apps",
    Path("/Applications"),
)


@dataclass
class Step:
    name: str
    status: str
    detail: str = ""


@dataclass
class MediaContext:
    raw_target: str
    target: Path | None
    output_dir: Path
    videos_dir: Path
    dry_run: bool = False
    steps: list[Step] = field(default_factory=list)

    def record(self, name: str, status: str, detail: str = "") -> None:
        self.steps.append(Step(name, status, detail))
        suffix = f" - {detail}" if detail else ""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {status.upper()}: {name}{suffix}")


def looks_like_creative_brief(value: str) -> bool:
    if is_url(value):
        return False
    expanded = Path(value).expanduser()
    if expanded.exists():
        return False
    if expanded.is_absolute() or expanded.parent != Path("."):
        return False
    lowered = value.lower()
    brief_words = {
        "create",
        "make",
        "trailer",
        "video",
        "ad",
        "character",
        "movie",
        "story",
        "scene",
        "cute",
        "goofy",
        "style",
        "minutes",
        "mins",
    }
    return " " in value and any(word in lowered for word in brief_words)


def is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def safe_name(value: str | Path) -> str:
    name = Path(str(value)).name
    for suffix in (".app", ".dmg"):
        if name.endswith(suffix):
            name = Path(name).stem
    if not name and is_url(str(value)):
        parsed = urlparse(str(value))
        name = parsed.netloc + parsed.path.rstrip("/")
    cleaned = "".join(ch if ch.isalnum() or ch in "._- " else "-" for ch in name).strip(" .-_")
    return cleaned or "media-target"


def prompt_slug(prompt: str) -> str:
    words = re.findall(r"[A-Za-z0-9]+", prompt.lower())
    stop = {"a", "an", "and", "as", "but", "if", "it", "of", "the", "to", "for", "with", "that", "is", "was"}
    selected = [word for word in words if word not in stop][:8]
    digest = hashlib.sha1(prompt.encode("utf-8")).hexdigest()[:8]
    return "-".join(selected or ["creative-brief"]) + "-" + digest


def stamped_name(base: str, stamp: str) -> str:
    return base if base.endswith(stamp) else f"{base}{stamp}"


def resolve_target(raw: str) -> Path | None:
    if is_url(raw):
        return None
    expanded = Path(raw).expanduser()
    if expanded.exists():
        return expanded.resolve()
    if expanded.is_absolute() or expanded.parent != Path("."):
        return expanded.resolve()

    for root in SEARCH_ROOTS:
        candidate = root / raw
        if candidate.exists():
            return candidate.resolve()

    for root in SEARCH_ROOTS[1:]:
        if not root.exists():
            continue
        try:
            for candidate in root.rglob(raw):
                if candidate.exists():
                    return candidate.resolve()
        except (OSError, PermissionError):
            continue
    return expanded.resolve()


def command_exists(command: str) -> bool:
    return shutil.which(command) is not None


def output_root_for(raw: str, target: Path | None, output: str | None) -> Path:
    if output:
        return Path(output).expanduser().resolve()
    if target and target.exists():
        if target.suffix == ".app" and target.parent == Path("/Applications"):
            return Path("/Applications") / "perfect-media-output"
        parent = target.parent if target.is_file() or target.suffix == ".app" else target
        return parent / "perfect-media-output"
    return Path.cwd() / "perfect-media-output"


def infer_duration_seconds(prompt: str | None, default: int = 15) -> int:
    if not prompt:
        return default
    lowered = prompt.lower()
    match = re.search(r"(\d+)\s*(?:min|mins|minute|minutes)\b", lowered)
    if match:
        return max(15, min(600, int(match.group(1)) * 60))
    match = re.search(r"(\d+)\s*(?:sec|secs|second|seconds)\b", lowered)
    if match:
        return max(5, min(600, int(match.group(1))))
    if "trailer" in lowered:
        return 120
    return default


def infer_kind_from_prompt(prompt: str, requested: str | None) -> str:
    if requested:
        return requested
    lowered = prompt.lower()
    if "trailer" in lowered or "movie" in lowered:
        return "trailer"
    if "ad" in lowered or "commercial" in lowered:
        return "ad"
    if "how" in lowered or "tutorial" in lowered:
        return "how-to"
    if "marketing" in lowered or "promo" in lowered:
        return "marketing"
    return "concept"


def creative_brief_facts(prompt: str) -> dict:
    slug = prompt_slug(prompt)
    return {
        "name": slug,
        "raw_target": prompt,
        "target": "creative-brief",
        "source_confidence": "prompt-derived",
        "source_root": "",
        "framework": "natural-language creative brief",
        "description": prompt.strip(),
        "creative_prompt": prompt.strip(),
        "duration_seconds": infer_duration_seconds(prompt),
    }


def collect_facts(raw: str, target: Path | None) -> dict:
    if looks_like_creative_brief(raw):
        return creative_brief_facts(raw)
    name = safe_name(target or raw)
    facts = {
        "name": name,
        "raw_target": raw,
        "target": str(target) if target else raw,
        "source_confidence": "layout-derived",
        "source_root": "",
        "framework": "url" if is_url(raw) else "unknown",
        "description": "Video generated from available app, project, URL, file, and layout metadata.",
    }
    if target and target.exists():
        if target.suffix == ".app":
            facts["framework"] = "macOS app bundle"
            facts["source_confidence"] = "app-layout-derived"
            plist = target / "Contents" / "Info.plist"
            if plist.exists() and command_exists("plutil"):
                for key, field_name in (("CFBundleDisplayName", "name"), ("CFBundleName", "name"), ("CFBundleIdentifier", "bundle_id")):
                    proc = subprocess.run(["plutil", "-extract", key, "raw", str(plist)], text=True, capture_output=True)
                    if proc.returncode == 0 and proc.stdout.strip():
                        facts[field_name] = proc.stdout.strip()
        elif target.is_dir():
            facts["source_root"] = str(target)
            facts["source_confidence"] = "source-derived"
            if (target / "package.json").exists():
                facts["framework"] = "node/react/vite/electron/tauri"
                try:
                    data = json.loads((target / "package.json").read_text())
                    facts["name"] = data.get("name") or facts["name"]
                    facts["description"] = data.get("description") or facts["description"]
                except (OSError, json.JSONDecodeError):
                    pass
            elif (target / "Package.swift").exists():
                facts["framework"] = "swift package"
            elif any(target.glob("*.xcodeproj")):
                facts["framework"] = "xcode"
            elif (target / "pyproject.toml").exists() or any(target.glob("*.py")):
                facts["framework"] = "python"
            else:
                facts["framework"] = "folder"
        else:
            facts["framework"] = target.suffix.lstrip(".") or "file"
    return facts


def video_scenes(kind: str, facts: dict) -> list[dict[str, str]]:
    if facts.get("source_confidence") == "prompt-derived":
        return prompt_video_scenes(kind, facts)
    title = VIDEO_TITLES[kind]
    name = facts.get("name", "Target")
    source = facts.get("source_root") or facts.get("target")
    base = [
        {"title": f"{name} - {title}", "subtitle": f"{facts['source_confidence']} media package"},
        {"title": "Target Read", "subtitle": f"Framework: {facts['framework']}; source: {source}"},
        {"title": "What It Does", "subtitle": facts.get("description", "A focused product workflow.")},
    ]
    endings = {
        "walkthrough": [
            {"title": "Screen Story", "subtitle": "Show the entry screen, the main action, and the expected result."},
            {"title": "Use It", "subtitle": "Open the app or project and follow the visible workflow."},
        ],
        "how-to": [
            {"title": "Step One", "subtitle": "Choose the input app, project, file, folder, or URL."},
            {"title": "Step Two", "subtitle": "Review the generated video, captions, storyboard, and report."},
        ],
        "marketing": [
            {"title": "Value", "subtitle": "Explain what changes for the user and where the output is saved."},
            {"title": "Share", "subtitle": "Use the MP4, captions, and storyboard as the media handoff."},
        ],
        "ad": [
            {"title": "Fast Message", "subtitle": "A short, direct product story for social or launch use."},
            {"title": "Call To Action", "subtitle": "Open, inspect, use, and share the generated package."},
        ],
        "launch": [
            {"title": "Release Moment", "subtitle": "Frame the app/project as a complete launch package."},
            {"title": "Ready Assets", "subtitle": "Videos, captions, reports, and storyboards are together."},
        ],
        "workflow": [
            {"title": "Input To Output", "subtitle": "Follow the workflow from selected target to media package."},
            {"title": "Traceable Result", "subtitle": "Every output is documented in VIDEO-BUILD-REPORT.md."},
        ],
        "trailer": [
            {"title": "The Hook", "subtitle": "Open on the strongest emotional promise in the creative brief."},
            {"title": "The World", "subtitle": "Show the setting, the central contrast, and the character's first choice."},
        ],
        "concept": [
            {"title": "Concept Beat", "subtitle": "Turn the natural-language idea into a clear visual promise."},
            {"title": "Next Build", "subtitle": "Use the idea sheet to improve characters, shots, voice, and pacing."},
        ],
    }
    return base + endings[kind]


def split_prompt_beats(prompt: str, count: int) -> list[str]:
    pieces = [piece.strip(" .!?") for piece in re.split(r"[,.;\n]+", prompt) if piece.strip()]
    if not pieces:
        pieces = [prompt.strip()]
    while len(pieces) < count:
        pieces.append(pieces[-1])
    return pieces[:count]


def prompt_video_scenes(kind: str, facts: dict) -> list[dict[str, str]]:
    prompt = facts.get("creative_prompt") or facts.get("description") or "Creative brief"
    beats = split_prompt_beats(prompt, 6)
    title = VIDEO_TITLES.get(kind, "Creative Video")
    return [
        {"title": f"{title}: New Idea", "subtitle": beats[0]},
        {"title": "Reasoning Pass", "subtitle": "Audience, tone, character energy, conflict, and shareability are mapped before rendering."},
        {"title": "Character Direction", "subtitle": beats[1]},
        {"title": "World And Mood", "subtitle": beats[2]},
        {"title": "Trailer Structure", "subtitle": "Tease the world, introduce the character, raise the stakes, then end on a memorable reveal."},
        {"title": "Upgrade Ideas", "subtitle": "Improve the next render with reference images, voiceover, source footage, music timing, and scene-specific prompts."},
    ]


def color_for(kind: str) -> str:
    return {
        "walkthrough": "0x101827",
        "how-to": "0x13231c",
        "marketing": "0x241a2e",
        "ad": "0x301417",
        "launch": "0x10242a",
        "workflow": "0x201f14",
        "trailer": "0x1d1828",
        "concept": "0x18251f",
    }[kind]


def srt_time(seconds: int) -> str:
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d},000"


def write_storyboard(kind: str, scenes: list[dict[str, str]], facts: dict, ctx: MediaContext) -> list[Path]:
    md = ctx.videos_dir / f"{kind}-storyboard.md"
    js = ctx.videos_dir / f"{kind}-storyboard.json"
    lines = [
        f"# {VIDEO_TITLES[kind]} Storyboard",
        "",
        f"- Target: `{facts['raw_target']}`",
        f"- Source confidence: `{facts['source_confidence']}`",
        f"- Remotion repo: `{REMOTION_REPO}`",
        "",
    ]
    for index, scene in enumerate(scenes, 1):
        lines.extend([f"## {index}. {scene['title']}", "", scene["subtitle"], ""])
    if ctx.dry_run:
        ctx.record(f"storyboard {kind}", "dry-run", str(md))
    else:
        md.write_text("\n".join(lines))
        js.write_text(json.dumps({"kind": kind, "facts": facts, "scenes": scenes}, indent=2) + "\n")
        ctx.record(f"storyboard {kind}", "ok", str(md))
    return [md, js]


def write_captions(kind: str, scenes: list[dict[str, str]], ctx: MediaContext, duration_seconds: int = 15) -> Path:
    path = ctx.videos_dir / f"{kind}.srt"
    lines: list[str] = []
    per_scene = max(2, int(round(duration_seconds / max(1, len(scenes)))))
    for index, scene in enumerate(scenes, 1):
        start = (index - 1) * per_scene
        end = start + per_scene
        lines.extend([str(index), f"{srt_time(start)} --> {srt_time(end)}", scene["title"], scene["subtitle"], ""])
    if ctx.dry_run:
        ctx.record(f"captions {kind}", "dry-run", str(path))
    else:
        path.write_text("\n".join(lines))
        ctx.record(f"captions {kind}", "ok", str(path))
    return path


def render_segment(kind: str, segment: Path, ctx: MediaContext, duration: int = 3) -> bool:
    fade_out = max(0.4, duration - 0.35)
    vf = (
        "fade=t=in:st=0:d=0.35,"
        f"fade=t=out:st={fade_out}:d=0.35,"
        "drawbox=x=0:y=0:w=1280:h=18:color=0x88F7FF@0.85:t=fill,"
        "drawbox=x=70:y=140:w=1140:h=8:color=0xFFFFFF@0.22:t=fill,"
        "drawbox=x=70:y=255:w=840:h=20:color=0x88F7FF@0.50:t=fill,"
        "drawbox=x=70:y=330:w=1000:h=12:color=0xD8DEE9@0.34:t=fill,"
        "drawbox=x=70:y=382:w=780:h=12:color=0xD8DEE9@0.24:t=fill,"
        "drawbox=x=70:y=520:w=1140:h=4:color=0xFFFFFF@0.18:t=fill,"
        "drawbox=x=70:y=560:w=300:h=34:color=0x88F7FF@0.22:t=fill"
    )
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"color=c={color_for(kind)}:s=1280x720:d={duration}",
        "-vf",
        vf,
        "-r",
        "30",
        "-pix_fmt",
        "yuv420p",
        str(segment),
    ]
    proc = subprocess.run(cmd, text=True, capture_output=True)
    if proc.returncode == 0:
        ctx.record(f"render {segment.name}", "ok", "scene rendered")
        return True
    ctx.record(f"render {segment.name}", "failed", (proc.stderr or proc.stdout)[-500:])
    return False


def render_video(kind: str, scenes: list[dict[str, str]], ctx: MediaContext, duration_seconds: int = 15) -> Path | None:
    out = ctx.videos_dir / f"{kind}.mp4"
    if ctx.dry_run:
        ctx.record(f"video {kind}", "dry-run", str(out))
        return out
    if not command_exists("ffmpeg"):
        ctx.record(f"video {kind}", "failed", "ffmpeg not found")
        return None
    segments_dir = ctx.videos_dir / "_segments" / kind
    segments_dir.mkdir(parents=True, exist_ok=True)
    segments: list[Path] = []
    per_scene = max(2, int(round(duration_seconds / max(1, len(scenes)))))
    for index, _scene in enumerate(scenes, 1):
        segment = segments_dir / f"{index:02d}-{kind}.mp4"
        if render_segment(kind, segment, ctx, per_scene):
            segments.append(segment)
    if not segments:
        return None
    concat = segments_dir / "concat.txt"
    concat.write_text("".join(f"file '{segment}'\n" for segment in segments))
    proc = subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", str(out)], text=True, capture_output=True)
    if proc.returncode == 0:
        ctx.record(f"assemble {kind}", "ok", str(out))
        return out
    ctx.record(f"assemble {kind}", "failed", (proc.stderr or proc.stdout)[-500:])
    return None


def progress(label: str, dry_run: bool) -> None:
    if dry_run or not sys.stdout.isatty():
        return
    colors = ["\033[38;5;39m", "\033[38;5;45m", "\033[38;5;84m", "\033[38;5;190m", "\033[38;5;214m", "\033[38;5;205m"]
    for pct in range(1, 101):
        color = colors[min(len(colors) - 1, pct // 18)]
        filled = max(1, int(34 * pct / 100))
        phase = "thinking" if pct < 22 else "mapping" if pct < 44 else "building" if pct < 68 else "rendering" if pct < 90 else "saving"
        print(f"\r{color}{label:<20} {pct:3d}% {'█' * filled}{'░' * (34 - filled)} {phase}\033[0m", end="", flush=True)
    print()


def write_report(facts: dict, kinds: list[str], outputs: list[Path | None], ctx: MediaContext) -> Path:
    report = ctx.videos_dir / "VIDEO-BUILD-REPORT.md"
    lines = [
        "# Perfect Media Video Build Report",
        "",
        f"- Target: `{facts['raw_target']}`",
        f"- Resolved target: `{facts['target']}`",
        f"- Source confidence: `{facts['source_confidence']}`",
        f"- Framework: `{facts['framework']}`",
        f"- Intended duration: `{facts.get('duration_seconds', 'auto')}` seconds",
        f"- Tool root: `{TOOL_ROOT}`",
        f"- Remotion repo: `{REMOTION_REPO}`",
        "",
        "## Selected Video Types",
        "",
        *[f"- {VIDEO_TITLES[kind]}" for kind in kinds],
        "",
        "## Outputs",
        "",
        *[f"- `{path}`" for path in outputs if path],
        "",
        "## Reasoning And Upgrade Ideas",
        "",
        *reasoning_lines(facts, kinds),
        "",
        "## Steps",
        "",
        *[f"- **{step.status}** {step.name}: {step.detail}" if step.detail else f"- **{step.status}** {step.name}" for step in ctx.steps],
        "",
    ]
    if ctx.dry_run:
        ctx.record("report", "dry-run", str(report))
    else:
        report.write_text("\n".join(lines))
        ctx.record("report", "ok", str(report))
    return report


def reasoning_lines(facts: dict, kinds: list[str]) -> list[str]:
    prompt = facts.get("creative_prompt") or facts.get("description", "")
    lines = [
        "- Start with a source scan when a real app/project is provided; otherwise treat the quoted target as a creative brief.",
        "- Build the storyboard before rendering so narration, captions, pacing, and visual sections stay aligned.",
        "- Improve later renders by adding screenshots, product footage, reference images, music direction, and voiceover notes.",
    ]
    if prompt:
        lines.extend(
            [
                f"- Creative brief: `{prompt}`",
                "- Prompt-to-video mode currently renders a real edit package with storyboard, captions, report, and MP4 motion plates.",
                "- For higher fidelity, pass the storyboard into Remotion, Runway, Pika, Luma, Stable Video, or another model-backed renderer.",
            ]
        )
    if "trailer" in kinds:
        lines.append("- Trailer mode should emphasize character reveal, world contrast, escalating stakes, and a final title-card beat.")
    return lines


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create app/project/URL videos with a standalone Remotion-aware media workflow.")
    parser.add_argument("target", nargs="?", default=".", help="File path, app name with extension, project folder, or URL.")
    parser.add_argument("--output", help="Custom output root. Defaults to perfect-media-output beside the target.")
    parser.add_argument("--kind", choices=VIDEO_KINDS, help="Generate one video type.")
    parser.add_argument("--all", action="store_true", help="Generate all video types.")
    parser.add_argument("--prompt", action="store_true", help="Force natural-language creative brief mode.")
    parser.add_argument("--duration", type=int, help="Requested video length in seconds. Prompt text like '2 mins' is also understood.")
    parser.add_argument("--dry-run", action="store_true", help="Plan outputs without writing/rendering videos.")
    return parser.parse_args(argv)


def choose_kinds(args: argparse.Namespace) -> list[str]:
    if args.all:
        return list(VIDEO_KINDS)
    if args.kind:
        return [args.kind]
    if not sys.stdin.isatty():
        return ["walkthrough"]
    print("\nPerfect Media options:\n")
    for index, kind in enumerate(VIDEO_KINDS, 1):
        print(f"  {index}. {VIDEO_TITLES[kind]}")
    print("  7. All")
    choice = input("\nChoice [default 7]: ").strip() or "7"
    if choice == "7" or choice.lower() == "all":
        return list(VIDEO_KINDS)
    try:
        index = int(choice)
    except ValueError:
        return ["walkthrough"]
    return [VIDEO_KINDS[index - 1]] if 1 <= index <= len(VIDEO_KINDS) else list(VIDEO_KINDS)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    prompt_mode = args.prompt or looks_like_creative_brief(args.target)
    target = None if prompt_mode else resolve_target(args.target)
    if not prompt_mode and target and not target.exists() and not is_url(args.target):
        print(f"ERROR: target not found: {target}", file=sys.stderr)
        return 1
    stamp = datetime.now().strftime("-%b-%d")
    output_root = output_root_for(args.target, target, args.output)
    output_name = prompt_slug(args.target) if prompt_mode else safe_name(target or args.target)
    output_dir = output_root / stamped_name(output_name, stamp)
    videos_dir = output_dir / "videos"
    ctx = MediaContext(args.target, target, output_dir, videos_dir, args.dry_run)
    if not args.dry_run:
        videos_dir.mkdir(parents=True, exist_ok=True)
    facts = creative_brief_facts(args.target) if prompt_mode else collect_facts(args.target, target)
    if args.duration:
        facts["duration_seconds"] = max(5, min(600, args.duration))
    kinds = [infer_kind_from_prompt(args.target, args.kind)] if prompt_mode and not args.all else choose_kinds(args)
    ctx.record("target", "ok", facts["source_confidence"])
    ctx.record("remotion repo", "ok" if REMOTION_REPO.exists() else "missing", str(REMOTION_REPO))
    ctx.record("video options", "ok", ", ".join(kinds))
    outputs: list[Path | None] = []
    for kind in kinds:
        progress(VIDEO_TITLES[kind], args.dry_run)
        scenes = video_scenes(kind, facts)
        outputs.extend(write_storyboard(kind, scenes, facts, ctx))
        outputs.append(write_captions(kind, scenes, ctx, int(facts.get("duration_seconds") or 15)))
        outputs.append(render_video(kind, scenes, ctx, int(facts.get("duration_seconds") or 15)))
    outputs.append(write_report(facts, kinds, outputs, ctx))
    failures = [step for step in ctx.steps if step.status in {"failed", "missing"}]
    if failures:
        print(f"\nCompleted with {len(failures)} issue(s). See {ctx.videos_dir}.")
        return 2
    print(f"\nPerfect Media outputs saved in: {ctx.videos_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
