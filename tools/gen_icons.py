#!/usr/bin/env python3
"""Genera assets/icon-32.png y assets/icon-180.png a partir de assets/icon.svg.

Requiere: python3 -m pip install playwright && python3 -m playwright install chromium
"""
import asyncio, pathlib
from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
SVG = (ROOT / 'assets' / 'icon.svg').read_text()

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for size in (32, 180):
            pg = await b.new_page(viewport={'width': size, 'height': size})
            await pg.set_content(f'<html><body style="margin:0;background:transparent">'
                                 f'<div style="width:{size}px;height:{size}px">{SVG.replace("<svg ", f"<svg width=\'{size}\' height=\'{size}\' ")}</div></body></html>')
            out = ROOT / 'assets' / f'icon-{size}.png'
            await pg.screenshot(path=str(out), omit_background=True, clip={'x': 0, 'y': 0, 'width': size, 'height': size})
            print('escrito', out.relative_to(ROOT))
        await b.close()

asyncio.run(main())
