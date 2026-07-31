package br.com.zapagendado.agenda

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import br.com.zapagendado.data.AppDatabase
import br.com.zapagendado.data.Repeticao
import br.com.zapagendado.data.Status
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

/** Alarmes morrem quando o aparelho reinicia. Aqui todos voltam. */
class BootReceiver : BroadcastReceiver() {

    override fun onReceive(context: Context, intent: Intent) {
        val pending = goAsync()
        CoroutineScope(Dispatchers.IO).launch {
            try {
                val dao = AppDatabase.get(context).dao()
                val agora = System.currentTimeMillis()

                dao.pendentes().forEach { item ->
                    when {
                        item.quandoMillis > agora -> Agendador.agendar(context, item)

                        // Passou da hora enquanto o aparelho estava desligado
                        item.repeticao != Repeticao.NUNCA -> {
                            val proxima = Agendador.proximaOcorrencia(item.quandoMillis, item.repeticao)
                            if (proxima != null) {
                                val atualizado = item.copy(quandoMillis = proxima)
                                dao.atualizar(atualizado)
                                Agendador.agendar(context, atualizado)
                            }
                        }

                        else -> dao.mudarStatus(item.id, Status.FALHOU)
                    }
                }
            } finally {
                pending.finish()
            }
        }
    }
}
