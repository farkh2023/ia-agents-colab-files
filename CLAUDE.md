# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Directory Is

`Colab_files/` is a local cache of browser-saved artifacts from Google Colab sessions. It contains:
- HTML output frames rendered by Colab notebook cells (`outputframe*.html`)
- Saved Colab notebook pages (`saved_resource*.html`)
- Cached JavaScript/CSS assets from the Colab runtime

**The actual notebooks live on Google Drive**, not here. To edit or run code, open the notebooks directly in [Google Colab](https://colab.research.google.com).

## Project Domain

The notebooks in this project are Python-based AI agents using the Gemini API:
- Client: `google.genai.Client` from the `google-genai` package
- Auth: `GEMINI_API_KEY` stored as a Colab secret (accessed via `google.colab.userdata.get("GOOGLE_API_KEY")`)
- Storage: Google Drive mounted at `/content/drive`

## Working With Colab Notebooks Locally

If you download a notebook (`.ipynb`) into this directory, you can run it locally with:

```bash
pip install google-genai jupyter
GEMINI_API_KEY=your_key jupyter notebook notebook_name.ipynb
```

Note: `google.colab.*` imports (`userdata`, `drive`) are Colab-specific and will fail outside Colab. Replace them with local environment variable reads when running locally.
