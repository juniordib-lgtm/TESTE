# Zap Agendado

App Android que guarda mensagens do WhatsApp para saírem em data e hora marcadas.

Kotlin + Jetpack Compose + Room + AlarmManager. Sem servidor, sem conta, sem internet: tudo roda no aparelho.

---

## Antes de tudo: o que é possível e o que não é

O WhatsApp **não tem API pública para mandar mensagem da sua conta pessoal**. Isso muda tudo no que dá para construir. Existem três caminhos, e é bom saber em qual você está pisando:

| Caminho | Como funciona | Custo |
|---|---|---|
| **Intent (este app)** | Na hora marcada o app abre a conversa com o texto já digitado. Você toca em enviar. | Confiável, sem risco de banimento, mas pede um toque seu |
| **Acessibilidade** | Um serviço encontra o botão enviar e toca nele por você | Automático, mas quebra a cada atualização do WhatsApp, viola os Termos de Uso e a Play Store costuma reprovar |
| **Cloud API oficial** | Servidor seu chama a API da Meta | Totalmente automático e legítimo, mas exige conta Business, aprovação da Meta, e fora da janela de 24h só permite modelos aprovados |

Este projeto entrega o primeiro caminho como padrão e o segundo como opção desligada. Se o seu caso é envio comercial em massa, o caminho certo é o terceiro — não este app.

---

## Como rodar

1. Abra a pasta no Android Studio (Ladybug ou mais novo).
2. Sincronize o Gradle. Tudo baixa sozinho.
3. Rode em um aparelho com WhatsApp instalado. Emulador sem WhatsApp não serve.

`minSdk 24` · `targetSdk 35` · JDK 17

---

## O que acontece por dentro

```
Você agenda
   └─ Room grava o registro
        └─ AlarmManager.setAlarmClock() marca o horário
             │  (setAlarmClock fura o modo Soneca — é o mais confiável que o Android oferece)
             ▼
        AlarmeReceiver acorda
             ├─ abre a EnvioActivity (funciona porque o app entra
             │    na lista de dispensa temporária ao tratar um alarme exato)
             └─ publica uma notificação de tela cheia como rede de segurança,
                  caso o sistema bloqueie a abertura em segundo plano
                       ▼
             EnvioActivity monta https://wa.me/<numero>?text=<texto>
             e entrega para o pacote com.whatsapp
```

Se o aparelho reiniciar, o `BootReceiver` remonta todos os alarmes pendentes — sem ele, tudo se perde no reboot.

---

## Permissões e por que cada uma existe

| Permissão | Sem ela |
|---|---|
| `SCHEDULE_EXACT_ALARM` / `USE_EXACT_ALARM` | O Android decide a hora de acordar o app, e o atraso pode passar de uma hora |
| `RECEIVE_BOOT_COMPLETED` | Todo agendamento morre quando o celular reinicia |
| `POST_NOTIFICATIONS` | A rede de segurança some e o disparo pode passar em branco |
| `USE_FULL_SCREEN_INTENT` | O aviso não aparece por cima da tela bloqueada |
| `REQUEST_IGNORE_BATTERY_OPTIMIZATIONS` | Xiaomi, Oppo, Vivo e Samsung matam o app antes da hora |
| `<queries>` no manifesto | No Android 11+ o app nem enxerga que o WhatsApp está instalado |

A permissão de contatos não é pedida: o seletor usa `ACTION_PICK`, que dá acesso só ao contato escolhido.

---

## Envio automático (desligado por padrão)

O `AutoEnvioService` é um `AccessibilityService` que procura o botão enviar e toca nele. Ele fica inerte o tempo todo e só age dentro de uma janela de 15 segundos aberta pela `EnvioActivity`, e só se aquele agendamento tiver a opção marcada.

Antes de ligar, saiba o que está aceitando:

- **Termos do WhatsApp.** Envio automatizado é motivo declarado de bloqueio de conta. Em volume, o bloqueio é questão de tempo.
- **Play Store.** A política de acessibilidade exige que a API sirva a usuários com deficiência. Automatizar mensagens não passa nessa justificativa, e a publicação costuma ser reprovada. Para uso próprio via sideload, não há problema.
- **Fragilidade.** O código procura `com.whatsapp:id/send`. Esse identificador muda sem aviso a cada atualização. Há um plano B pela descrição do botão, mas ele também quebra.

O caminho manual — abrir a conversa pronta e você tocar em enviar — não tem nenhum desses problemas. Vale considerar se um toque por mensagem é mesmo caro no seu caso.

---

## Limitações conhecidas

- **Grupos não funcionam.** O link `wa.me` só aceita número individual. Para grupos seria preciso guardar o JID e usar `ACTION_SEND` com escolha manual da conversa.
- **Anexos não vão.** Só texto. Imagens exigiriam `ACTION_SEND` com `EXTRA_STREAM` e um FileProvider.
- **Um número por agendamento.** Disparo para lista exigiria uma tabela de destinatários e espaçamento entre envios.
- **Sem confirmação de entrega.** O app sabe que abriu o WhatsApp; não sabe se você enviou.

---

## Estrutura

```
app/src/main/java/br/com/zapagendado/
├─ ZapApp.kt                    canal de notificação
├─ MainActivity.kt              navegação, permissões, seletor de contato
├─ data/
│  ├─ Agendamento.kt            entidade, status, recorrência
│  ├─ AgendamentoDao.kt
│  ├─ AppDatabase.kt
│  └─ Telefone.kt               normalização de número com DDI
├─ agenda/
│  ├─ Agendador.kt              AlarmManager e cálculo de recorrência
│  ├─ AlarmeReceiver.kt         o disparo
│  └─ BootReceiver.kt           remonta alarmes após reiniciar
├─ envio/
│  ├─ EnvioActivity.kt          abre a conversa com texto pronto
│  └─ AutoEnvioService.kt       opcional, toca em enviar
└─ ui/
   ├─ Tema.kt · Tempo.kt
   ├─ ListaScreen.kt            fila com contagem regressiva
   ├─ EditorScreen.kt
   └─ AgendamentoViewModel.kt
```

---

## Se der problema

**Não dispara na hora** — confira o aviso amarelo na tela inicial (permissão de alarme exato) e tire o app da otimização de bateria. Em Xiaomi, ative "Início automático" nas configurações do app.

**Abre o WhatsApp mas a conversa vem vazia** — o número saiu errado da normalização. Cheque o texto de apoio embaixo do campo: ele mostra o número final.

**"WhatsApp não encontrado"** — falta o bloco `<queries>` no manifesto, ou o pacote instalado é o Business (`com.whatsapp.w4b`) com a opção desmarcada.
