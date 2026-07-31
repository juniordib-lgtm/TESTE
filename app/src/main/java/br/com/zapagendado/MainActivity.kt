package br.com.zapagendado

import android.Manifest
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.ContactsContract
import android.provider.Settings
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.viewModels
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.core.net.toUri
import br.com.zapagendado.agenda.Agendador
import br.com.zapagendado.data.Agendamento
import br.com.zapagendado.data.Telefone
import br.com.zapagendado.envio.AutoEnvioService
import br.com.zapagendado.ui.AgendamentoViewModel
import br.com.zapagendado.ui.EditorScreen
import br.com.zapagendado.ui.ListaScreen
import br.com.zapagendado.ui.TemaZap

class MainActivity : ComponentActivity() {

    companion object {
        /** Só pergunta uma vez por execução, para não virar diálogo repetido. */
        private var jaPerguntouBateria = false
    }

    private val vm: AgendamentoViewModel by viewModels()

    private var aoReceberContato: ((String, String) -> Unit)? = null

    private val pedirNotificacao =
        registerForActivityResult(ActivityResultContracts.RequestPermission()) { }

    private val escolherContato =
        registerForActivityResult(ActivityResultContracts.StartActivityForResult()) { res ->
            val uri = res.data?.data ?: return@registerForActivityResult
            contentResolver.query(
                uri,
                arrayOf(
                    ContactsContract.CommonDataKinds.Phone.NUMBER,
                    ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME
                ),
                null, null, null
            )?.use { c ->
                if (c.moveToFirst()) {
                    val numero = Telefone.normalizar(c.getString(0).orEmpty())
                    val nome = c.getString(1).orEmpty()
                    aoReceberContato?.invoke(nome, numero)
                }
            }
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            pedirNotificacao.launch(Manifest.permission.POST_NOTIFICATIONS)
        }

        setContent {
            TemaZap {
                val itens by vm.lista.collectAsState()

                // null = lista, Agendamento = editor
                var editando by remember { mutableStateOf<Agendamento?>(null) }
                var emEdicao by remember { mutableStateOf(false) }
                var contato by remember { mutableStateOf<Pair<String, String>?>(null) }
                var alarmeOk by remember { mutableStateOf(Agendador.podeAlarmeExato(this)) }

                if (!emEdicao) {
                    alarmeOk = Agendador.podeAlarmeExato(this)
                    ListaScreen(
                        itens = itens,
                        avisoAlarmeExato = !alarmeOk,
                        onCorrigirAlarme = { abrirAjusteAlarme() },
                        onNovo = { editando = null; contato = null; emEdicao = true },
                        onEditar = { editando = it; contato = null; emEdicao = true },
                        onCancelar = vm::cancelar,
                        onReativar = vm::reativar,
                        onRemover = vm::remover,
                        onLimpar = vm::limparConcluidos
                    )
                } else {
                    EditorScreen(
                        original = editando,
                        autoDisponivel = true,
                        contatoEscolhido = contato,
                        onEscolherContato = {
                            aoReceberContato = { n, num -> contato = n to num }
                            escolherContato.launch(
                                Intent(Intent.ACTION_PICK, ContactsContract.CommonDataKinds.Phone.CONTENT_URI)
                            )
                        },
                        onSalvar = { item ->
                            if (item.autoEnviar && !AutoEnvioService.ligado(this)) abrirAjusteAcessibilidade()
                            vm.salvar(item)
                            emEdicao = false
                            editando = null
                            contato = null
                        },
                        onVoltar = { emEdicao = false; editando = null; contato = null }
                    )
                }
            }
        }
    }

    override fun onResume() {
        super.onResume()
        pedirIsencaoDeBateria()
    }

    private fun abrirAjusteAlarme() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            runCatching {
                startActivity(
                    Intent(Settings.ACTION_REQUEST_SCHEDULE_EXACT_ALARM, "package:$packageName".toUri())
                )
            }
        }
    }

    private fun abrirAjusteAcessibilidade() {
        runCatching { startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)) }
    }

    /** Sem isso, fabricantes agressivos (Xiaomi, Oppo, Samsung) matam o alarme. */
    private fun pedirIsencaoDeBateria() {
        if (jaPerguntouBateria) return
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.M) return
        val pm = getSystemService(android.os.PowerManager::class.java)
        if (pm.isIgnoringBatteryOptimizations(packageName)) return
        jaPerguntouBateria = true
        runCatching {
            startActivity(
                Intent(
                    Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS,
                    Uri.parse("package:$packageName")
                )
            )
        }
    }
}
