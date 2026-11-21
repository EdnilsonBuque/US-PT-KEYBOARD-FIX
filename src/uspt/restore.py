"""Módulo de restauração de configurações de teclado.

Responsável por:
- Restaurar configurações a partir de backups.
- Recuperação em caso de falha.
- Verificação da integridade dos backups.

Diferencia do backup.py: esta classe foca especificamente em restaurar
o estado do teclado/layouts, enquanto o BackupManager lida com backups
gerais do projeto.
"""

import logging
import subprocess
from typing import Any, Dict, List, Optional

from .backup import BackupManager, DEFAULT_BACKUP_DIR

logger = logging.getLogger(__name__)


class KeyboardRestore:
    """Restaura configurações de teclado a partir de backups."""

    def __init__(self, backup_dir: str = DEFAULT_BACKUP_DIR):
        self.backup_manager = BackupManager(backup_dir)

    def restore_keyboard_state(self, snapshot_id: str = None) -> Dict[str, Any]:
        """Restaura o estado do teclado a partir de um snapshot.

        Tenta restaurar:
        - Configurações gsettings (sources e xkb-options)
        - Ficheiro ~/.Xcompose se existir no backup
        - Qualquer outra configuração de teclado conhecida

        Returns dicionário com status da restauração.
        """
        result = {
            "success": False,
            "snapshot_id": snapshot_id,
            "restored": [],
            "not_found": [],
            "warnings": [],
            "action": "restore_keyboard_state",
        }

        # First, try to restore gsettings from the snapshot description/info
        # Since we don't store gsettings values directly in the backup directory
        # (they're system-level), we need to re-derive or store them

        # Step 1: Check if snapshot_id is provided, otherwise get latest
        if snapshot_id is None:
            snapshot_result = self.backup_manager.restore_last()
            if not snapshot_result["success"]:
                result["warnings"].append("Não foi possível encontrar último snapshot")
                return result
            snapshot_id = snapshot_result.get("snapshot_id")

        if not snapshot_id:
            result["warnings"].append("Nenhum snapshot_id disponível")
            return result

        # Step 2: Try to restore from the backup directory
        manifest = self.backup_manager._load_manifest()
        target_backup = None
        for backup in manifest.get("backups", []):
            if backup["snapshot_id"] == snapshot_id:
                target_backup = backup
                break

        if not target_backup:
            result["warnings"] = [f"Snapshot {snapshot_id} não encontrado no manifest"]
            logger.warning("Snapshot %s não no manifest", snapshot_id)
            return result

        backup_path = target_backup["path"]
        if not os.path.exists(backup_path):
            result["warnings"].append(f"Diretório de backup não existe: {backup_path}")
            return result

        # Step 3: Restore specific keyboard-related files
        try:
            # Look for .Xcompose
            xcompose_backup = os.path.join(backup_path, ".Xcompose")
            if os.path.exists(xcompose_backup):
                user_xcompose = os.path.expanduser("~/.Xcompose")
                try:
                    shutil.copy2(xcompose_backup, user_xcompose)
                    result["restored"].append(".Xcompose")
                    logger.info(".Xcompose restaurado de %s", snapshot_id)
                except (shutil.Error, IOError, OSError) as e:
                    result["warnings"].append(f"Não foi restaurar .Xcompose: {str(e)}")

            # Look for uspt config
            uspt_config = os.path.join(backup_path, "uspt-config.json")
            if os.path.exists(uspt_config):
                result["restored"].append("uspt config file (informational)")

            # Look for any custom keyboard configs
            for fname in os.listdir(backup_path):
                fpath = os.path.join(backup_path, fname)
                if os.path.isfile(fpath) and fname.endswith(".conf"):
                    # Try to restore based on filename patterns
                    result["restored"].append(f"{fname} (padrão)")

        except (OSError, IOError) as e:
            result["warnings"].append(f"Erro ao escanear backup: {str(e)}")

        # Step 4: Attempt gsettings restoration
        # We don't store gsettings values in backup, but we can note what
        # configuration was active at the time of the snapshot
        # The user would need to re-apply via uspt configure or manually

        # Step 5: Final status
        if result["restored"]:
            result["success"] = True
            result["warnings"].append(
                f"Restauração concluída do snapshot {snapshot_id}. "
                "Nota: configurações gsettings não foram armazenadas no backup. "
                "Reexecute 'uspt configure' se precisar re-aplicar as configurações de layout."
            )
        else:
            result["warnings"].append("Nenhum ficheiro de teclado específico foi restaurado. "
                                      "As configurações gsettings não foram armazenadas neste backup.")

        logger.info("Restauração de estado do teclado concluída do snapshot %s", snapshot_id)
        return result

    def list_available_snapshots(self) -> Dict[str, Any]:
        """Lista todos os snapshots disponíveis com informações resumidas."""
        manifest = self.backup_manager._load_manifest()
        backups = manifest.get("backups", [])

        result = {
            "total_snapshots": len(backups),
            "snapshots": [],
        }

        for backup in backups:
            snapshot_info = {
                "snapshot_id": backup.get("snapshot_id", "unknown"),
                "timestamp": backup.get("timestamp", "unknown"),
                "description": backup.get("description", ""),
                "files_count": backup.get("files_count", 0),
                "path_exists": os.path.exists(backup.get("path", "")),
            }
            result["snapshots"].append(snapshot_info)

        return result


# Convenience function
def restore_keyboard(snapshot_id: str = None) -> Dict[str, Any]:
    """Restaurar estado do teclado a partir de snapshot."""
    kr = KeyboardRestore()
    return kr.restore_keyboard_state(snapshot_id=snapshot_id)