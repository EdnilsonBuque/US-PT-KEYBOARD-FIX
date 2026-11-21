# Como usar o US-PT Keyboard Fix

## Comandos disponíveis

### uspt detect
Deteta o sistema, ambiente gráfico, tipo de sessão e layout de teclado atual.

```bash
uspt detect
```

### uspt diagnose
Executa um diagnóstico completo e apresenta problemas e recomendações.

```bash
uspt diagnose
```

### uspt configure
Configura o teclado para escrever em português.

Opções:
- `--modalidade altgr` (padrão): Usa AltGr + , para ç/Ç. Funciona em Wayland e X11.
- `--modalidade dead_keys`: Usa teclas mortas (compose key). Pode não funcionar em todas as aplicações em Wayland.

```bash
# Usar modalidade AltGr (recomendado)
uspt configure --modalidade altgr

# Usar teclas mortas
uspt configure --modalidade dead_keys
```

### uspt status
Consulta o estado atual da configuração do teclado.

```bash
uspt status
```

### uspt backup
Faz um snapshot das configurações atuais antes de fazer alterações.

```bash
uspt backup
# Ou com descrição
uspt backup --description "Antes de testar configuração"
```

### uspt restore
Restaura a última configuração a partir do backup mais recente.

```bash
uspt restore
# Ou especificar um snapshot
uspt restore --snapshot snapshot-20261121-143000
```

### uspt compose
Gestão do ficheiro ~/.Xcompose.

```bash
# Ver informação de compatibilidade
uspt compose --info

# Criar ficheiro XCompose
uspt compose --create

# Remover/restorar XCompose de backup
uspt compose --remove
```

### uspt altgr
Ver ou alterar configurações AltGr.

```bash
# Ver estado atual
uspt altgr

# Aplicar AltGr
uspt altgr --enable

# Remover AltGr
uspt altgr --disable
```

### uspt uninstall
Desinstala a ferramenta, removendo ficheiros do projeto.

```bash
uspt uninstall
```

### uspt --version / uspt --help
- `--version`: Mostra a versão da aplicação.
- `--help`: Mostra esta ajuda (também por comando: `uspt --help` ou `uspt {comando} --help`).

## Fluxo de trabalho típico

```bash
# 1. Detectar situação atual
uspt detect

# 2. Verificar se há problemas
uspt diagnose

# 3. Fazer backup (precaução)
uspt backup --description "Antes da primeira configuração"

# 4. Configurar para português
uspt configure --modalidade altgr

# 5. Verificar se funcionou
uspt status

# 6. (Opcional) Gerir XCompose se preferir Modalidade A
uspt compose --info
```

## Dicas

- **Wayland vs X11**: Em sessões Wayland, `setxkbmap` não persiste across reboots. Sempre use `uspt configure` que usa `gsettings` (persistente).
- **Modalidade B (AltGr)** é a recomendada para Wayland, pois não depende do ficheiro XCompose que algumas aplicações não leem.
- **Backup**: Sempre faça backup antes de configurar pela primeira vez. A restauração é feita com `uspt restore`.
- **Perfis de utilizador**: A ferramenta preserva layouts existentes. Não remove layouts que já configurou.