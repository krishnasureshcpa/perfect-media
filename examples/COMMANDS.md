# Perfect Media Commands

```bash
# App by exact name, resolved from /Applications or MasterBase
perfect-media FileSmith-May-01.app

# Specific app path
perfect-media /Applications/FileSmith-May-01.app --kind walkthrough

# Generate all supported video packages
perfect-media /Applications/FileSmith-May-01.app --all

# Project folder
perfect-media /Users/sgkrishna/MasterBase/projects/active-applications/apps/The-FileSmith-App --kind marketing

# URL
perfect-media https://example.com --kind ad

# Natural-language creative brief
perfect-media "create a up-like character that is as cute and goofy but if it was zootopia and make it as a trailer for 2 mins"

# Force a video type from a prompt
perfect-media "make a launch ad for a file archive app in 45 seconds" --kind ad

# Prompt with explicit duration
perfect-media "create a workflow explainer for organizing chaotic project folders" --duration 60

# Plan without writing files
perfect-media FileSmith-May-01.app --all --dry-run

# Custom output root
perfect-media FileSmith-May-01.app --output ~/Desktop/perfect-media-output --kind launch
```

Default output folder:

```text
<target-or-parent>/perfect-media-output/<TargetName-Mon-DD>/videos/
```

Installed apps in `/Applications` default to:

```text
/Applications/perfect-media-output/<AppName-Mon-DD>/videos/
```

Natural-language briefs default to:

```text
./perfect-media-output/<prompt-slug-Mon-DD>/videos/
```
