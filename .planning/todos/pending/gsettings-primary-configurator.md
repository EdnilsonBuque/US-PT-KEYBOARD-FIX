---
title: Implementar configurador via gsettings em vez de setxkbmap
date: 2026-11-21
priority: high
status: pending
related: REQ-005, .planning/notes/gnome-wayland-keyboard-mechanisms.md
---

# Implementar configurador via `gsettings` em vez de `setxkbmap`

## O que

Reescrever o caminho de configuração de `configurator.py` e o caminho de diagnóstico de
`diagnostic.py` para usar `gsettings org.gnome.desktop.input-sources` como mecanismo primário,
com `setxkbmap` reduzido a fallback de sessões X11.

## Porquê

Verificado na pesquisa de 2026-11-21: `setxkbmap` sob Wayland produz
`WARNING: Running setxkbmap against an Xwayland server` e não tem efeito sobre o keymap real
da sessão. Isto é a causa raiz de "as configurações desaparecem após reiniciar" — a ferramenta
aparenta funcionar no arranque atual e perde tudo a seguir.

`gsettings` escreve em dconf e persiste através de reinícios.

## Tarefas

- [ ] Criar função de aplicação que escreve `sources` e `xkb-options` via `gsettings`, preservando
      os layouts já existentes do utilizador (acrescentar, nunca substituir).
- [ ] Detetar tipo de sessão (`XDG_SESSION_TYPE` / `WAYLAND_DISPLAY`) **antes** de escolher o
      mecanismo.
- [ ] Manter `setxkbmap` apenas como caminho para sessões X11, com aviso claro.
- [ ] Em `diagnostic.py`, sinalizar `setxkbmap`-sob-Wayland como problema encontrado, com a
      solução recomendada.
- [ ] Teste unitário: mock de `gsettings` verifica que o comando gerado é uma lista de argumentos
      (sem `shell=True`) e que os layouts existentes são preservados.
- [ ] Teste de integração: verificar persistência após `gsettings reset` simulado.

## Critério de aceitação

- `uspt configure` num GNOME Wayland produz configuração que sobrevive a reinício.
- Nenhum layout pré-existente do utilizador é removido.
- Nenhum comando usa `shell=True`.

## Nota

Não afirmar que foi testado em Wayland sem executar efetivamente o teste na sessão Wayland.
