package br.com.zapagendado.data

import androidx.room.Dao
import androidx.room.Delete
import androidx.room.Insert
import androidx.room.Query
import androidx.room.Update
import kotlinx.coroutines.flow.Flow

@Dao
interface AgendamentoDao {

    @Query("SELECT * FROM agendamentos ORDER BY quando_millis ASC")
    fun observarTodos(): Flow<List<Agendamento>>

    @Query("SELECT * FROM agendamentos WHERE status = 'PENDENTE' ORDER BY quando_millis ASC")
    suspend fun pendentes(): List<Agendamento>

    @Query("SELECT * FROM agendamentos WHERE id = :id")
    suspend fun porId(id: Long): Agendamento?

    @Insert
    suspend fun inserir(item: Agendamento): Long

    @Update
    suspend fun atualizar(item: Agendamento)

    @Delete
    suspend fun remover(item: Agendamento)

    @Query("UPDATE agendamentos SET status = :status WHERE id = :id")
    suspend fun mudarStatus(id: Long, status: Status)

    @Query("DELETE FROM agendamentos WHERE status IN ('ENVIADO','CANCELADO','FALHOU')")
    suspend fun limparConcluidos()
}
