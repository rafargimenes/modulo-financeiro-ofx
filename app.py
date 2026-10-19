import streamlit as st
import psycopg2
import pandas as pd
import re

DB_HOST = "localhost"
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASSWORD = "unifeob@123"
DB_PORT = "5432"

def obter_conexao():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT
    )

def classificar_categoria(descricao):
    desc = descricao.upper()
    
    if "ENERGIA" in desc or "LUZ" in desc:
        return "Energia Elétrica"
    elif "INTERNET" in desc or "TELEFONE" in desc or "CLOUD" in desc:
        return "Tecnologia / Comunicação"
    elif "ALUGUEL" in desc:
        return "Aluguel / Imóvel"
    elif "FOLHA" in desc or "SALARIO" in desc:
        return "Folha de Pagamento"
    elif "MATERIAL" in desc or "LIMPEZA" in desc:
        return "Insumos e Materiais"
    elif "ESTACIONAMENTO" in desc or "VEICULO" in desc:
        return "Transporte / Manutenção"
    elif "RECEBIMENTO" in desc or "PAGAMENTO CLIENTE" in desc or "PIX" in desc:
        return "Receita de Vendas / Serviços"
    else:
        return "Outros Lançamentos"

def parse_ofx_customizado(conteudo_texto):
    """ Parser manual direto para evitar falha de encoding da biblioteca externa """
    blocos = conteudo_texto.split("<STMTTRN>")
    transacoes = []

    for bloco in blocos[1:]:
        fitid = re.search(r"<FITID>(.*)", bloco)
        dtposted = re.search(r"<DTPOSTED>(\d{8})", bloco)
        trnamt = re.search(r"<TRNAMT>([\d\.-]+)", bloco)
        memo = re.search(r"<MEMO>(.*)", bloco)

        if fitid and dtposted and trnamt and memo:
            data_str = dtposted.group(1)
            data_formatted = f"{data_str[:4]}-{data_str[4:6]}-{data_str[6:8]}"
            valor = float(trnamt.group(1))
            descricao = memo.group(1).strip()
            
            tipo = "ENTRADA" if valor > 0 else "SAÍDA"
            categoria = classificar_categoria(descricao)

            transacoes.append({
                "id_transacao": fitid.group(1).strip(),
                "data_movimentacao": data_formatted,
                "valor": valor,
                "tipo": tipo,
                "categoria": categoria,
                "descricao": descricao
            })

    return transacoes

st.set_page_config(page_title="Módulo Financeiro - ETL OFX", layout="wide")

st.title("🏦 Módulo Financeiro - Processamento e Classificação de OFX")
st.write("Selecione um arquivo .ofx para carregar, categorizar e salvar no banco PostgreSQL.")

if "dados_transacoes" not in st.session_state:
    st.session_state.dados_transacoes = None

arquivo_enviado = st.file_uploader("Escolha o arquivo bancário (.ofx)", type=["ofx"])

if arquivo_enviado is not None:
    try:
        conteudo_bytes = arquivo_enviado.getvalue()
        conteudo_texto = conteudo_bytes.decode('iso-8859-1', errors='replace')
        
        st.session_state.dados_transacoes = parse_ofx_customizado(conteudo_texto)

    except Exception as e:
        st.error(f"Erro ao ler o arquivo: {e}")

if st.session_state.dados_transacoes:
    lista_transacoes = st.session_state.dados_transacoes
    
    entradas = sum(t["valor"] for t in lista_transacoes if t["valor"] > 0)
    saidas = sum(t["valor"] for t in lista_transacoes if t["valor"] < 0)
    total_movimentacoes = len(lista_transacoes)
    saldo_calculado = entradas + saidas

    st.subheader("📊 Resumo do Extrato")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Movimentações", total_movimentacoes)
    c2.metric("Total Entradas", f"R$ {entradas:,.2f}")
    c3.metric("Total Saídas", f"R$ {saidas:,.2f}")
    c4.metric("Saldo Calculado", f"R$ {saldo_calculado:,.2f}")

    st.subheader("📋 Lançamentos Classificados")
    df = pd.DataFrame(lista_transacoes)
    st.dataframe(df, use_container_width=True)

    st.markdown("---")
    if st.button("💾 Gravar no PostgreSQL", type="primary"):
        try:
            conexao = obter_conexao()
            cursor = conexao.cursor()

            inseridos = 0
            duplicados = 0

            sql = """
                INSERT INTO movimentacoes (id_transacao, data_movimentacao, valor, tipo, categoria, descricao)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id_transacao) DO NOTHING;
            """

            for item in lista_transacoes:
                cursor.execute(sql, (
                    item["id_transacao"],
                    item["data_movimentacao"],
                    item["valor"],
                    item["tipo"],
                    item["categoria"],
                    item["descricao"]
                ))
                if cursor.rowcount > 0:
                    inseridos += 1
                else:
                    duplicados += 1

            conexao.commit()
            cursor.close()
            conexao.close()

            st.success("✅ Operação finalizada com sucesso!")
            st.info(f"🟢 **{inseridos}** registros novos salvos no PostgreSQL.\n🔴 **{duplicados}** registros repetidos ignorados (sem duplicidade).")

        except Exception as e:
            st.error(f"Erro ao gravar no banco de dados: {e}")

st.markdown("---")
st.subheader("🗄️ Registros Gravados no PostgreSQL")

if st.button("🔄 Consultar Tabela do Banco"):
    try:
        conexao = obter_conexao()
        df_banco = pd.read_sql("SELECT * FROM movimentacoes ORDER BY data_movimentacao ASC", conexao)
        conexao.close()

        if not df_banco.empty:
            st.dataframe(df_banco, use_container_width=True)
        else:
            st.warning("A tabela está vazia no momento.")
    except Exception as e:
        st.error(f"Erro ao consultar o banco de dados: {e}")