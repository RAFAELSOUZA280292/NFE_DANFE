import re
import io
import time
import requests
import streamlit as st

# ==============================
# ⚠️ AVISO IMPORTANTE
# DANFE.br.com pode usar métodos não-oficiais.
# Use para testes / POCs. Para produção, prefira provedores oficiais (p.ex. SERPRO) ou amplamente reconhecidos.
# ==============================

API_URL = "http://danfe.br.com/api/nfe/danfe.json"
TIMEOUT = 30

st.set_page_config(page_title="NF-e → XML & DANFE", page_icon="🧾", layout="centered")
st.title("🧾 Consulta NF-e pela Chave de Acesso → XML & DANFE (PDF)")
st.caption("Demo educacional. Forneça a **chave de acesso (44 dígitos)**. O app tenta obter o **XML** e o **DANFE (PDF)**.")

with st.expander("⚠️ Avisos legais e de conformidade", expanded=False):
    st.write(
        "- Este app chama um serviço de terceiros (DANFE.br.com). "
        "Na prática, pode não haver respaldo oficial do fisco para o método de coleta. "
        "Para produção, considere integrações oficiais (p.ex. SERPRO) ou provedores amplamente reconhecidos.\n"
        "- Não armazene dados sensíveis aqui. Use por sua conta e risco."
    )

# Secrets (configure no Streamlit Cloud: Settings → Secrets)
DANFEBR_API_KEY = st.secrets.get("DANFEBR_API_KEY", "")

st.markdown("### 🔧 Configurações")
col1, col2 = st.columns([2, 1])
with col1:
    chave = st.text_input("Chave de Acesso (44 dígitos)", placeholder="Ex.: 3524... (somente números)", max_chars=44)
with col2:
    show_raw_json = st.toggle("Ver retorno JSON bruto", value=False)

st.divider()

def only_digits(s: str) -> str:
    return re.sub(r"\D", "", s or "")

def is_valid_chave(ch: str) -> bool:
    ch = only_digits(ch)
    return len(ch) == 44

def fetch_json(apikey: str, chave_acesso: str) -> dict:
    params = {"apikey": apikey, "chave": only_digits(chave_acesso)}
    r = requests.get(API_URL, params=params, timeout=TIMEOUT)
    # Pode retornar 200 com payload de erro — tratar sempre:
    try:
        data = r.json()
    except Exception:
        r.raise_for_status()
        # Se não for JSON, vai levantar acima; mas por segurança:
        data = {"status_code": r.status_code, "text": r.text}
    data["_http_status"] = r.status_code
    return data

def download_bytes(url: str) -> bytes:
    r = requests.get(url, timeout=TIMEOUT)
    r.raise_for_status()
    return r.content

# Mostrar como configurar segredo se estiver rodando fora do Cloud (apenas info)
if not DANFEBR_API_KEY:
    st.warning("🔐 Configure o segredo `DANFEBR_API_KEY` no Streamlit Cloud (Settings → Secrets) para usar o app.")

agree = st.checkbox("Entendo os riscos e desejo consultar mesmo assim", value=False)

btn = st.button("Consultar NF-e agora", type="primary", use_container_width=True)

if btn:
    if not agree:
        st.error("Você precisa marcar a caixa de confirmação de riscos.")
    elif not DANFEBR_API_KEY:
        st.error("Segredo `DANFEBR_API_KEY` não configurado. No Streamlit Cloud: **Settings → Secrets**.")
    elif not is_valid_chave(chave):
        st.error("Chave de acesso inválida. Deve conter **44 dígitos numéricos**.")
    else:
        with st.status("Consultando serviço... ⏳", expanded=True) as status:
            try:
                st.write("➡️ Enviando requisição à API…")
                t0 = time.time()
                data = fetch_json(DANFEBR_API_KEY, chave)
                elapsed = time.time() - t0
                st.write(f"✅ Retorno em {elapsed:.2f}s (HTTP {data.get('_http_status')})")

                # Mostrar JSON bruto (opcional)
                if show_raw_json:
                    st.subheader("Retorno JSON (bruto)")
                    st.json(data)

                # Normalização de chaves comuns de retorno
                xml_url = data.get("xml") or data.get("xml_url") or data.get("link_xml")
                pdf_url = data.get("danfe") or data.get("pdf") or data.get("link_pdf")

                # Mensagens comuns de erro que alguns serviços retornam
                possible_error = data.get("error") or data.get("message") or data.get("mensagem")

                if not xml_url and not pdf_url:
                    if possible_error:
                        st.error(f"Serviço respondeu com erro: {possible_error}")
                    else:
                        st.error("Não foi possível localizar XML/PDF no retorno da API.")
                    status.update(label="Concluído com erro", state="error")
                else:
                    st.success("Consulta concluída com sucesso.")

                    if xml_url:
                        st.markdown("### 📂 XML da NF-e")
                        try:
                            xml_bytes = download_bytes(xml_url)
                            try:
                                xml_text = xml_bytes.decode("utf-8", errors="ignore")
                            except Exception:
                                xml_text = "<não foi possível decodificar em UTF-8>"
                            st.code(xml_text, language="xml")
                            st.download_button(
                                "⬇️ Baixar XML",
                                data=xml_bytes,
                                file_name=f"{only_digits(chave)}.xml",
                                mime="application/xml",
                                use_container_width=True
                            )
                        except Exception as e:
                            st.error(f"Falha ao baixar/exibir XML: {e}")

                    if pdf_url:
                        st.markdown("### 🧾 DANFE (PDF)")
                        st.markdown(f"[📥 Abrir/baixar DANFE em nova aba]({pdf_url})")
                        try:
                            pdf_bytes = download_bytes(pdf_url)
                            st.download_button(
                                "⬇️ Baixar PDF (DANFE)",
                                data=pdf_bytes,
                                file_name=f"{only_digits(chave)}.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                        except Exception as e:
                            st.warning(f"Não consegui fazer o download direto do PDF agora, mas o link acima está disponível.\n\nDetalhe: {e}")

                    status.update(label="Concluído", state="complete")
            except requests.HTTPError as e:
                st.error(f"Erro HTTP: {e}")
            except requests.Timeout:
                st.error("Tempo esgotado (timeout). Tente novamente.")
            except Exception as e:
                st.error(f"Erro inesperado: {e}")

st.divider()
with st.expander("💡 Dica: Alternativa mais ‘compliance’", expanded=False):
    st.write(
        "Para produção, considere provedores como SERPRO (consulta oficial com e-CNPJ) "
        "ou gateways amplamente reconhecidos. Posso adaptar este app para outra API: "
        "basta você me dizer qual provedor quer usar."
    )
