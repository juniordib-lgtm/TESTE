using System;
using System.Collections.Generic;

namespace RptToPdf
{
    internal sealed class ArgumentosCli
    {
        public string? CaminhoEntrada { get; private set; }
        public string? CaminhoSaida { get; private set; }
        public string? PastaEntrada { get; private set; }
        public string? PastaSaida { get; private set; }
        public string? DbServidor { get; private set; }
        public string? DbBanco { get; private set; }
        public string? DbUsuario { get; private set; }
        public string? DbSenha { get; private set; }

        public List<(string Chave, string Valor)> Parametros { get; } = new();
        public List<(string Chave, string Valor)> Formulas { get; } = new();

        public bool ModoLote => !string.IsNullOrEmpty(PastaEntrada);

        public static ArgumentosCli Analisar(string[] args)
        {
            var resultado = new ArgumentosCli();

            for (var i = 0; i < args.Length; i++)
            {
                switch (args[i])
                {
                    case "--input":
                        resultado.CaminhoEntrada = ProximoValor(args, ref i, "--input");
                        break;
                    case "--output":
                        resultado.CaminhoSaida = ProximoValor(args, ref i, "--output");
                        break;
                    case "--input-dir":
                        resultado.PastaEntrada = ProximoValor(args, ref i, "--input-dir");
                        break;
                    case "--output-dir":
                        resultado.PastaSaida = ProximoValor(args, ref i, "--output-dir");
                        break;
                    case "--db-server":
                        resultado.DbServidor = ProximoValor(args, ref i, "--db-server");
                        break;
                    case "--db-name":
                        resultado.DbBanco = ProximoValor(args, ref i, "--db-name");
                        break;
                    case "--db-user":
                        resultado.DbUsuario = ProximoValor(args, ref i, "--db-user");
                        break;
                    case "--db-password":
                        resultado.DbSenha = ProximoValor(args, ref i, "--db-password");
                        break;
                    case "--param":
                        resultado.Parametros.Add(AnalisarParChaveValor(ProximoValor(args, ref i, "--param")));
                        break;
                    case "--formula":
                        resultado.Formulas.Add(AnalisarParChaveValor(ProximoValor(args, ref i, "--formula")));
                        break;
                    default:
                        throw new ArgumentException($"Argumento desconhecido: {args[i]}");
                }
            }

            return resultado;
        }

        private static string ProximoValor(string[] args, ref int indice, string nomeOpcao)
        {
            if (indice + 1 >= args.Length)
                throw new ArgumentException($"A opção {nomeOpcao} exige um valor.");
            indice++;
            return args[indice];
        }

        private static (string, string) AnalisarParChaveValor(string texto)
        {
            var posicao = texto.IndexOf('=');
            if (posicao <= 0)
                throw new ArgumentException($"Formato inválido, use Nome=Valor: '{texto}'");
            return (texto[..posicao], texto[(posicao + 1)..]);
        }
    }
}
