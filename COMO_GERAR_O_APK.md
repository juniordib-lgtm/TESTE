# Como gerar o APK

O código-fonte precisa ser compilado uma vez. Escolha um dos dois caminhos.

---

## Caminho A — Android Studio (recomendado, sem terminal)

1. Baixe o Android Studio em https://developer.android.com/studio (gratuito, Windows/Mac/Linux).
2. Descompacte o `ZapAgendado.zip`.
3. No Android Studio: **File → Open** e escolha a pasta `ZapAgendado`.
4. Espere a barra de progresso terminar. Na primeira vez ele baixa o Gradle e o SDK sozinho — leva de 5 a 15 minutos dependendo da internet.
5. Menu **Build → Build Bundle(s) / APK(s) → Build APK(s)**.
6. Quando aparecer o aviso no canto, clique em **locate**. O arquivo está em:

```
ZapAgendado/app/build/outputs/apk/debug/app-debug.apk
```

7. Passe esse `.apk` para o celular (cabo, Google Drive, Telegram) e toque nele para instalar.

Para instalar direto pelo cabo USB, com Depuração USB ligada no celular: **Run → Run 'app'**.

---

## Caminho B — GitHub Actions (compila na nuvem, sem instalar nada)

Já deixei o workflow pronto no projeto. Você só precisa de uma conta no GitHub.

1. Crie um repositório novo em https://github.com/new (pode ser privado).
2. Envie os arquivos: na página do repositório vazio, use **uploading an existing file** e arraste tudo de dentro da pasta `ZapAgendado`.
   - Atenção: arraste o *conteúdo* da pasta, não a pasta em si. O `build.gradle.kts` precisa ficar na raiz do repositório.
3. Vá na aba **Actions**. O workflow "Gerar APK" começa sozinho.
4. Espere terminar (uns 5 minutos, marca de check verde).
5. Clique na execução e baixe **zapagendado-debug-apk** na seção Artifacts. Dentro do zip está o `app-debug.apk`.

---

## Ao instalar no celular

O Android vai avisar que o app veio de fonte desconhecida — é o comportamento normal para APK que não veio da Play Store. Autorize a instalação para o app que está abrindo o arquivo (Arquivos, Chrome ou Drive).

Depois de abrir o Zap Agendado pela primeira vez, conceda:

- **Alarmes e lembretes** — sem isso os horários atrasam
- **Notificações**
- **Bateria sem restrição** — em Xiaomi, ative também "Início automático"

---

## Sobre assinatura

O APK gerado acima é de *debug*: assinado com a chave de teste do Android. Funciona perfeitamente para uso próprio e instala em qualquer aparelho.

Para publicar na Play Store seria preciso um APK de *release* com sua própria chave (**Build → Generate Signed Bundle / APK** no Android Studio). Vale lembrar o que está no README: se a opção de envio automático por acessibilidade estiver ativa, a Play Store costuma reprovar a publicação.
