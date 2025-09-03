import streamlit as st
import requests

# URL base da API DANFE.br.com
API_URL = "http://danfe.br.com/api/nfe/danfe.json"

st.set_page_config(page_title="Consulta NF-e DANFE", page_icon="📄", layout="centered")

st.title("📄 Consulta NF-e pela Chave de Acesso")
st.markdown("Digite a chave de acesso abaixo e obtenha o **XML** e o **DANFE (PDF)**.")

# Input da chave de acesso
chave_acesso = st.text_input("🔑 Chave de Acesso da NF-e (44 dígitos)", "")

# Input da API Key
apikey = st.text_input("🔐 API Key do DANFE.br.com", type="password")

if st.button("Consultar Nota"):
    if not chave_acesso or not apikey:
        st.error("⚠️ Informe a chave de acesso e sua API Key.")
    else:
        try:
            # Faz a requisição
            params = {"apikey": apikey, "chave": chave_acesso}
            response = requests.get(API_URL, params=params)

            if response.status_code == 200:
                data = response.json()

                # Exibir informações
                st.success("✅ Nota encontrada!")
                if "xml" in data:
                    st.markdown("### 📂 XML da Nota")
                    st.code(requests.get(data["xml"]).text, language="xml")
                    st.download_button("⬇️ Baixar XML", requests.get(data["xml"]).content, "nota.xml")

                if "danfe" in data:
                    st.markdown("### 🧾 DANFE (PDF)")
                    st.markdown(f"[📥 Clique aqui para baixar o DANFE]({data['danfe']})")

            else:
                st.error(f"❌ Erro ao consultar. Código: {response.status_code}")
        except Exception as e:
            st.error(f"Erro: {str(e)}")
