package br.com.zapagendado.agenda

import android.app.AlarmManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build
import br.com.zapagendado.MainActivity
import br.com.zapagendado.data.Agendamento
import java.util.Calendar

object Agendador {

    const val EXTRA_ID = "agendamento_id"

    private fun alarmManager(ctx: Context) =
        ctx.getSystemService(Context.ALARM_SERVICE) as AlarmManager

    private fun disparo(ctx: Context, id: Long): PendingIntent {
        val i = Intent(ctx, AlarmeReceiver::class.java).apply {
            action = "br.com.zapagendado.DISPARAR"
            putExtra(EXTRA_ID, id)
        }
        return PendingIntent.getBroadcast(
            ctx, id.toInt(), i,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
    }

    /** Intent que abre o app quando a pessoa toca no ícone de alarme da barra de status. */
    private fun aberturaDoApp(ctx: Context): PendingIntent {
        val i = Intent(ctx, MainActivity::class.java)
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP)
        return PendingIntent.getActivity(
            ctx, 0, i, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
    }

    fun podeAlarmeExato(ctx: Context): Boolean =
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) alarmManager(ctx).canScheduleExactAlarms()
        else true

    fun agendar(ctx: Context, item: Agendamento) {
        val am = alarmManager(ctx)
        val pi = disparo(ctx, item.id)

        if (podeAlarmeExato(ctx)) {
            // setAlarmClock é o mais confiável: fura o modo Soneca (Doze)
            am.setAlarmClock(
                AlarmManager.AlarmClockInfo(item.quandoMillis, aberturaDoApp(ctx)),
                pi
            )
        } else {
            // Sem a permissão de alarme exato, cai para um alarme aproximado
            am.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, item.quandoMillis, pi)
        }
    }

    fun cancelar(ctx: Context, id: Long) {
        alarmManager(ctx).cancel(disparo(ctx, id))
    }

    /** Calcula o próximo horário de um agendamento que se repete. */
    fun proximaOcorrencia(millis: Long, repeticao: br.com.zapagendado.data.Repeticao): Long? {
        val c = Calendar.getInstance().apply { timeInMillis = millis }
        when (repeticao) {
            br.com.zapagendado.data.Repeticao.NUNCA -> return null
            br.com.zapagendado.data.Repeticao.DIARIO -> c.add(Calendar.DAY_OF_YEAR, 1)
            br.com.zapagendado.data.Repeticao.SEMANAL -> c.add(Calendar.WEEK_OF_YEAR, 1)
            br.com.zapagendado.data.Repeticao.MENSAL -> c.add(Calendar.MONTH, 1)
        }
        // Se o aparelho ficou desligado, avança até passar do agora
        while (c.timeInMillis <= System.currentTimeMillis()) {
            when (repeticao) {
                br.com.zapagendado.data.Repeticao.DIARIO -> c.add(Calendar.DAY_OF_YEAR, 1)
                br.com.zapagendado.data.Repeticao.SEMANAL -> c.add(Calendar.WEEK_OF_YEAR, 1)
                br.com.zapagendado.data.Repeticao.MENSAL -> c.add(Calendar.MONTH, 1)
                else -> return null
            }
        }
        return c.timeInMillis
    }
}
