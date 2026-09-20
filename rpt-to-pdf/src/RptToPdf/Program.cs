using System;
using System.IO;
using System.Linq;

namespace RptToPdf
{
    /// <summary>
    /// CLI para converter arquivo(s) .rpt (Crystal Reports) em PDF.
    ///
    /// Exemplos:
    ///   rpttopdf --input relatorio.rpt --output relatorio.pdf
    ///   rpttopdf --input relatorio.rpt --output saida.pdf --param DataInicio=2026-01-01 --param DataFim=2026-01-31
    ///   rpttopdf --input-dir ./relatorios --output-dir ./pdfs
    ///   rpttopdf --input relatorio.rpt --output saida.pdf --db-server srv --db-name meubanco --db-user usr --db-password ***
    /// </summary>
    internal static class Program
    {
        private static int Main(string[] args)
        {
            if (args.Length == 0 || args.Contains("--help") || args.Contains("-h"))
            {
                MostrarAjuda();
                return args.Length == 0 ? 1 : 0;
            }

            try
            {
                var argumentos = ArgumentosCli.Analisar(args);

                if (argumentos.ModoLote)
                    ConverterPasta(argumentos);
                else
                    ConverterArquivoUnico(argumentos);

                return 0;
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine($"Erro: {ex.Message}");
                return 1;
            }
        }

        private static void ConverterArquivoUnico(ArgumentosCli argumentos)
        {
            if (string.IsNullOrEmpty(argumentos.CaminhoEntrada))
                throw new ArgumentException("Informe --input <arquivo.rpt> (ou use --input-dir para converter uma pasta).");

            var caminhoSaida = argumentos.CaminhoSaida
                ?? Path.ChangeExtension(argumentos.CaminhoEntrada, ".pdf");

            var opcoes = MontarOpcoes(argumentos, argumentos.CaminhoEntrada, caminhoSaida);

            Console.WriteLine($"Convertendo: {argumentos.CaminhoEntrada} -> {caminhoSaida}");
            ConversorRelatorio.ConverterParaPdf(opcoes);
            Console.WriteLine("Concluído.");
        }

        private static void ConverterPasta(ArgumentosCli argumentos)
        {
            var pastaEntrada = argumentos.PastaEntrada!;
            var pastaSaida = argumentos.PastaSaida ?? pastaEntrada;

            if (!Directory.Exists(pastaEntrada))
                throw new DirectoryNotFoundException($"Pasta não encontrada: {pastaEntrada}");

            var arquivosRpt = Directory.GetFiles(pastaEntrada, "*.rpt", SearchOption.TopDirectoryOnly);
            if (arquivosRpt.Length == 0)
            {
                Console.WriteLine("Nenhum arquivo .rpt encontrado na pasta informada.");
                return;
            }

            var sucessos = 0;
            foreach (var caminhoRpt in arquivosRpt)
            {
                var nomeBase = Path.GetFileNameWithoutExtension(caminhoRpt);
                var caminhoPdf = Path.Combine(pastaSaida, nomeBase + ".pdf");
                var opcoes = MontarOpcoes(argumentos, caminhoRpt, caminhoPdf);

                Console.WriteLine($"Convertendo: {caminhoRpt} -> {caminhoPdf}");
                try
                {
                    ConversorRelatorio.ConverterParaPdf(opcoes);
                    sucessos++;
                }
                catch (Exception ex)
                {
                    Console.Error.WriteLine($"  Falhou: {ex.Message}");
                }
            }

            Console.WriteLine($"Concluído: {sucessos}/{arquivosRpt.Length} arquivo(s) convertido(s).");
        }

        private static OpcoesConversao MontarOpcoes(ArgumentosCli argumentos, string caminhoRpt, string caminhoPdf)
        {
            var opcoes = new OpcoesConversao
            {
                CaminhoRpt = caminhoRpt,
                CaminhoPdf = caminhoPdf,
            };

            foreach (var (chave, valor) in argumentos.Parametros)
                opcoes.Parametros[chave] = valor;

            foreach (var (chave, valor) in argumentos.Formulas)
                opcoes.Formulas[chave] = valor;

            opcoes.Login.Servidor = argumentos.DbServidor;
            opcoes.Login.BancoDeDados = argumentos.DbBanco;
            opcoes.Login.Usuario = argumentos.DbUsuario;
            opcoes.Login.Senha = argumentos.DbSenha;

            return opcoes;
        }

        private static void MostrarAjuda()
        {
            Console.WriteLine(string.Join(Environment.NewLine, new[]
            {
                "rpttopdf - converte relatórios Crystal Reports (.rpt) em PDF",
                "",
                "Uso (arquivo único):",
                "  rpttopdf --input <arquivo.rpt> [--output <saida.pdf>]",
                "           [--param Nome=Valor ...] [--formula Nome=Expressao ...]",
                "           [--db-server S --db-name N --db-user U --db-password P]",
                "",
                "Uso (pasta inteira):",
                "  rpttopdf --input-dir <pasta-com-rpts> [--output-dir <pasta-destino>]",
                "",
                "Opções:",
                "  --input <arquivo.rpt>     Caminho do relatório a converter.",
                "  --output <arquivo.pdf>    Caminho do PDF de saída (padrão: mesmo nome, extensão .pdf).",
                "  --input-dir <pasta>       Converte todos os .rpt da pasta (modo lote).",
                "  --output-dir <pasta>      Pasta de destino no modo lote (padrão: mesma pasta de entrada).",
                "  --param Nome=Valor        Define um parâmetro do relatório. Pode repetir.",
                "  --formula Nome=Expressao  Sobrescreve um campo de fórmula. Pode repetir.",
                "  --db-server, --db-name, --db-user, --db-password",
                "                            Credenciais de banco, se o relatório não estiver",
                "                            configurado para conectar sozinho.",
                "  --help                    Mostra esta ajuda.",
                "",
                "Requer: Windows + \"SAP Crystal Reports Runtime Engine for .NET Framework\"",
                "instalado. Veja o README.md na raiz do projeto.",
            }));
        }
    }
}
