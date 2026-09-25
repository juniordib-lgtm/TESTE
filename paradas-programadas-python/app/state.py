"""
Estado da aplicação em memória + operações de CRUD.
Port fiel de state.js (mesma lógica, mesmos nomes de campo no JSON — o que
torna o `dados-paradas.json` desta versão em Python intercambiável com o
da versão web do mesmo sistema).

`AppState.data` é sempre um dict puro, pronto para `json.dump()` sem
nenhuma etapa extra de serialização: datas são guardadas como strings ISO
8601 em UTC (ver `dates.py`), exatamente como a versão web grava.
"""

from __future__ import annotations
import uuid
from datetime import datetime, timedelta

from . import dates
from .calendar_engine import calcular_data_fim, calcular_duracao_horas, calendario_padrao

STATUS_LABELS = {
    'planejada': 'Planejada',
    'em_andamento': 'Em andamento',
    'concluida': 'Concluída',
    'atrasada': 'Atrasada',
}

STATUS_CORES = {
    'planejada': '#4338ca',
    'em_andamento': '#b45309',
    'concluida': '#15803d',
    'atrasada': '#b91c1c',
}

STATUS_CORES_CLARAS = {
    'planejada': '#e0e7ff',
    'em_andamento': '#fef3c7',
    'concluida': '#dcfce7',
    'atrasada': '#fee2e2',
}

TIPOS_RECURSO = {
    'mao_de_obra': 'Mão de obra',
    'equipamento': 'Equipamento',
    'material': 'Material',
    'servico': 'Serviço',
}


def novo_id() -> str:
    return str(uuid.uuid4())


