package br.com.boedconversor

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import java.util.Locale

/**
 * Fatores de equivalência usados pela indústria (SPE/SEC):
 * 1 m³ de óleo = 6,28981 bbl
 * 1 boe = 6.000 pés³ de gás = 169,901 m³ de gás
 */
private const val BBL_POR_M3_OLEO = 6.28981
private const val M3_GAS_POR_BOE = 169.901

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
                Surface(modifier = Modifier.fillMaxSize()) {
                    TelaConversor()
                }
            }
        }
    }
}

private fun textoParaNumero(texto: String): Double =
    texto.trim().replace(",", ".").toDoubleOrNull() ?: 0.0

private fun formata(valor: Double): String =
    String.format(Locale.US, "%,.2f", valor)

@Composable
fun TelaConversor() {
    var oleoTexto by remember { mutableStateOf("") }
    var gasTexto by remember { mutableStateOf("") }

    val oleoM3d = textoParaNumero(oleoTexto)
    val gasM3d = textoParaNumero(gasTexto)

    val oleoBoed = oleoM3d * BBL_POR_M3_OLEO
    val gasBoed = gasM3d / M3_GAS_POR_BOE
    val totalBoed = oleoBoed + gasBoed

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        Text(
            text = "Conversor BOED",
            style = MaterialTheme.typography.headlineMedium,
            fontWeight = FontWeight.Bold
        )
        Text(
            text = "Converte a produção de teste de óleo e gás (m³/d) em barris de óleo equivalente por dia (BOED).",
            style = MaterialTheme.typography.bodyMedium
        )

        OutlinedTextField(
            value = oleoTexto,
            onValueChange = { oleoTexto = it },
            label = { Text("Produção de teste de óleo (m³/d)") },
            keyboardOptions = androidx.compose.foundation.text.KeyboardOptions(keyboardType = KeyboardType.Decimal),
            singleLine = true,
            modifier = Modifier.fillMaxWidth()
        )

        OutlinedTextField(
            value = gasTexto,
            onValueChange = { gasTexto = it },
            label = { Text("Produção de teste de gás (m³/d)") },
            keyboardOptions = androidx.compose.foundation.text.KeyboardOptions(keyboardType = KeyboardType.Decimal),
            singleLine = true,
            modifier = Modifier.fillMaxWidth()
        )

        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer)
        ) {
            Column(
                modifier = Modifier.padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Text("Óleo: ${formata(oleoBoed)} BOED", style = MaterialTheme.typography.bodyLarge)
                Text("Gás: ${formata(gasBoed)} BOED", style = MaterialTheme.typography.bodyLarge)
                Text(
                    text = "Total: ${formata(totalBoed)} BOED",
                    style = MaterialTheme.typography.headlineSmall,
                    fontWeight = FontWeight.Bold
                )
            }
        }

        Text(
            text = "Fatores usados: 1 m³ de óleo = 6,28981 bbl · 1 boe = 169,901 m³ de gás (6.000 pés³/boe).",
            style = MaterialTheme.typography.bodySmall
        )
    }
}
