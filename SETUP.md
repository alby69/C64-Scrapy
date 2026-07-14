# Setup Pipeline CI/CD

Procedura per configurare la pipeline automatica che sincronizza i dati scraped con il repo [C64-KB-Agent](https://github.com/alby69/C64-KB-Agent).

## 1. Creare il Personal Access Token

1. Vai su **https://github.com/settings/tokens**
2. Clicca **"Generate new token (classic)"**
3. Compila:
   - **Note**: `C64-Scrapy CI/CD`
   - **Expiration**: 90 giorni (o più)
   - **Scope**: seleziona **`repo`** (tutto il blocco)
4. Clicca **"Generate token"**
5. **Copia subito il token** (inizia con `ghp_...`), non potrà più essere visto

## 2. Aggiungere il secret al repo C64-Scrapy

1. Vai su **https://github.com/alby69/C64-Scrapy/settings/secrets/actions**
2. Clicca **"New repository secret"**
3. Compila:
   - **Name**: `KB_AGENT_TOKEN`
   - **Secret**: incolla il token `ghp_...`
4. Clicca **"Add secret"**

## 3. Lanciare la Action

### Manuale
1. Vai su **https://github.com/alby69/C64-Scrapy/actions**
2. Seleziona **"Scrape and Sync"**
3. Clicca **"Run workflow"**
4. Opzionale: specifica gli spider (es. `codebase64,bbcelite`) o lascia `all`
5. Clicca **"Run workflow"**

### Automatica
La Action parte automaticamente ogni **lunedì alle 06:00 UTC**.

## 4. Verificare il risultato

1. Dopo l'esecuzione, controlla il repo **https://github.com/alby69/C64-KB-Agent**
2. I dati saranno in `data/docs/` e `data/dataset/`
3. Il commit avrà il messaggio `chore: update scraped data (YYYY-MM-DD)`

## Note

- Il token va rigenerato prima della scadenza
- Se la Action fallisce per "Permission denied", il token è scaduto o non ha lo scope `repo`
- Lo scraping richiede circa 10-15 minuti
