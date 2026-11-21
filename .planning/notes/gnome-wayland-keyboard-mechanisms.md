---
title: Mecanismos de teclado em GNOME/Wayland
date: 2026-11-21
context: US-PT Keyboard Fix — pesquisa prévia à FASE 2 (deteção) e FASE 3 (configuração XKB/XCompose)
---

# Mecanismos de teclado em GNOME/Wayland

Achados de pesquisa e verificação local (GNOME 50.1, sessão Wayland, layout `us`).
Todos os pontos marcados como **Verificado** foram confirmados na máquina de desenvolvimento.

## 1. `setxkbmap` não funciona em Wayland

**Verificado.** Executar `setxkbmap` sob Wayland produz:

```
WARNING: Running setxkbmap against an Xwayland server.
```

O comando altera o keymap do Xwayland, que é isolado do keymap real da sessão. Não tem efeito
durável nem visível nas aplicações Wayland.

**Consequência para o projeto:** `setxkbmap` não pode ser o mecanismo primário. Pode ser usado
apenas como caminho de fallback em sessões X11, e a deteção do tipo de sessão tem de preceder
qualquer tentativa de configuração.

## 2. O mecanismo fiável é `gsettings` sobre dconf

**Verificado.** `org.gnome.desktop.input-sources` persiste em dconf através de reinícios.

Isto é a causa raiz do problema "as configurações desaparecem após reiniciar": ferramentas que
usam `setxkbmap` parecem funcionar na sessão atual e perdem tudo no próximo arranque.

Comandos relevantes:

```bash
gsettings get org.gnome.desktop.input-sources sources
gsettings get org.gnome.desktop.input-sources xkb-options
gsettings set org.gnome.desktop.input-sources sources "[('xkb', 'us')]"
gsettings set org.gnome.desktop.input-sources xkb-options "['compose:ralt']"
```

**Consequência para o projeto:** `configurator.py` e `diagnostic.py` têm de tratar `gsettings`
como caminho primário em GNOME, com `localectl`/`setxkbmap` apenas como fallbacks em
ambientes não-GNOME ou X11.

## 3. `~/.Xcompose` — quem o lê realmente

**Verificado na documentação da libxkbcommon** (`xkb_compose_table_new_from_locale()`):

Ordem de procura: `XCOMPOSEFILE` → `$XDG_CONFIG_HOME/XCompose` → `$HOME/.Xcompose`.

| Cliente | Lê `~/.Xcompose` |
|---|---|
| GTK3, Qt6, terminais baseados em libxkbcommon | **Sim**, incluindo em Wayland |
| Aplicações X11 via XIM/libX11 | **Sim** |
| Chromium / Electron em Wayland nativo | **Não** — usa tabela CharacterComposer própria |
| GTK4 ≥ 4.19/4.20 | **Incerto** — delega teclas mortas ao IME (text-input-v3) |

O mutter **não** aplica XCompose a ninguém. A compose é sempre resolvida por cliente.

**Consequência para o projeto:** o `.Xcompose` é um suplemento opcional, nunca a base da
configuração. A ferramenta não pode prometer que todos os programas respeitam um mapeamento
XCompose, e o diagnóstico deve dizer isso explicitamente.

## 4. Causa raiz do problema ç → ć

**Verificado** em `/usr/share/X11/locale/en_US.UTF-8/Compose`, linha 575:

```
dead_acute <c> : "ć"  # LATIN SMALL LETTER C WITH ACUTE
```

Com locale `en_US`, a tecla morta de acento agudo combinada com `c` produz **ć**, nunca `ç`.
Não há opção XKB que mude isto — o Compose é independente do layout.

Soluções reais, por ordem de fiabilidade:

1. **AltGr + `,` → `ç` diretamente.** Mapeado em `/usr/share/X11/xkb/symbols/us` para
   `us(intl)`. Não passa pelo Compose, logo não sofre do problema acima. **Caminho preferido.**
2. Locale `pt_BR`, que define `dead_acute + c → ç`.
3. Ficheiro `~/.Xcompose` próprio, que sobrescreve o default — mas só para clientes que o leem
   (ver ponto 3).

**Consequência para o projeto:** a Modalidade B (AltGr) é o modo por omissão. A Modalidade A
(teclas mortas) só é fiável quando combinada com um `~/.Xcompose` próprio, e a ferramenta tem
de avisar das suas limitações.

## 5. Estado da máquina de desenvolvimento

- GNOME 50.1, sessão Wayland
- `sources=[('xkb', 'us')]`
- `~/.Xcompose` presente

## Incertezas em aberto

- Comportamento exato do GTK4 ≥ 4.19 com compose — só testável empíricamente.
- Nada foi testado em Fedora, KDE ou XFCE. Não afirmar suporte sem executar os testes.
