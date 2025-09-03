# NF-e → XML & DANFE (Streamlit)

App **100% online** para consultar **XML** e **DANFE (PDF)** de NF-e pela **chave de acesso (44 dígitos)**, usando a API do DANFE.br.com.

> ⚠️ Aviso: uso apenas educativo/POC. Para produção, prefira integrações oficiais (SERPRO) ou provedores amplamente reconhecidos.

## Como usar (100% online)

1. **Crie um repositório no GitHub** e adicione `app.py` e `requirements.txt`.
2. **Faça o deploy no Streamlit Cloud** (share.streamlit.io) conectando seu GitHub.
3. Em **Settings → Secrets** do app, adicione:
   - `DANFEBR_API_KEY` com sua chave da API.

Pronto. Abra o app e consulte pela chave de acesso (44 dígitos).

## Segredos
- `DANFEBR_API_KEY`: sua chave de API do DANFE.br.com.

## Observações
- O app não armazena dados; apenas consome o endpoint e, se possível, baixa os arquivos.
- Caso o provedor mude o formato do JSON, ajuste as chaves em `xml_url`/`danfe`.
