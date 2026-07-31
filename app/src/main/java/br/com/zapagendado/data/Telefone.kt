package br.com.zapagendado.data

/** Normalização de número no padrão que o WhatsApp aceita: só dígitos, com DDI. */
object Telefone {

    const val DDI_PADRAO = "55"

    fun normalizar(bruto: String, ddi: String = DDI_PADRAO): String {
        var d = bruto.filter { it.isDigit() }
        if (d.isEmpty()) return ""

        // Tira zeros de operadora/tronco na frente
        while (d.startsWith("0")) d = d.drop(1)

        // Já veio com DDI
        if (d.startsWith(ddi) && d.length > 10) return d

        // 10 ou 11 dígitos = DDD + número (Brasil), falta o DDI
        return if (d.length in 10..11) ddi + d else d
    }

    fun formatarBonito(numero: String): String {
        val d = numero.filter { it.isDigit() }
        return when {
            d.length == 13 -> "+${d.take(2)} (${d.substring(2, 4)}) ${d.substring(4, 9)}-${d.substring(9)}"
            d.length == 12 -> "+${d.take(2)} (${d.substring(2, 4)}) ${d.substring(4, 8)}-${d.substring(8)}"
            else -> "+$d"
        }
    }

    fun valido(numero: String): Boolean = numero.filter { it.isDigit() }.length in 10..15
}
