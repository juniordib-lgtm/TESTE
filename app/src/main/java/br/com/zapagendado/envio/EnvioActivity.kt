package br.com.zapagendado.envio

import android.app.Activity
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.widget.Toast
import br.com.zapagendado.data.Agendamento

/**
 * Activity sem interface. Abre a conversa no WhatsApp com o texto já digitado.
 * O toque final em "enviar" é seu — a menos que o serviço de acessibilidade esteja ligado.
 */
class EnvioActivity : Activity() {

    companion object {
        private const val E_NUMERO = "numero"
        private const val E_TEXTO = "texto"
        private const val E_BUSINESS = "business"
        private const val E_AUTO = "auto"

        const val PKG_WHATSAPP = "com.whatsapp"
        const val PKG_BUSINESS = "com.whatsapp.w4b"

        fun intent(ctx: Context, item: Agendamento): Intent =
            Intent(ctx, EnvioActivity::class.java).apply {
                addFlags(
                    Intent.FLAG_ACTIVITY_NEW_TASK or
                        Intent.FLAG_ACTIVITY_CLEAR_TOP or
                        Intent.FLAG_ACTIVITY_EXCLUDE_FROM_RECENTS
                )
                putExtra(E_NUMERO, item.numero)
                putExtra(E_TEXTO, item.mensagem)
                putExtra(E_BUSINESS, item.business)
                putExtra(E_AUTO, item.autoEnviar)
            }

        fun instalado(ctx: Context, pacote: String): Boolean = runCatching {
            ctx.packageManager.getPackageInfo(pacote, 0); true
        }.getOrDefault(false)
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        acordarTela()

        val numero = intent.getStringExtra(E_NUMERO).orEmpty()
        val texto = intent.getStringExtra(E_TEXTO).orEmpty()
        val business = intent.getBooleanExtra(E_BUSINESS, false)
        val auto = intent.getBooleanExtra(E_AUTO, false)

        val pacote = if (business) PKG_BUSINESS else PKG_WHATSAPP

        if (!instalado(this, pacote)) {
            Toast.makeText(this, "WhatsApp não encontrado neste aparelho", Toast.LENGTH_LONG).show()
            finish()
            return
        }

        if (auto) AutoEnvioService.armar(15_000)

        val url = "https://wa.me/$numero?text=" + Uri.encode(texto)
        val abrir = Intent(Intent.ACTION_VIEW, Uri.parse(url)).apply {
            setPackage(pacote)
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        }

        val ok = runCatching { startActivity(abrir); true }.getOrElse {
            // Alguns aparelhos recusam o setPackage; tenta sem ele
            runCatching {
                startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
                true
            }.getOrDefault(false)
        }

        if (!ok) Toast.makeText(this, "Não deu para abrir a conversa", Toast.LENGTH_LONG).show()
        finish()
    }

    private fun acordarTela() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O_MR1) {
            setShowWhenLocked(true)
            setTurnScreenOn(true)
        } else {
            @Suppress("DEPRECATION")
            window.addFlags(
                android.view.WindowManager.LayoutParams.FLAG_SHOW_WHEN_LOCKED or
                    android.view.WindowManager.LayoutParams.FLAG_TURN_SCREEN_ON or
                    android.view.WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON
            )
        }
    }
}
