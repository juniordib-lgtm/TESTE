package br.com.zapagendado.ui

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import br.com.zapagendado.agenda.Agendador
import br.com.zapagendado.data.Agendamento
import br.com.zapagendado.data.AppDatabase
import br.com.zapagendado.data.Status
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

class AgendamentoViewModel(app: Application) : AndroidViewModel(app) {

    private val dao = AppDatabase.get(app).dao()

    val lista: StateFlow<List<Agendamento>> = dao.observarTodos()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())

    fun salvar(item: Agendamento) = viewModelScope.launch {
        val ctx = getApplication<Application>()
        if (item.id == 0L) {
            val id = dao.inserir(item)
            Agendador.agendar(ctx, item.copy(id = id))
        } else {
            dao.atualizar(item)
            Agendador.cancelar(ctx, item.id)
            if (item.status == Status.PENDENTE) Agendador.agendar(ctx, item)
        }
    }

    fun cancelar(item: Agendamento) = viewModelScope.launch {
        Agendador.cancelar(getApplication(), item.id)
        dao.mudarStatus(item.id, Status.CANCELADO)
    }

    fun reativar(item: Agendamento) = viewModelScope.launch {
        if (item.quandoMillis <= System.currentTimeMillis()) return@launch
        dao.mudarStatus(item.id, Status.PENDENTE)
        Agendador.agendar(getApplication(), item.copy(status = Status.PENDENTE))
    }

    fun remover(item: Agendamento) = viewModelScope.launch {
        Agendador.cancelar(getApplication(), item.id)
        dao.remover(item)
    }

    fun limparConcluidos() = viewModelScope.launch { dao.limparConcluidos() }
}
