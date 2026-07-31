package br.com.zapagendado.ui

import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Date
import java.util.Locale

object Tempo {

    private val ptBR = Locale("pt", "BR")
    private val hora = SimpleDateFormat("HH:mm", ptBR)
    private val dataCurta = SimpleDateFormat("d 'de' MMM", ptBR)
    private val dataCompleta = SimpleDateFormat("d 'de' MMMM 'de' yyyy", ptBR)

    fun hora(millis: Long): String = hora.format(Date(millis))

    fun dataCompleta(millis: Long): String = dataCompleta.format(Date(millis))

    /** "hoje", "amanhã" ou "12 de mar" */
    fun dia(millis: Long): String {
        val alvo = Calendar.getInstance().apply { timeInMillis = millis }
        val hoje = Calendar.getInstance()
        val amanha = Calendar.getInstance().apply { add(Calendar.DAY_OF_YEAR, 1) }

        fun mesmoDia(a: Calendar, b: Calendar) =
            a.get(Calendar.YEAR) == b.get(Calendar.YEAR) &&
                a.get(Calendar.DAY_OF_YEAR) == b.get(Calendar.DAY_OF_YEAR)

        return when {
            mesmoDia(alvo, hoje) -> "hoje"
            mesmoDia(alvo, amanha) -> "amanhã"
            else -> dataCurta.format(Date(millis))
        }
    }

    /** O destaque de cada cartão: "em 2h 14min", "em 38min", "agora". */
    fun contagem(millis: Long): String {
        val falta = millis - System.currentTimeMillis()
        if (falta <= 0) return "agora"

        val min = falta / 60_000
        val h = min / 60
        val dias = h / 24

        return when {
            dias >= 1 -> {
                val hRestantes = h % 24
                if (hRestantes > 0) "em ${dias}d ${hRestantes}h" else "em ${dias}d"
            }
            h >= 1 -> {
                val mRestantes = min % 60
                if (mRestantes > 0) "em ${h}h ${mRestantes}min" else "em ${h}h"
            }
            min >= 1 -> "em ${min}min"
            else -> "em menos de 1min"
        }
    }

    fun juntarDataHora(dataMillisUtc: Long, horas: Int, minutos: Int): Long {
        // O DatePicker devolve meia-noite em UTC; extraímos o dia sem fuso e remontamos local.
        val utc = Calendar.getInstance(java.util.TimeZone.getTimeZone("UTC")).apply {
            timeInMillis = dataMillisUtc
        }
        return Calendar.getInstance().apply {
            set(Calendar.YEAR, utc.get(Calendar.YEAR))
            set(Calendar.MONTH, utc.get(Calendar.MONTH))
            set(Calendar.DAY_OF_MONTH, utc.get(Calendar.DAY_OF_MONTH))
            set(Calendar.HOUR_OF_DAY, horas)
            set(Calendar.MINUTE, minutos)
            set(Calendar.SECOND, 0)
            set(Calendar.MILLISECOND, 0)
        }.timeInMillis
    }
}
