# 🏦 Módulo Financeiro - ETL e Classificação de Extratos OFX

Projeto desenvolvido em Python para leitura, categorização automática e armazenamento de movimentações financeiras em banco de dados PostgreSQL.

## 🚀 Tecnologias Utilizadas
- **Python 3**
- **Streamlit** (Interface Web)
- **PostgreSQL** (Banco de Dados Relacional)
- **Psycopg2 e Pandas**

## 📌 Funcionalidades
- Upload dinâmico de arquivos bancários no formato `.ofx`
- Leitura de dados com tratamento para caracteres especiais (ISO-8859-1)
- Classificação automática por categoria de gasto/receita
- Cálculo e exibição do resumo financeiro (Entradas, Saídas e Saldo)
- Gravação dos dados no PostgreSQL com prevenção de duplicidade (`ON CONFLICT DO NOTHING`)