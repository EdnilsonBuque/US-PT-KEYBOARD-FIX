---
title: Suporte a KDE Plasma e XFCE
trigger_condition: Quando surgirem pedidos de utilizadores no GitHub, ou quando a v1 (apenas GNOME) estiver estável e publicada.
planted_date: 2026-11-21
status: dormant
related: REQ-002
---

# Suporte a KDE Plasma e XFCE

## Ideia

Alargar o suporte de ambientes gráficos para além do GNOME, mantendo a mesma arquitetura de
deteção → diagnóstico → aplicação → snapshot → reversão.

## Porque é uma seed e não uma fase

A decisão de restringir a v1 a apenas GNOME foi tomada deliberadamente na sessão de exploração
de 2026-11-21: reduz para cerca de metade a superfície de aplicação e de reversão, e elimina os
caminhos onde uma ferramenta mal construída apaga configuração do utilizador.

## O que implica quando acordar

Cada ambiente guarda a configuração do teclado num sítio diferente:

| Ambiente | Mecanismo | Ficheiro/origem |
|---|---|---|
| GNOME | `gsettings` | `org.gnome.desktop.input-sources` (dconf) |
| KDE Plasma | `kwriteconfig5` / `kxkbrc` | `~/.config/kxkbrc` |
| XFCE | `xfconf-query` | `/xfce4/keyboard-layout` |

Implicações:

- Uma implementação por ambiente, isolada atrás de uma interface comum.
- Testes de reversão **por ambiente** — o snapshot tem de saber o que copiar em cada caso.
- Deteção tem de correr antes de qualquer escrita, e recusar ambientes não implementados.
- A matriz de testes passa a ser 3× maior; considerar CI com múltiplas imagens.

## Pré-condições antes de acordar

- [ ] v1 publicada e estável em GNOME.
- [ ] Mecanismo de deteção de ambiente já abstraído o suficiente para adicionar backends.
- [ ] Cobertura de testes do módulo de aplicação suficiente para detetar regressões.
- [ ] Disponibilidade real de uma máquina/VM com KDE e outra com XFCE para testes efetivos.

## Regra de honestidade

Não afirmar suporte a KDE ou XFCE sem executar testes efetivos nessas sessões. A regra
REQ-006 aplica-se integralmente.
