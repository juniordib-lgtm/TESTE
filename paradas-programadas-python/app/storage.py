"""
Persistência em disco: pasta de trabalho, arquivo de dados e backups.

Diferente da versão web (que precisa da File System Access API do
navegador, com toda a dança de pedir permissão de novo a cada sessão),
aqui o acesso ao sistema de arquivos é nativo — então isto é bem mais
simples e robusto: a última pasta usada fica gravada num arquivo de
configuração no diretório do usuário e é reaberta automaticamente na
próxima vez, sem qualquer novo diálogo ou permissão.
"""

from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path

NOME_ARQUIVO_DADOS = 'dados-paradas.json'
NOME_PASTA_CONFIG = '.paradas_programadas'
NOME_ARQUIVO_CONFIG = 'config.json'


def pasta_config() -> Path:
    p = Path.home() / NOME_PASTA_CONFIG
    p.mkdir(parents=True, exist_ok=True)
    return p


def pasta_padrao() -> Path:
    """Pasta de trabalho usada quando o usuário ainda não escolheu nenhuma."""
    p = Path.home() / 'ParadasProgramadas'
    p.mkdir(parents=True, exist_ok=True)
    return p


def _arquivo_config() -> Path:
    return pasta_config() / NOME_ARQUIVO_CONFIG


def carregar_config() -> dict:
    caminho = _arquivo_config()
    if not caminho.exists():
        return {}
    try:
        return json.loads(caminho.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError):
        return {}


def salvar_config(config: dict):
    _arquivo_config().write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding='utf-8')


def obter_ultima_pasta() -> Path | None:
    caminho = carregar_config().get('ultimaPasta')
    if not caminho:
        return None
    p = Path(caminho)
    return p if p.is_dir() else None


def definir_ultima_pasta(pasta: Path):
    config = carregar_config()
    config['ultimaPasta'] = str(pasta)
    salvar_config(config)


def caminho_dados(pasta: Path) -> Path:
    return pasta / NOME_ARQUIVO_DADOS


def workspace_tem_dados(pasta: Path) -> bool:
    return caminho_dados(pasta).exists()


def carregar_workspace(pasta: Path) -> dict | None:
    caminho = caminho_dados(pasta)
    if not caminho.exists():
        return None
    try:
        return json.loads(caminho.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError):
        return None


def salvar_workspace(pasta: Path, data: dict):
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = caminho_dados(pasta)
    tmp = caminho.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    tmp.replace(caminho)  # escrita atômica: evita corromper o arquivo se a app fechar no meio


def sugerir_nome_backup() -> str:
    ts = datetime.now().strftime('%Y-%m-%d-%H%M')
    return f'paradas-programadas-backup-{ts}.json'


def exportar_json(data: dict, destino: Path):
    destino.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def importar_json(origem: Path) -> dict:
    return json.loads(origem.read_text(encoding='utf-8'))
