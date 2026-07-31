package br.com.zapagendado.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.MoreVert
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ElevatedCard
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExtendedFloatingActionButton
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableLongStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import br.com.zapagendado.data.Agendamento
import br.com.zapagendado.data.Repeticao
import br.com.zapagendado.data.Status
import br.com.zapagendado.data.Telefone
import kotlinx.coroutines.delay

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ListaScreen(
    itens: List<Agendamento>,
    avisoAlarmeExato: Boolean,
    onCorrigirAlarme: () -> Unit,
    onNovo: () -> Unit,
    onEditar: (Agendamento) -> Unit,
    onCancelar: (Agendamento) -> Unit,
    onReativar: (Agendamento) -> Unit,
    onRemover: (Agendamento) -> Unit,
    onLimpar: () -> Unit
) {
    // Redesenha a contagem regressiva a cada 30 s
    var tick by remember { mutableLongStateOf(0L) }
    LaunchedEffect(Unit) {
        while (true) {
            delay(30_000)
            tick++
        }
    }

    val pendentes = itens.filter { it.status == Status.PENDENTE }.sortedBy { it.quandoMillis }
    val resto = itens.filter { it.status != Status.PENDENTE }.sortedByDescending { it.quandoMillis }

    Scaffold(
        containerColor = MaterialTheme.colorScheme.background,
        topBar = {
            TopAppBar(
                title = { Text("Zap Agendado", style = MaterialTheme.typography.titleLarge) },
                actions = {
                    if (resto.isNotEmpty()) {
                        TextButton(onClick = onLimpar) { Text("Limpar histórico") }
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.background,
                    titleContentColor = Texto,
                    actionIconContentColor = TextoFraco
                )
            )
        },
        floatingActionButton = {
            ExtendedFloatingActionButton(
                onClick = onNovo,
                containerColor = Sinal,
                contentColor = Tinta,
                icon = { Icon(Icons.Default.Add, null) },
                text = { Text("Agendar") }
            )
        }
    ) { pad ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(pad),
            contentPadding = PaddingValues(16.dp, 8.dp, 16.dp, 96.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            if (avisoAlarmeExato) {
                item { AvisoAlarme(onCorrigirAlarme) }
            }

            if (itens.isEmpty()) {
                item { Vazio() }
            }

            if (pendentes.isNotEmpty()) {
                item { Rotulo("NA FILA · ${pendentes.size}") }
                items(pendentes, key = { it.id }) { item ->
                    Cartao(item, tick, onEditar, onCancelar, onReativar, onRemover)
                }
            }

            if (resto.isNotEmpty()) {
                item { Spacer(Modifier.height(12.dp)); Rotulo("JÁ PASSOU") }
                items(resto, key = { it.id }) { item ->
                    Cartao(item, tick, onEditar, onCancelar, onReativar, onRemover)
                }
            }
        }
    }
}

@Composable
private fun Rotulo(texto: String) {
    Text(
        texto,
        style = MaterialTheme.typography.labelSmall,
        color = TextoFraco,
        modifier = Modifier.padding(start = 4.dp, top = 8.dp, bottom = 2.dp)
    )
}

@Composable
private fun Vazio() {
    Column(Modifier.fillMaxWidth().padding(top = 96.dp), horizontalAlignment = Alignment.CenterHorizontally) {
        Text("Nada na fila", style = MaterialTheme.typography.titleLarge, color = Texto)
        Spacer(Modifier.height(6.dp))
        Text(
            "Toque em Agendar para escrever uma mensagem e escolher quando ela deve sair.",
            style = MaterialTheme.typography.bodyMedium,
            color = TextoFraco,
            modifier = Modifier.padding(horizontal = 32.dp)
        )
    }
}

@Composable
private fun AvisoAlarme(onCorrigir: () -> Unit) {
    ElevatedCard(
        colors = CardDefaults.elevatedCardColors(containerColor = SuperficieAlta),
        shape = RoundedCornerShape(14.dp),
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(Modifier.padding(14.dp), verticalAlignment = Alignment.CenterVertically) {
            Icon(Icons.Default.Warning, null, tint = Ambar, modifier = Modifier.size(20.dp))
            Spacer(Modifier.width(12.dp))
            Column(Modifier.weight(1f)) {
                Text("Os horários podem atrasar", color = Texto, style = MaterialTheme.typography.titleMedium)
                Text(
                    "Sem permissão de alarme exato, o Android decide a hora de acordar o app.",
                    color = TextoFraco,
                    style = MaterialTheme.typography.bodyMedium
                )
            }
            TextButton(onClick = onCorrigir) { Text("Permitir") }
        }
    }
}

@Composable
private fun Cartao(
    item: Agendamento,
    @Suppress("UNUSED_PARAMETER") tick: Long,
    onEditar: (Agendamento) -> Unit,
    onCancelar: (Agendamento) -> Unit,
    onReativar: (Agendamento) -> Unit,
    onRemover: (Agendamento) -> Unit
) {
    val pendente = item.status == Status.PENDENTE
    val cor = when (item.status) {
        Status.PENDENTE -> Sinal
        Status.ENVIADO -> Apagado
        Status.CANCELADO -> Apagado
        Status.FALHOU -> Ambar
    }
    var menuAberto by remember { mutableStateOf(false) }

    ElevatedCard(
        colors = CardDefaults.elevatedCardColors(containerColor = Superficie),
        shape = RoundedCornerShape(14.dp),
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(Modifier.fillMaxWidth()) {
            // Faixa vertical de estado — a única cor no cartão
            Box(
                Modifier
                    .width(3.dp)
                    .height(if (pendente) 118.dp else 96.dp)
                    .clip(RoundedCornerShape(topStart = 14.dp, bottomStart = 14.dp))
                    .background(cor)
            )

            Column(Modifier.weight(1f).padding(14.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Column(Modifier.weight(1f)) {
                        Text(
                            item.nomeContato.ifBlank { Telefone.formatarBonito(item.numero) },
                            style = MaterialTheme.typography.titleMedium,
                            color = Texto,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis
                        )
                        if (item.nomeContato.isNotBlank()) {
                            Text(
                                Telefone.formatarBonito(item.numero),
                                style = MaterialTheme.typography.bodyMedium,
                                color = TextoFraco
                            )
                        }
                    }

                    Box {
                        IconButton(onClick = { menuAberto = true }) {
                            Icon(Icons.Default.MoreVert, "Mais opções", tint = TextoFraco)
                        }
                        DropdownMenu(menuAberto, onDismissRequest = { menuAberto = false }) {
                            if (pendente) {
                                DropdownMenuItem(
                                    text = { Text("Editar") },
                                    onClick = { menuAberto = false; onEditar(item) }
                                )
                                DropdownMenuItem(
                                    text = { Text("Cancelar envio") },
                                    onClick = { menuAberto = false; onCancelar(item) }
                                )
                            } else if (item.quandoMillis > System.currentTimeMillis()) {
                                DropdownMenuItem(
                                    text = { Text("Colocar de volta na fila") },
                                    leadingIcon = { Icon(Icons.Default.Refresh, null) },
                                    onClick = { menuAberto = false; onReativar(item) }
                                )
                            }
                            HorizontalDivider()
                            DropdownMenuItem(
                                text = { Text("Excluir") },
                                leadingIcon = { Icon(Icons.Default.Delete, null) },
                                onClick = { menuAberto = false; onRemover(item) }
                            )
                        }
                    }
                }

                Spacer(Modifier.height(6.dp))
                Text(
                    item.mensagem,
                    style = MaterialTheme.typography.bodyLarge,
                    color = TextoFraco,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis
                )
                Spacer(Modifier.height(10.dp))

                // O elemento que dá a razão de existir do app: quanto falta.
                if (pendente) {
                    Text(
                        Tempo.contagem(item.quandoMillis),
                        style = MaterialTheme.typography.displaySmall,
                        color = cor
                    )
                }
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        "${Tempo.dia(item.quandoMillis)} às ${Tempo.hora(item.quandoMillis)}",
                        style = MaterialTheme.typography.bodyMedium,
                        color = TextoFraco
                    )
                    if (item.repeticao != Repeticao.NUNCA) {
                        Text(" · ${item.repeticao.rotulo.lowercase()}", style = MaterialTheme.typography.bodyMedium, color = TextoFraco)
                    }
                    if (!pendente) {
                        Text(
                            " · " + when (item.status) {
                                Status.ENVIADO -> "aberto no WhatsApp"
                                Status.CANCELADO -> "cancelado"
                                Status.FALHOU -> "não disparou"
                                else -> ""
                            },
                            style = MaterialTheme.typography.bodyMedium,
                            color = cor
                        )
                    }
                }
            }
        }
    }
}
