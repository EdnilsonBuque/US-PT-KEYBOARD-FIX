# Como contribuir com o US-PT Keyboard Fix

## 🌟 Obrigado por considerar contribuir!

Qualquer tipo de contribuição é bem-vinda: desde da correção de bugs e melhorias de documentação até novas funcionalidades e testes.

## 📋 Diretrizes

### 1. Fork and branch
```bash
git fork https://github.com/EdnilsonBuque/US-PT-KEYBOARD-FIX.git
git checkout -b feature/minha-contribuicao
```

### 2. Commit conventions
Use mensagens de commit claras. Exemplo:
```
git commit -m "feat: add AltGr modality option to configure command"
git commit -m "fix: resolve issue with backup restore on Wayland"
git commit -m "doc: update INSTALLATION.md with new install method"
```

### 3. Pull Request
- Preencha o template do PR.
- Certifique-se de que os testes passam.
- Documente novas funcionalidades.
- Não quebre a funcionalidade existente sem aviso.

## 🛠️ Desenvolvimento

### Setup local
```bash
# Clonar
git clone https://github.com/EdnilsonBuque/US-PT-KEYBOARD-FIX.git
cd us-pt-keyboard-fix

# Instalar dependências
pip3 install -e ".[dev]"

# Executar testes
pytest

# Verificar lint
flake8 src/uspt/
black src/uspt/
```

### Padrões de código
- Follow [PEP 8](https://pep8.org/).
- Use type hints (`from typing import Any, Dict, List, Optional`).
- Docstrings em funções públicas.
- Sem `shell=True` em subprocessos (usar lista de argumentos).
- Backups antes de qualquer escrita.
- Mensagens de erro acionáveis.

### Novas funcionalidades
1. Discuta a ideia em uma Issue antes de implementar (opcional, mas recomendado).
2. Implemente a funcionalidade.
3. Adicione testes unitários e de integração.
4. Atualize a documentação (USAGE.md, INSTALLATION.md, TROUBLESHOOTING.md).
5. Execute `make lint` e `make test`.
6. Crie um Pull Request.

## � Bug reports

Use o modelo da Issue para reportar bugs:
- Descreva o problema de forma clara.
- Inclua o output de `uspt diagnose`.
- Mencione a distribuição Linux, ambiente gráfico e tipo de sessão (Wayland/X11).
- Passos para reproduzir.

## 📝 Nova língua / localização

Se quiser adicionar suporte a novas línguas nos mensajes ou documentos:
1. Adicione strings no ficheiro `src/uspt/utils.py` ou nos docs.
2. Mantenha a consistência com o inglês.
3. Teste a renderização em diferentes localidades.

## 📄 Licença

Ao contribuir, você concorda que suas contribuições serão licenciadas sob a [licença MIT](LICENSE).

---

## 🏗️ Roadmap (visão geral)

- **v1**: GNOME only, AltGr modality (completed).
- **v2**: KDE Plasma e XFCE support (triggered by user demand).
- **v3**: Histórico de configurações avançado, mais modalidades.
- **Futuro**: Suporte a múltiplos ambientes, interface gráfica opcional.

Ver [.planning/seeds/kde-xfce-support.md] para quando o suporte a KDE/XFCE será acordado.