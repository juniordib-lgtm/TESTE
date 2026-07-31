package br.com.zapagendado.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.DateRange
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.Schedule
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.AssistChip
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.DatePicker
import androidx.compose.material3.DatePickerDialog
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TimePicker
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.material3.rememberDatePickerState
import androidx.compose.material3.rememberTimePickerState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableLongStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import br.com.zapagendado.data.Agendamento
import br.com.zapagendado.data.Repeticao
import br.com.zapagendado.data.Telefone
import java.util.Calendar

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun EditorScreen(
    original: Agendamento?,
    autoDisponivel: Boolean,
    onEscolherContato: () -> Unit,
    contatoEscolhido: Pair<String, String>?, // nome, numero
    onSalvar: (Agendamento) -> Unit,
    onVoltar: () -> Unit
) {
    var numero by remember { mutableStateOf(original?.numero.orEmpty()) }
    var nome by remember { mutableStateOf(original?.nomeContato.orEmpty()) }
    var mensagem by remember { mutableStateOf(original?.mensagem.orEmpty()) }
    var business by remember { mutableStateOf(original?.business ?: false) }
    var autoEnviar by remember { mutableStateOf(original?.autoEnviar ?: false) }
    var repeticao by remember { mutableStateOf(original?.repeticao ?: Repeticao.NUNCA) }

    var quando by remember {
        mutableLongStateOf(
            original?.quandoMillis ?: Calendar.getInstance()
                .apply { add(Calendar.HOUR_OF_DAY, 1); set(Calendar.SECOND, 0) }.timeInMillis
        )
    }

    // Contato vindo da agenda do celular
    if (contatoEscolhido != null) {
        val (n, num) = contatoEscolhido
        if (num.isNotBlank() && num != numero) {
            nome = n
            numero = num
        }
    }

    var abrirData by remember { mutableStateOf(false) }
    var abrirHora by remember { mutableStateOf(false) }

    val numeroOk = Telefone.valido(numero)
    val futuro = quando > System.currentTimeMillis()
    val podeSalvar = numeroOk && mensagem.isNotBlank() && futuro

    Scaffold(
        containerColor = MaterialTheme.colorScheme.background,
        topBar = {
            TopAppBar(
                title = { Text(if (original == null) "Nova mensagem" else "Editar mensagem") },
                navigationIcon = {
                    IconButton(onClick = onVoltar) { Icon(Icons.Default.ArrowBack, "Voltar") }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.background,
                    titleContentColor = Texto,
                    navigationIconContentColor = Texto
                )
            )
        }
    ) { pad ->
        Column(
            Modifier
                .fillMaxSize()
                .padding(pad)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp)
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                OutlinedTextField(
                    value = numero,
                    onValueChange = { numero = it },
                    label = { Text("Número com DDD") },
                    placeholder = { Text("84 99999-8888") },
                    supportingText = {
                        Text(
                            if (numero.isBlank()) "O DDI 55 entra sozinho se você não colocar"
                            else Telefone.formatarBonito(Telefone.normalizar(numero))
                        )
                    },
                    isError = numero.isNotBlank() && !numeroOk,
                    singleLine = true,
                    keyboardOptions = androidx.compose.foundation.text.KeyboardOptions(keyboardType = KeyboardType.Phone),
                    modifier = Modifier.weight(1f)
                )
                Spacer(Modifier.width(8.dp))
                OutlinedButton(onClick = onEscolherContato, shape = RoundedCornerShape(12.dp)) {
                    Icon(Icons.Default.Person, "Escolher da agenda")
                }
            }

            OutlinedTextField(
                value = nome,
                onValueChange = { nome = it },
                label = { Text("Apelido (opcional)") },
                singleLine = true,
                modifier = Modifier.fillMaxWidth()
            )

            OutlinedTextField(
                value = mensagem,
                onValueChange = { mensagem = it },
                label = { Text("Mensagem") },
                minLines = 4,
                supportingText = { Text("${mensagem.length} caracteres") },
                modifier = Modifier.fillMaxWidth()
            )

            Text("QUANDO", style = MaterialTheme.typography.labelSmall, color = TextoFraco)
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp), modifier = Modifier.fillMaxWidth()) {
                OutlinedButton(
                    onClick = { abrirData = true },
                    shape = RoundedCornerShape(12.dp),
                    modifier = Modifier.weight(1f)
                ) {
                    Icon(Icons.Default.DateRange, null); Spacer(Modifier.width(8.dp))
                    Text(Tempo.dataCompleta(quando))
                }
                OutlinedButton(onClick = { abrirHora = true }, shape = RoundedCornerShape(12.dp)) {
                    Icon(Icons.Default.Schedule, null); Spacer(Modifier.width(8.dp))
                    Text(Tempo.hora(quando))
                }
            }

            if (futuro) {
                AssistChip(onClick = {}, label = { Text("Sai ${Tempo.contagem(quando)}") })
            } else {
                Text("Escolha um horário que ainda não passou.", color = Ambar, style = MaterialTheme.typography.bodyMedium)
            }

            Text("REPETIR", style = MaterialTheme.typography.labelSmall, color = TextoFraco)
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Repeticao.entries.forEach { r ->
                    FilterChip(
                        selected = repeticao == r,
                        onClick = { repeticao = r },
                        label = { Text(r.rotulo) }
                    )
                }
            }

            Spacer(Modifier.height(4.dp))
            Linha("Usar WhatsApp Business", "Abre no com.whatsapp.w4b", business) { business = it }

            if (autoDisponivel) {
                Linha(
                    "Tocar em enviar sozinho",
                    "Precisa do serviço de acessibilidade ligado. Veja os riscos no README.",
                    autoEnviar
                ) { autoEnviar = it }
            }

            Spacer(Modifier.height(8.dp))
            Button(
                onClick = {
                    onSalvar(
                        (original ?: Agendamento(numero = "", mensagem = "", quandoMillis = 0)).copy(
                            numero = Telefone.normalizar(numero),
                            nomeContato = nome.trim(),
                            mensagem = mensagem.trim(),
                            quandoMillis = quando,
                            repeticao = repeticao,
                            business = business,
                            autoEnviar = autoEnviar,
                            status = br.com.zapagendado.data.Status.PENDENTE
                        )
                    )
                },
                enabled = podeSalvar,
                colors = ButtonDefaults.buttonColors(containerColor = Sinal, contentColor = Tinta),
                shape = RoundedCornerShape(14.dp),
                modifier = Modifier.fillMaxWidth().height(52.dp)
            ) { Text(if (original == null) "Colocar na fila" else "Salvar alterações") }

            Text(
                "Na hora marcada o app abre a conversa com o texto pronto. O toque em enviar é seu, a não ser que você ligue o envio automático.",
                style = MaterialTheme.typography.bodyMedium,
                color = TextoFraco
            )
        }
    }

    if (abrirData) {
        val estado = rememberDatePickerState(initialSelectedDateMillis = quando)
        DatePickerDialog(
            onDismissRequest = { abrirData = false },
            confirmButton = {
                TextButton(onClick = {
                    estado.selectedDateMillis?.let { d ->
                        val c = Calendar.getInstance().apply { timeInMillis = quando }
                        quando = Tempo.juntarDataHora(d, c.get(Calendar.HOUR_OF_DAY), c.get(Calendar.MINUTE))
                    }
                    abrirData = false
                }) { Text("Escolher") }
            },
            dismissButton = { TextButton(onClick = { abrirData = false }) { Text("Voltar") } }
        ) { DatePicker(state = estado) }
    }

    if (abrirHora) {
        val c = Calendar.getInstance().apply { timeInMillis = quando }
        val estado = rememberTimePickerState(
            initialHour = c.get(Calendar.HOUR_OF_DAY),
            initialMinute = c.get(Calendar.MINUTE),
            is24Hour = true
        )
        AlertDialog(
            onDismissRequest = { abrirHora = false },
            confirmButton = {
                TextButton(onClick = {
                    val dia = Calendar.getInstance().apply {
                        timeInMillis = quando
                        set(Calendar.HOUR_OF_DAY, estado.hour)
                        set(Calendar.MINUTE, estado.minute)
                        set(Calendar.SECOND, 0)
                        set(Calendar.MILLISECOND, 0)
                    }
                    quando = dia.timeInMillis
                    abrirHora = false
                }) { Text("Escolher") }
            },
            dismissButton = { TextButton(onClick = { abrirHora = false }) { Text("Voltar") } },
            text = { TimePicker(state = estado) }
        )
    }
}

@Composable
private fun Linha(titulo: String, apoio: String, valor: Boolean, onMudar: (Boolean) -> Unit) {
    Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
        Column(Modifier.weight(1f)) {
            Text(titulo, color = Texto, style = MaterialTheme.typography.titleMedium)
            Text(apoio, color = TextoFraco, style = MaterialTheme.typography.bodyMedium)
        }
        Switch(checked = valor, onCheckedChange = onMudar)
    }
}
