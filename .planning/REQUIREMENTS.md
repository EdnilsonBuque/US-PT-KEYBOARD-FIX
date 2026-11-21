# Requisitos — US-PT Keyboard Fix

Requisitos derivados da especificação do projeto e da sessão de exploração de 2026-11-21.

---

## REQ-001 — Público-alvo da v1: publicação no GitHub

A primeira versão é publicada como Open Source e destinada a desconhecidos. O instalador, o
desinstalador e as mensagens de erro têm de estar preparados desde o primeiro commit.

**Critérios:**
- Instalador com verificação de dependências e mensagens claras.
- Desinstalador que remove apenas ficheiros pertencentes ao projeto.
- Mensagens de erro acionáveis, sem jargão assumido.
- Nenhum endereço GitHub inventado — URL configurável até existir repositório real.

**Origem:** sessão de exploração, 2026-11-21.

---

## REQ-002 — Ambiente gráfico suportado na v1: apenas GNOME

A v1 suporta exclusivamente GNOME. Ambientes não suportados são detetados e recusados
educadamente, em vez de tentar aplicar configurações.

**Critérios:**
- Deteção correta de GNOME vs KDE vs XFCE vs outros.
- Em ambiente não-GNOME, a ferramenta explica a limitação e não altera nada.
- Cobre Ubuntu, Debian, Linux Mint e Fedora nas suas variantes GNOME.

**Origem:** sessão de exploração, 2026-11-21. Reduz em cerca de metade a superfície de
aplicação e reversão.

---

## REQ-003 — Modelo de backup: snapshot por alteração

Antes de cada alteração, a ferramenta copia os ficheiros que vai modificar para um diretório
com timestamp. Restaurar significa voltar atrás na última alteração.

**Critérios:**
- Um snapshot antes de cada operação de escrita.
- Cada snapshot regista: timestamp, ficheiros tocados, comando executado, resultado.
- Restauração limitada ao último snapshot, com verificação de integridade (hash).
- Nunca sobrescrever um snapshot existente.

**Origem:** sessão de exploração, 2026-11-21. Histórico completo fica para versão futura.

---

## REQ-004 — Modo por omissão: AltGr

Quando o utilizador executa a configuração de caracteres portugueses sem escolher, aplica-se
a Modalidade B (AltGr).

**Critérios:**
- `ç` produzido por AltGr + `,` diretamente, sem passar pelo Compose.
- Não altera o comportamento de teclas comuns como `'`, `^`, `` ` ``.
- A Modalidade A (teclas mortas) continua disponível como escolha explícita do utilizador.
- A ferramenta nunca afirma que a Modalidade A funciona em todos os programas.

**Racional:** ver `.planning/notes/gnome-wayland-keyboard-mechanisms.md` — o Compose default
`en_US` produz `ć` em vez de `ç`, pelo que a via teclas mortas é inerentemente menos robusta.

**Origem:** sessão de exploração, 2026-11-21.

---

## REQ-005 — Mecanismo primário de configuração: `gsettings`/dconf

A configuração de layout em GNOME tem de usar `org.gnome.desktop.input-sources` via
`gsettings`. `setxkbmap` não é válido em Wayland.

**Critérios:**
- `configurator.py` usa `gsettings` como caminho primário.
- `setxkbmap` é fallback apenas em sessões X11, e só após deteção do tipo de sessão.
- A configuração persiste através de reinícios (verificado em dconf).
- Preservar os layouts já configurados pelo utilizador — acrescentar, nunca substituir.

**Origem:** pesquisa técnica, 2026-11-21.

---

## REQ-006 — Nunca afirmar deteção não verificada

A ferramenta nunca afirma que detetou o teclado físico, o ambiente, ou o sucesso de um teste
que não foi efetivamente executado.

**Critérios:**
- Layout físico só é reportado se houver fonte real de informação.
- Mensagens distinguem claramente "detetado", "assumido" e "não disponível".
- Testes em Wayland/X11/distribuições só são alegados se executados.

**Origem:** especificação do projeto, secção 14 — critério de aceitação implícito e regra
de honestidade explícita.
