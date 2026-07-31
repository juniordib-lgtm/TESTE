package br.com.zapagendado.envio

import android.accessibilityservice.AccessibilityService
import android.content.Context
import android.provider.Settings
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo

/**
 * OPCIONAL — toca no botão "enviar" do WhatsApp sozinho.
 *
 * Fica inerte o tempo todo. Só age dentro de uma janela de poucos segundos
 * aberta pela EnvioActivity, e só quando você marcou "enviar sozinho" naquele
 * agendamento. Leia a seção de riscos do README antes de ligar isso.
 */
class AutoEnvioService : AccessibilityService() {

    companion object {
        @Volatile private var armadoAte: Long = 0L

        /** Abre a janela em que o serviço pode agir. */
        fun armar(duracaoMs: Long) {
            armadoAte = System.currentTimeMillis() + duracaoMs
        }

        fun desarmar() { armadoAte = 0L }

        fun ligado(ctx: Context): Boolean {
            val ativos = Settings.Secure.getString(
                ctx.contentResolver,
                Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES
            ).orEmpty()
            return ativos.contains("${ctx.packageName}/${AutoEnvioService::class.java.name}")
        }

        private val IDS_ENVIAR = listOf(
            "com.whatsapp:id/send",
            "com.whatsapp.w4b:id/send"
        )

        private val ROTULOS_ENVIAR = listOf("enviar", "send")
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        if (System.currentTimeMillis() > armadoAte) return

        val raiz = rootInActiveWindow ?: return
        val botao = acharBotaoEnviar(raiz) ?: return

        val clicavel = generateSequence(botao) { it.parent }.firstOrNull { it.isClickable }
        if (clicavel != null && clicavel.performAction(AccessibilityNodeInfo.ACTION_CLICK)) {
            desarmar()
        }
    }

    override fun onInterrupt() = desarmar()

    private fun acharBotaoEnviar(raiz: AccessibilityNodeInfo): AccessibilityNodeInfo? {
        // Caminho rápido: id conhecido
        for (id in IDS_ENVIAR) {
            raiz.findAccessibilityNodeInfosByViewId(id).firstOrNull()?.let { return it }
        }
        // Caminho lento: procura pela descrição do botão
        return varrer(raiz) { no ->
            val desc = no.contentDescription?.toString()?.lowercase().orEmpty()
            no.isVisibleToUser && ROTULOS_ENVIAR.any { desc == it || desc.startsWith("$it ") }
        }
    }

    private fun varrer(no: AccessibilityNodeInfo, casa: (AccessibilityNodeInfo) -> Boolean): AccessibilityNodeInfo? {
        if (casa(no)) return no
        for (i in 0 until no.childCount) {
            val filho = no.getChild(i) ?: continue
            varrer(filho, casa)?.let { return it }
        }
        return null
    }
}
