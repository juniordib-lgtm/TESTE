package br.com.zapagendado

import android.app.Application
import android.app.NotificationChannel
import android.app.NotificationManager
import android.os.Build

class ZapApp : Application() {

    companion object {
        const val CANAL_DISPARO = "disparo"
    }

    override fun onCreate() {
        super.onCreate()
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val canal = NotificationChannel(
                CANAL_DISPARO,
                "Disparo de mensagens",
                NotificationManager.IMPORTANCE_HIGH
            ).apply {
                description = "Avisa e abre o WhatsApp na hora marcada"
                enableVibration(true)
                setBypassDnd(true)
                lockscreenVisibility = android.app.Notification.VISIBILITY_PUBLIC
            }
            (getSystemService(NotificationManager::class.java)).createNotificationChannel(canal)
        }
    }
}
