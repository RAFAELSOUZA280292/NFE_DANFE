import re
import time
import requests
import streamlit as st

st.set_page_config(page_title="Meu Danfe → XML & DANFE", page_icon="🧾", layout="centered")
st.title("🧾 Consulta NF-e pela chave → XML & DANFE (Meu Danfe)")

# ====== Ajuda rápida ======
with st.expander("Como conseguir a API Key do Meu Danfe?"):
    st.markdown(
        "- Acesse **web.meudanfe.com.br** → faça login → **API / Integração** → **Criar NOVA** (gera a chave)."
        "\n- Use essa chave no campo **API Key** abaixo."
    )

# ====== Config ======
colA, colB = st.columns([2, 1])
with colA:
    # Deixe este endpoint exatamente como o painel do Meu Danfe informar.
    base_url = st.text_input(
        "Endpoint da API (copie do painel do Meu Danfe)",
        value="https://web.meudanfe.com.br/api/v1/nfe",  # valor padrão sugerido; ajuste conforme painel
        help="Cole aqui o endpoint que aparece na sua Área do Cliente (API/Integração)."
    )
with colB:
    http_method = st.selectbox("Método HTTP", ["GET", "POST"], index=0)

api_key = st.text_input("API Key (Authorization)", type="password", help="Cole a API Key criada no Meu Danfe")
header_name = st.text_input("Nome do header de auth", value="Authorization")
param_name = st.text_input("Parâmetro da chave de acesso", value="chave")
show_json = st.toggle("Mostrar JSON bruto de resposta", value=False)

st.divider()

# ====== Entrada da chave de acesso ======
chave = st.text_input("Chave de acesso (44 dígitos)", placeholder="Somente números", max_chars=44)

def only_digits(s: str) -> str:
    return re.sub(r"\D", "", s or "")

def valid_chave(s: str) -> bool:
    return len(only_digits(s)) == 44

def do_request():
    headers = {}
    if api_key:
        headers[header_name] = api_key

    params = {param_name: only_digits(chave)} if http_method == "GET" else None
    data   = {param_name: only_digits(chave)} if http_method == "POST" else None

    t0 = time.time()
    if http_method == "GET":
        r = requests.get(base_url, params=params, headers=headers, timeout=40)
    else:
        r = requests.post(base_url, json=data, headers=headers, timeout=40)
    elapsed = time.time() - t0

    try:
        payload = r.json()
    except Exception:
        payload = {"_raw": r.text}
    payload["_http_status"] = r.status_code
    payload["_elapsed_sec"] = round(elapsed, 3)
    return payload

def download_bytes(url: str) -> bytes:
    r = requests.get(url, timeout=40)
    r.raise_for_status()
    return r.content

if st.button("Consultar agora", type="primary", use_container_width=True):
    if not api_key:
        st.error("Informe a **API Key** (Authorization) gerada no Meu Danfe.")
    elif not valid_chave(chave):
        st.error("A chave de acesso deve ter **44 dígitos numéricos**.")
    elif not base_url.lower().startswith("http"):
        st.error("Endpoint inválido. Cole a URL exata do painel do Meu Danfe.")
    else:
        with st.status("Consultando Meu Danfe…", expanded=True) as s:
            try:
                s.write("➡️ Enviando requisição…")
                resp = do_request()
                s.write(f"HTTP {resp.get('_http_status')} em {resp.get('_elapsed_sec')}s")

                if show_json:
                    st.subheader("JSON bruto")
                    st.json(resp)

                # Tentamos mapear campos comuns (ajuste se o painel indicar nomes exatos)
                xml_url = (resp.get("xml") or resp.get("xml_url") or resp.get("link_xml") or resp.get("url_xml"))
                pdf_url = (resp.get("pdf") or resp.get("danfe") or resp.get("link_pdf") or resp.get("url_pdf"))
                msg_err = resp.get("error") or resp.get("message") or resp.get("mensagem")

                if not xml_url and not pdf_url:
                    st.error(f"Não localizei URLs de XML/PDF no retorno. Detalhe: {msg_err or 'verifique endpoint e parâmetros no painel'}")
                    s.update(label="Concluído com erro", state="error")
                else:
                    st.success("Consulta concluída com sucesso.")

                    if xml_url:
                        st.markdown("### 📂 XML")
                        try:
                            xml_bytes = download_bytes(xml_url)
                            st.code(xml_bytes.decode("utf-8", errors="ignore"), language="xml")
                            st.download_button(
                                "⬇️ Baixar XML",
                                data=xml_bytes,
                                file_name=f"{only_digits(chave)}.xml",
                                mime="application/xml",
                                use_container_width=True
                            )
                        except Exception as e:
                            st.warning(f"Falha ao baixar/exibir XML: {e}")

                    if pdf_url:
                        st.markdown("### 🧾 DANFE (PDF)")
                        st.markdown(f"[Abrir/baixar em nova aba]({pdf_url})")
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
                            st.info(f"Se o download direto falhar, use o link acima. Detalhe: {e}")

                    s.update(label="Concluído", state="complete")
            except requests.Timeout:
                st.error("Tempo esgotado (timeout). Tente novamente.")
            except requests.HTTPError as e:
                st.error(f"Erro HTTP: {e}")
            except Exception as e:
                st.error(f"Erro inesperado: {e}")
