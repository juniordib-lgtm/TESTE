package br.com.zapagendado.data

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.PrimaryKey

enum class Status { PENDENTE, ENVIADO, CANCELADO, FALHOU }

enum class Repeticao(val rotulo: String) {
    NUNCA("Não repete"),
    DIARIO("Todo dia"),
    SEMANAL("Toda semana"),
    MENSAL("Todo mês")
}

@Entity(tableName = "agendamentos")
data class Agendamento(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    /** Só dígitos, com DDI. Ex.: 5584999998888 */
    val numero: String,
    val nomeContato: String = "",
    val mensagem: String,
    @ColumnInfo(name = "quando_millis") val quandoMillis: Long,
    val status: Status = Status.PENDENTE,
    val repeticao: Repeticao = Repeticao.NUNCA,
    /** true = WhatsApp Business (com.whatsapp.w4b) */
    val business: Boolean = false,
    /** true = tenta tocar em enviar sozinho (exige serviço de acessibilidade ligado) */
    val autoEnviar: Boolean = false
)
