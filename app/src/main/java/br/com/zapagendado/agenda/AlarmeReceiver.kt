package br.com.zapagendado.agenda

import android.app.NotificationManager
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.Build
import androidx.core.app.NotificationCompat
import br.com.zapagendado.ZapApp
import br.com.zapagendado.data.AppDatabase
import br.com.zapagendado.data.Repeticao
import br.com.zapagendado.data.Status
import br.com.zapagendado.data.Telefone
import br.com.zapagendado.envio.EnvioActivity
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

/**
 * Acordado pelo AlarmManager na hora marcada.
 *
 * Faz duas coisas ao mesmo tempo, de propósito:
 *  1. tenta abrir a EnvioActivity direto (funciona porque o app fica na lista de
 *     dispensa temporária enquanto processa um alarme exato);
 *  2. publica uma notificação de tela cheia como rede de segurança, caso o
 *     sistema bloqueie a abertura em segundo plano.
 */
class AlarmeReceiver : BroadcastReceiver() {

    override fun onReceive(context: Context, intent: Intent) {
        val id = intent.getLongExtra(Agendador.EXTRA_ID, -1L)
        if (id <= 0) return

        val pending = goAsync()
        CoroutineScope(Dispatchers.IO).launch {
            try {
                val dao = AppDatabase.get(context).dao()
                val item = dao.porId(id) ?: return@launch
                if (item.status != Status.PENDENTE) return@launch

                val abrir = EnvioActivity.intent(context, item)

                // 1) tentativa direta
                runCatching { context.startActivity(abrir) }

                // 2) rede de segurança
                notificar(context, item.id, item.nomeContato.ifBlank { Telefone.formatarBonito(item.numero) }, item.mensagem, abrir)

                // Marca como enviado e reagenda se for recorrente
                dao.mudarStatus(item.id, Status.ENVIADO)
                val proxima = Agendador.proximaOcorrencia(item.quandoMillis, item.repeticao)
                if (item.repeticao != Repeticao.NUNCA && proxima != null) {
                    val novo = item.copy(id = 0, quandoMillis = proxima, status = Status.PENDENTE)
                    val novoId = dao.inserir(novo)
                    Agendador.agendar(context, novo.copy(id = novoId))
                }
            } finally {
                pending.finish()
            }
        }
    }

    private fun notificar(ctx: Context, id: Long, contato: String, texto: String, abrir: Intent) {
        val pi = PendingIntent.getActivity(
            ctx, id.toInt(), abrir,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val n = NotificationCompat.Builder(ctx, ZapApp.CANAL_DISPARO)
            .setSmallIcon(android.R.drawable.ic_dialog_email)
            .setContentTitle("Hora de enviar para $contato")
            .setContentText(texto.take(80))
            .setStyle(NotificationCompat.BigTextStyle().bigText(texto))
            .setPriority(NotificationCompat.PRIORITY_MAX)
            .setCategory(NotificationCompat.CATEGORY_ALARM)
            .setContentIntent(pi)
            .setFullScreenIntent(pi, true)
            .setAutoCancel(true)
            .addAction(android.R.drawable.ic_menu_send, "Abrir WhatsApp", pi)
            .build()

        val nm = ctx.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU ||
            ctx.checkSelfPermission(android.Manifest.permission.POST_NOTIFICATIONS) ==
            android.content.pm.PackageManager.PERMISSION_GRANTED
        ) {
            nm.notify(id.toInt(), n)
        }
    }
}
