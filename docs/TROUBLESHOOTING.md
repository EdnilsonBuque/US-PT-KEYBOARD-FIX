# Resolução de Problemas

## Problemas comuns

### "setxkbmap: WARNING: Running setxkbmap against an Xwayland server"

**Causa:** Está a usar uma sessão Wayland. `setxkbmap` apenas afeta o Xwayland e não persiste across reboots.

**Solução:** Use `uspt configure` em vez de comandos `setxkbmap` manual. A ferramenta usará `gsettings` que persiste em dconf.

### "Comando gsettings não encontrado"

**Causa:** Não está num ambiente GNOME, ou `gsettings` não está instalado.

**Solução:** Esta versão (v1) suporta apenas ambientes GNOME. Em outros ambientes, a configuração terá de ser feita manualmente ou mediante atualização da ferramenta.

### "Layout português não afeta alguns aplicativos"

**Causa:** O ficheiro `~/.Xcompose` não é lido por todas as aplicações:
- Chromium/Electron Wayland nativo: ignora completamente.
- GTK4 ≥ 4.19/4.20: usa IME, pode não ler o ficheiro.
- Algumas aplicações Qt antigas têm suporte limitado.

**Solução:** Mude para a Modalidade B (AltGr) que funciona em todas as aplicações através do XKB:
```bash
uspt configure --modalidade altgr
```

### "Não consigo restaurar o backup"

**Causa:** O diretório de backup foi removido ou corrompido.

**Solução:** Verifique se `~/.local/share/uspt-backup/` existe. Se foi removido, não há como restaurar aquele snapshot. backups futuros serão criados a partir do estado atual.

### "Os caracteres acentuados deixam de funcionar após reiniciar"

**Causa:** Provavelmente as configurações foram feitas com `setxkbmap` em sessão Wayland, que não persiste.

**Solução:** Re-aplique com `uspt configure --modalidade altgr`, que usa `gsettings` em dconf e persiste através de reinícios.

## Verificar sessão

```bash
# Ver se está em Wayland ou X11
echo "WAYLAND_DISPLAY: $WAYLAND_DISPLAY"
echo "XDG_SESSION_TYPE: $XDG_SESSION_TYPE"

# Se WAYLAND_DISPLAY estiver definido, está em Wayland.
# Se estiver vazio ou X11, está em X11.
```

## Logs detalhados

Para depuração, pode aumentar o nível de log:

```bash
USPT_LOG_LEVEL=DEBUG uspt diagnose
```
ou edite temporariamente o ficheiro de log.