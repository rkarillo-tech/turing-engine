#!/usr/bin/env python3
"""Pruebas de extremo a extremo de Turing Engine con Playwright.

Uso:
    python3 -m pip install playwright
    python3 -m playwright install chromium
    python3 tests/test_juego.py
"""
import asyncio
import pathlib
import sys

from playwright.async_api import async_playwright

URL = (pathlib.Path(__file__).resolve().parent.parent / 'index.html').as_uri()
fallos = []


def comprobar(cond, msg):
    print(('  ✓ ' if cond else '  ✗ ') + msg)
    if not cond:
        fallos.append(msg)


async def nueva_pagina(browser, **kw):
    pg = await browser.new_page(**kw)
    errores = []
    pg.on('pageerror', lambda e: errores.append(str(e)))
    # Las fuentes de Google pueden no estar disponibles; no afectan a las pruebas.
    await pg.route('**/fonts.g*/**', lambda r: r.abort())
    await pg.goto(URL)
    await pg.wait_for_timeout(300)
    return pg, errores


async def soluciones(browser):
    print('Soluciones de referencia (15 niveles × 4 ciclos)')
    pg, errores = await nueva_pagina(browser)
    malas = await pg.evaluate("""() => {
      const out = [];
      for (let c = 0; c < 4; c++) for (let i = 0; i < LEVELS.length; i++) {
        P.cycle = c; P.idx = i; lvl = LEVELS[i]; buildTests();
        tests.forEach((t, k) => {
          const r = simulate(lvl.solution, t.input, 'q0', maxSteps);
          if (!judge(t.input, r).ok) out.push(`ciclo ${c + 1} nivel ${i + 1} prueba ${k + 1}`);
        });
        if (lvl.kind === 'decide' && (!tests.some(t => t.want) || !tests.some(t => !t.want)))
          out.push(`ciclo ${c + 1} nivel ${i + 1}: pruebas sin casos sí y no`);
      }
      return out;
    }""")
    comprobar(not malas, 'todas las soluciones superan todas sus pruebas' + (f': {malas}' if malas else ''))
    comprobar(not errores, 'sin errores de JavaScript')
    await pg.close()


async def partida_guiada(browser):
    print('Partida guiada con clics reales')
    pg, errores = await nueva_pagina(browser, viewport={'width': 1366, 'height': 900})
    coach = lambda: pg.evaluate('coachI')

    async def regla(key, w, d, s):
        await pg.click(f'.r-cell[data-key="{key}"]')
        await pg.click(f'#ed-write .bg-btn[data-w="{w}"]')
        await pg.click(f'#ed-dir .bg-btn[data-d="{d}"]')
        await pg.click(f'#ed-states .bg-btn[data-s="{s}"]')
        await pg.keyboard.press('Enter')
        await pg.wait_for_timeout(300)

    await pg.click('.wopt.rec')
    for _ in range(3):
        await pg.click('#coach-next')
    await pg.click('.r-cell[data-key="q0,0"]')
    await pg.click('#ed-write .bg-btn[data-w="0"]')
    await pg.keyboard.press('Enter')
    await pg.wait_for_timeout(300)
    comprobar('no es la que buscamos' in await pg.inner_text('#coach-warn'), 'avisa al elegir una regla equivocada')
    await regla('q0,0', '1', 'R', 'q0')
    await pg.click('#btn-step')
    await pg.keyboard.press('n')
    await pg.keyboard.press('n')
    await pg.wait_for_timeout(300)
    comprobar(await pg.evaluate('steps') == 3, 'los atajos de teclado funcionan tras pulsar un botón')
    await regla('q0,_', '_', 'S', 'qA')
    await pg.click('#btn-step')
    await pg.wait_for_timeout(1000)
    comprobar(await pg.evaluate("$('res-modal').classList.contains('show')"), 'se supera el nivel 1')
    await pg.click('#coach-next')
    await pg.wait_for_timeout(200)
    comprobar(await coach() == -1 and await pg.evaluate('P.idx') == 1, 'la guía termina y pasa al nivel 2')

    # Continuar tras definir una regla que faltaba
    await pg.click('#btn-run')
    await pg.wait_for_timeout(800)
    comprobar(await pg.evaluate("haltReason") == 'norule', 'se detiene si falta una regla')
    await pg.evaluate("trans=clone(lvl.solution);renderAll()")
    await pg.click('#btn-step')
    comprobar(await pg.evaluate("!halted||accepted"), 'continúa desde donde se detuvo')

    # Licencia visible
    await pg.click('#credits .link-inline')
    texto = await pg.inner_text('#lic-modal')
    comprobar('Rafael Karino Arillo' in texto and 'MIT' in texto, 'la ventana de licencia es visible desde el pie')
    comprobar(await pg.evaluate("[...document.querySelectorAll('link[rel=icon]')].length") >= 1, 'hay icono para la pestaña')
    comprobar(not errores, 'sin errores de JavaScript')
    await pg.close()


async def movil(browser):
    print('Móvil')
    pg, errores = await nueva_pagina(browser, viewport={'width': 390, 'height': 844}, is_mobile=True)
    await pg.click('text=IR AL JUEGO')
    comprobar(await pg.evaluate('document.documentElement.scrollWidth') <= 390, 'sin desplazamiento horizontal')
    comprobar(not errores, 'sin errores de JavaScript')
    await pg.close()


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        await soluciones(browser)
        await partida_guiada(browser)
        await movil(browser)
        await browser.close()
    print(f'\n{"TODO CORRECTO" if not fallos else f"{len(fallos)} FALLOS"}')
    sys.exit(1 if fallos else 0)


asyncio.run(main())