class AppState:
    def __init__(self):
        self.data: dict = self._workspace_vazio()
        self._listeners = []
        self.on_erro = None  # callback opcional: on_erro(mensagem)
        self.on_persist = None  # callback opcional: on_persist(data) -> grava em disco

    # ---------- infraestrutura ----------

    def _workspace_vazio(self) -> dict:
        return {
            'version': 1,
            'paradaAtivaId': None,
            'paradas': [],
            'calendarios': [calendario_padrao()],
            'atividades': [],
        }

    def on_change(self, fn):
        self._listeners.append(fn)

    def _notify(self):
        for fn in list(self._listeners):
            fn()

    def _avisar(self, mensagem: str):
        if self.on_erro:
            self.on_erro(mensagem)

    def carregar(self, novo_data: dict | None):
        if novo_data and novo_data.get('paradas') is not None:
            self.data = self._migrar(novo_data)
        self._notify()

    def substituir_tudo(self, novo_data: dict):
        self.data = self._migrar(novo_data)
        self._notify()

    def _migrar(self, d: dict) -> dict:
        if not d.get('calendarios'):
            d['calendarios'] = [calendario_padrao()]
        d.setdefault('atividades', [])
        d.setdefault('paradas', [])
        d.setdefault('paradaAtivaId', None)
        d.setdefault('version', 1)
        for a in d['atividades']:
            a.setdefault('imagens', [])
            a.setdefault('recursos', [])
            a.setdefault('progresso', 0)
            a.setdefault('status', 'planejada')
            a.setdefault('inicioReal', None)
            a.setdefault('fimReal', None)
            a.setdefault('predecessoraId', None)
            a.setdefault('defasagemHoras', 0)
            a.setdefault('parentId', None)
            a.setdefault('numeroOS', '')
        return d

    def get_data(self) -> dict:
        return self.data

    # ---------- Paradas ----------

    def listar_paradas(self) -> list[dict]:
        return sorted(self.data['paradas'], key=lambda p: p.get('criadoEm') or '')

    def get_parada(self, id_: str | None) -> dict | None:
        if not id_:
            return None
        return next((p for p in self.data['paradas'] if p['id'] == id_), None)

    def get_parada_ativa(self) -> dict | None:
        return self.get_parada(self.data.get('paradaAtivaId'))

    def set_parada_ativa(self, id_: str):
        self.data['paradaAtivaId'] = id_
        self._persist()

    def salvar_parada(self, parada: dict) -> dict:
        if not parada.get('calendarioId') and self.data['calendarios']:
            parada['calendarioId'] = self.data['calendarios'][0]['id']
        idx = next((i for i, p in enumerate(self.data['paradas']) if p['id'] == parada.get('id')), -1)
        if idx >= 0:
            self.data['paradas'][idx] = parada
        else:
            parada['id'] = parada.get('id') or novo_id()
            parada['criadoEm'] = dates.agora_iso_utc()
            self.data['paradas'].append(parada)
            if not self.data.get('paradaAtivaId'):
                self.data['paradaAtivaId'] = parada['id']
        self.recalcular_programacao(parada['id'])
        self._persist()
        return parada

    def excluir_parada(self, id_: str):
        self.data['paradas'] = [p for p in self.data['paradas'] if p['id'] != id_]
        self.data['atividades'] = [a for a in self.data['atividades'] if a['paradaId'] != id_]
        if self.data.get('paradaAtivaId') == id_:
            self.data['paradaAtivaId'] = self.data['paradas'][0]['id'] if self.data['paradas'] else None
        self._persist()

    # ---------- Calendários ----------

    def listar_calendarios(self) -> list[dict]:
        return self.data['calendarios']

    def get_calendario(self, id_: str | None) -> dict:
        cal = next((c for c in self.data['calendarios'] if c['id'] == id_), None)
        return cal or self.data['calendarios'][0]

    def salvar_calendario(self, cal: dict) -> dict:
        idx = next((i for i, c in enumerate(self.data['calendarios']) if c['id'] == cal.get('id')), -1)
        if idx >= 0:
            self.data['calendarios'][idx] = cal
        else:
            cal['id'] = cal.get('id') or novo_id()
            self.data['calendarios'].append(cal)
        for p in self.data['paradas']:
            if p.get('calendarioId') == cal['id']:
                self.recalcular_programacao(p['id'])
        self._persist()
        return cal

    def excluir_calendario(self, id_: str) -> bool:
        if len(self.data['calendarios']) <= 1:
            self._avisar('É preciso manter ao menos um calendário.')
            return False
        em_uso = any(p.get('calendarioId') == id_ for p in self.data['paradas'])
        if em_uso:
            self._avisar('Este calendário está em uso por uma parada e não pode ser excluído.')
            return False
        self.data['calendarios'] = [c for c in self.data['calendarios'] if c['id'] != id_]
        self._persist()
        return True

    # ---------- Atividades ----------

    def listar_atividades_da_parada(self, parada_id: str) -> list[dict]:
        """Ordenada por Data/Hora de Início (sem data vai para o final);
        empate usa a ordem de cadastro."""
        atividades = [a for a in self.data['atividades'] if a['paradaId'] == parada_id]

        def chave(a):
            di = dates.from_iso_utc(a.get('dataInicio'))
            return (di is None, di or datetime.max, a.get('ordem') or 0)

        return sorted(atividades, key=chave)

    def arvore_atividades(self, parada_id: str) -> list[dict]:
        """Atividades de topo (sem parentId), cada uma com 'subAtividades'
        preenchido recursivamente — sem limite de profundidade."""
        todas = self.listar_atividades_da_parada(parada_id)
        por_id = {a['id']: {**a, 'subAtividades': []} for a in todas}
        raizes = []
        for a in todas:
            pai_id = a.get('parentId')
            if pai_id and pai_id in por_id:
                por_id[pai_id]['subAtividades'].append(por_id[a['id']])
            else:
                raizes.append(por_id[a['id']])
        return raizes

    def lista_achatada(self, parada_id: str) -> list[dict]:
        """Achata a árvore em uma lista [{...atividade, 'nivel': n}],
        mantendo cada sub-atividade logo após a atividade correspondente."""
        out = []

        def visitar(lista, nivel):
            for a in lista:
                resto = {k: v for k, v in a.items() if k != 'subAtividades'}
                resto['nivel'] = nivel
                out.append(resto)
                visitar(a.get('subAtividades') or [], nivel + 1)

        visitar(self.arvore_atividades(parada_id), 0)
        return out

    def get_atividade(self, id_: str | None) -> dict | None:
        if not id_:
            return None
        return next((a for a in self.data['atividades'] if a['id'] == id_), None)

    def calendario_da_atividade(self, atividade: dict) -> dict:
        parada = self.get_parada(atividade.get('paradaId'))
        return self.get_calendario(parada.get('calendarioId')) if parada else calendario_padrao()

    def duracao_real_horas(self, atividade: dict) -> float | None:
        if not atividade.get('inicioReal') or not atividade.get('fimReal'):
            return None
        cal = self.calendario_da_atividade(atividade)
        ini = dates.from_iso_utc(atividade['inicioReal'])
        fim = dates.from_iso_utc(atividade['fimReal'])
        return calcular_duracao_horas(ini, fim, cal)

    def salvar_atividade(self, atividade: dict, modo_calculo: str = 'duracao') -> dict:
        """Salva uma atividade. `modo_calculo` indica qual campo foi editado
        por último: 'duracao' (recalcula dataFim) ou 'fim' (recalcula
        duracaoHoras). Ignorado quando a atividade tem predecessora — nesse
        caso a Data Início é sempre derivada pela cadeia, em
        `recalcular_programacao` logo abaixo."""
        if not atividade.get('predecessoraId'):
            cal = self.calendario_da_atividade(atividade)
            inicio = dates.from_iso_utc(atividade.get('dataInicio'))
            if modo_calculo == 'fim' and atividade.get('dataFim'):
                fim = dates.from_iso_utc(atividade['dataFim'])
                atividade['duracaoHoras'] = calcular_duracao_horas(inicio, fim, cal)
            else:
                fim = calcular_data_fim(inicio, float(atividade.get('duracaoHoras') or 0), cal)
                atividade['dataFim'] = dates.to_iso_utc(fim)

        idx = next((i for i, a in enumerate(self.data['atividades']) if a['id'] == atividade.get('id')), -1)
        if idx >= 0:
            self.data['atividades'][idx] = atividade
        else:
            atividade['id'] = atividade.get('id') or novo_id()
            if atividade.get('ordem') is None:
                atividade['ordem'] = len(self.listar_atividades_da_parada(atividade['paradaId'])) + 1
            atividade.setdefault('imagens', [])
            atividade.setdefault('recursos', [])
            self.data['atividades'].append(atividade)

        self.recalcular_programacao(atividade['paradaId'])
        self._persist()
        return atividade

    def excluir_atividade(self, id_: str):
        alvo = self.get_atividade(id_)
        # exclui também as sub-atividades, em qualquer profundidade
        ids_excluir = {id_}
        mudou = True
        while mudou:
            mudou = False
            for a in self.data['atividades']:
                if a.get('parentId') in ids_excluir and a['id'] not in ids_excluir:
                    ids_excluir.add(a['id'])
                    mudou = True
        # atividades que dependiam de algo removido voltam a ter data/hora manual
        for a in self.data['atividades']:
            if a.get('predecessoraId') in ids_excluir:
                a['predecessoraId'] = None
        self.data['atividades'] = [a for a in self.data['atividades'] if a['id'] not in ids_excluir]
        if alvo:
            self.recalcular_programacao(alvo['paradaId'])
        self._persist()

    # ---------- Predecessoras / sucessoras ----------

    def sucessoras_diretas(self, atividade_id: str) -> list[dict]:
        return [a for a in self.data['atividades'] if a.get('predecessoraId') == atividade_id]

    def cadeia_sucessoras(self, atividade_id: str, visitados: set | None = None) -> set:
        """IDs de `atividade_id` + todas as suas sucessoras diretas/indiretas."""
        if visitados is None:
            visitados = set()
        if atividade_id in visitados:
            return visitados
        visitados.add(atividade_id)
        for s in self.sucessoras_diretas(atividade_id):
            self.cadeia_sucessoras(s['id'], visitados)
        return visitados

    # ---------- Hierarquia (sub-atividades em qualquer profundidade) ----------

    def filhos_diretos(self, atividade_id: str) -> list[dict]:
        return [a for a in self.data['atividades'] if a.get('parentId') == atividade_id]

    def cadeia_descendentes(self, atividade_id: str, visitados: set | None = None) -> set:
        """IDs de `atividade_id` + todos os seus descendentes. Usado para
        impedir que uma atividade vire sub-atividade de algo que já é seu
        próprio descendente (evita laço na árvore)."""
        if visitados is None:
            visitados = set()
        if atividade_id in visitados:
            return visitados
        visitados.add(atividade_id)
        for f in self.filhos_diretos(atividade_id):
            self.cadeia_descendentes(f['id'], visitados)
        return visitados

    def recalcular_programacao(self, parada_id: str):
        """Recalcula Data Início/Fim de todas as atividades de uma parada,
        respeitando a cadeia de predecessoras: quem tem predecessora tem sua
        Data Início derivada automaticamente de "Data Fim da predecessora +
        defasagem"; quem não tem predecessora mantém a Data Início digitada
        manualmente. Percorre a cadeia em profundidade (predecessora antes
        de sucessora) para propagar mudanças em cascata, protegendo contra
        referência circular."""
        parada = self.get_parada(parada_id)
        calendario = self.get_calendario(parada.get('calendarioId')) if parada else calendario_padrao()
        todas = self.listar_atividades_da_parada(parada_id)
        por_id = {a['id']: a for a in todas}
        processadas = set()

        def processar(a: dict, pilha: set):
            if a is None or a['id'] in processadas or a['id'] in pilha:
                return
            pilha = pilha | {a['id']}
            pred_id = a.get('predecessoraId')
            if pred_id and pred_id in por_id:
                pred = por_id[pred_id]
                processar(pred, pilha)
                if pred.get('dataFim'):
                    lag = float(a.get('defasagemHoras') or 0)
                    pred_fim = dates.from_iso_utc(pred['dataFim'])
                    novo_inicio = pred_fim + timedelta(hours=lag)
                    a['dataInicio'] = dates.to_iso_utc(novo_inicio)

            inicio = dates.from_iso_utc(a.get('dataInicio'))
            fim = calcular_data_fim(inicio, float(a.get('duracaoHoras') or 0), calendario) if inicio else None
            a['dataFim'] = dates.to_iso_utc(fim)
            processadas.add(a['id'])

        for a in todas:
            processar(a, set())

    # ---------- Estatísticas ----------

    def faixa_data_parada(self, parada_id: str) -> tuple[datetime | None, datetime | None]:
        atividades = self.listar_atividades_da_parada(parada_id)
        inicio = fim = None
        for a in atividades:
            di = dates.from_iso_utc(a.get('dataInicio'))
            df = dates.from_iso_utc(a.get('dataFim'))
            if di and (inicio is None or di < inicio):
                inicio = di
            if df and (fim is None or df > fim):
                fim = df
        return inicio, fim

    def calcular_estatisticas(self, parada_id: str) -> dict:
        atividades = self.listar_atividades_da_parada(parada_id)
        total = len(atividades)
        por_status = {k: 0 for k in STATUS_LABELS}
        progresso_soma = 0.0
        horas_totais = 0.0
        recursos_por_tipo: dict[str, float] = {}
        custo_total = 0.0

        for a in atividades:
            por_status[a.get('status', 'planejada')] = por_status.get(a.get('status', 'planejada'), 0) + 1
            progresso_soma += float(a.get('progresso') or 0)
            horas_totais += float(a.get('duracaoHoras') or 0)
            for r in a.get('recursos') or []:
                tipo = r.get('tipo') or 'outro'
                recursos_por_tipo[tipo] = recursos_por_tipo.get(tipo, 0) + float(r.get('quantidade') or 0)
                custo_total += float(r.get('quantidade') or 0) * float(r.get('custoUnitario') or 0)

        progresso_medio = round(progresso_soma / total, 1) if total else 0
        inicio, fim = self.faixa_data_parada(parada_id)
        duracao_total_horas = round((fim - inicio).total_seconds() / 3600, 1) if inicio and fim else None

        return {
            'total': total,
            'porStatus': por_status,
            'progressoMedio': progresso_medio,
            'horasTotais': horas_totais,
            'recursosPorTipo': recursos_por_tipo,
            'custoTotal': custo_total,
            'inicio': inicio,
            'fim': fim,
            'duracaoTotalHoras': duracao_total_horas,
        }

    # ---------- Persistência ----------

    def _persist(self):
        if self.on_persist:
            self.on_persist(self.data)
        self._notify()
