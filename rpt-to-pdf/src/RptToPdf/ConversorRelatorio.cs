using System;
using System.Collections.Generic;
using System.IO;
using CrystalDecisions.CrystalReports.Engine;
using CrystalDecisions.Shared;

namespace RptToPdf
{
    /// <summary>
    /// Dados de login no banco usados pelo relatório, quando ele não estiver
    /// configurado para se conectar sozinho (relatórios com fonte de dados
    /// embutida/salva não precisam disso).
    /// </summary>
    public sealed class LoginBancoDados
    {
        public string? Servidor { get; set; }
        public string? BancoDeDados { get; set; }
        public string? Usuario { get; set; }
        public string? Senha { get; set; }

        public bool TemDados =>
            !string.IsNullOrEmpty(Servidor) || !string.IsNullOrEmpty(BancoDeDados) ||
            !string.IsNullOrEmpty(Usuario) || !string.IsNullOrEmpty(Senha);
    }

    public sealed class OpcoesConversao
    {
        public string CaminhoRpt { get; set; } = string.Empty;
        public string CaminhoPdf { get; set; } = string.Empty;
        public Dictionary<string, string> Parametros { get; } = new(StringComparer.OrdinalIgnoreCase);
        public Dictionary<string, string> Formulas { get; } = new(StringComparer.OrdinalIgnoreCase);
        public LoginBancoDados Login { get; } = new();
    }

    /// <summary>
    /// Encapsula a abertura de um .rpt pelo motor do Crystal Reports e a
    /// exportação para PDF. Precisa do "SAP Crystal Reports Runtime Engine
    /// for .NET Framework" instalado na máquina (ver README).
    /// </summary>
    public static class ConversorRelatorio
    {
        public static void ConverterParaPdf(OpcoesConversao opcoes)
        {
            if (!File.Exists(opcoes.CaminhoRpt))
                throw new FileNotFoundException($"Arquivo .rpt não encontrado: {opcoes.CaminhoRpt}");

            var pastaSaida = Path.GetDirectoryName(Path.GetFullPath(opcoes.CaminhoPdf));
            if (!string.IsNullOrEmpty(pastaSaida) && !Directory.Exists(pastaSaida))
                Directory.CreateDirectory(pastaSaida);

            using var documento = new ReportDocument();
            documento.Load(opcoes.CaminhoRpt);

            try
            {
                if (opcoes.Login.TemDados)
                    AplicarLoginBancoDados(documento, opcoes.Login);

                foreach (var par in opcoes.Parametros)
                    AplicarParametro(documento, par.Key, par.Value);

                foreach (var par in opcoes.Formulas)
                    documento.DataDefinition.FormulaFields[par.Key].Text = par.Value;

                documento.ExportToDisk(ExportFormatType.PortableDocFormat, opcoes.CaminhoPdf);
            }
            finally
            {
                documento.Close();
            }
        }

        private static void AplicarLoginBancoDados(ReportDocument documento, LoginBancoDados login)
        {
            foreach (Table tabela in documento.Database.Tables)
            {
                var infoConexao = tabela.LogOnInfo.ConnectionInfo;

                if (!string.IsNullOrEmpty(login.Servidor)) infoConexao.ServerName = login.Servidor;
                if (!string.IsNullOrEmpty(login.BancoDeDados)) infoConexao.DatabaseName = login.BancoDeDados;
                if (!string.IsNullOrEmpty(login.Usuario)) infoConexao.UserID = login.Usuario;
                if (login.Senha != null) infoConexao.Password = login.Senha;

                tabela.ApplyLogOnInfo(tabela.LogOnInfo);
            }

            // Subrelatórios têm suas próprias tabelas e login.
            foreach (ReportDocument subRelatorio in documento.Subreports)
                AplicarLoginBancoDados(subRelatorio, login);
        }

        private static void AplicarParametro(ReportDocument documento, string nome, string valor)
        {
            var campoParametro = EncontrarCampoParametro(documento, nome)
                ?? throw new ArgumentException($"Parâmetro '{nome}' não existe no relatório.");

            var valorConvertido = ConverterValorParametro(campoParametro, valor);
            documento.SetParameterValue(campoParametro.Name, valorConvertido);
        }

        private static ParameterFieldDefinition? EncontrarCampoParametro(ReportDocument documento, string nome)
        {
            foreach (ParameterFieldDefinition campo in documento.DataDefinition.ParameterFields)
                if (string.Equals(campo.Name, nome, StringComparison.OrdinalIgnoreCase))
                    return campo;
            return null;
        }

        private static object ConverterValorParametro(ParameterFieldDefinition campo, string valorTexto)
        {
            return campo.ValueType switch
            {
                FieldValueType.NumberField or FieldValueType.CurrencyField => double.Parse(valorTexto,
                    System.Globalization.CultureInfo.InvariantCulture),
                FieldValueType.BooleanField => bool.Parse(valorTexto),
                FieldValueType.DateField => DateTime.Parse(valorTexto, System.Globalization.CultureInfo.InvariantCulture),
                FieldValueType.DateTimeField => DateTime.Parse(valorTexto, System.Globalization.CultureInfo.InvariantCulture),
                _ => valorTexto,
            };
        }
    }
}
