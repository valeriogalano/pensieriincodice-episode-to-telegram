<div align="center">
  <img src="https://cdn.pensieriincodice.it/images/pensieriincodice-locandina.png" alt="Logo Progetto" width="150"/>
  <h1>Pensieri In Codice — Episode to Telegram</h1>
  <p>GitHub Action che invia automaticamente i nuovi episodi del podcast a un gruppo o canale Telegram.</p>
  <p>
    <img src="https://img.shields.io/github/stars/valeriogalano/pensieriincodice-episode-to-telegram?style=for-the-badge" alt="GitHub Stars"/>
    <img src="https://img.shields.io/github/forks/valeriogalano/pensieriincodice-episode-to-telegram?style=for-the-badge" alt="GitHub Forks"/>
    <img src="https://img.shields.io/github/last-commit/valeriogalano/pensieriincodice-episode-to-telegram?style=for-the-badge" alt="Last Commit"/>
    <a href="https://pensieriincodice.it/sostieni" target="_blank" rel="noopener noreferrer">
      <img src="https://img.shields.io/badge/sostieni-Pensieri_in_codice-fb6400?style=for-the-badge" alt="Sostieni Pensieri in codice"/>
    </a>
  </p>
</div>

---

## Come funziona

Il workflow viene eseguito ogni ora tra le 7:00 e le 18:00. Per ogni podcast configurato, controlla il feed RSS alla ricerca di nuovi episodi. Gli episodi già pubblicati vengono tracciati in un file `published_episodes_{podcast_id}.txt` per evitare duplicati. Il workflow può essere attivato anche manualmente dalla scheda Actions.

---

## Requisiti

- Un bot Telegram (creabile tramite [@BotFather](https://t.me/botfather))
- L'ID del gruppo o canale Telegram di destinazione
- Uno o più feed RSS di podcast

---

## Installazione e configurazione

### 1. Clona la repository

```bash
git clone https://github.com/YOUR_USERNAME/pensieriincodice-episode-to-telegram.git
cd pensieriincodice-episode-to-telegram
```

### 2. Configura i secrets di GitHub Actions

In **Settings → Secrets and variables → Actions**, aggiungi il seguente **Secret**:

| Secret | Descrizione |
|---|---|
| `TELEGRAM_BOT_API_KEY` | Token del bot Telegram (da [@BotFather](https://t.me/botfather)) |

### 3. Configura le variabili di GitHub Actions

Nella stessa sezione, sotto la scheda **Variables**, aggiungi:

| Variabile | Descrizione |
|---|---|
| `TELEGRAM_CHAT_ID` | ID del gruppo o canale Telegram (usa [@getidsbot](https://t.me/getidsbot)) |
| `PODCAST1_RSS_URL` | URL del feed RSS del primo podcast |
| `PODCAST1_TEMPLATE` | Template del messaggio per il primo podcast |
| `PODCAST2_RSS_URL` | URL del feed RSS del secondo podcast |
| `PODCAST2_TEMPLATE` | Template del messaggio per il secondo podcast |

### 4. Template del messaggio

I placeholder disponibili sono `{title}` e `{link}`. Il bot usa il formato MarkdownV2 di Telegram; i caratteri speciali vengono escaped automaticamente. Esempio:

```
🎙️ Nuovo episodio di Pensieri in Codice!

*{title}*

Ascoltalo qui: {link}
```

### 5. Aggiungere altri podcast

Modifica `.github/workflows/cron.yml` e aggiungi nuove configurazioni nello step "Create podcasts config":

```php
[
  "id" => "miopodcast",
  "name" => "Il mio podcast",
  "feed_url" => getenv("PODCAST3_RSS_URL"),
  "template" => getenv("PODCAST3_TEMPLATE")
]
```

Aggiungi poi le variabili corrispondenti (`PODCAST3_RSS_URL`, `PODCAST3_TEMPLATE`) in GitHub Actions.

---

## Contributi

Se noti qualche problema o hai suggerimenti, sentiti libero di aprire una **Issue** e successivamente una **Pull Request**. Ogni contributo è ben accetto!

---

## Importante

Vorremmo mantenere questo repository aperto e gratuito per tutti, ma lo scraping del contenuto di questo repository **NON È CONSENTITO**. Se ritieni che questo lavoro ti sia utile e vuoi utilizzare qualche risorsa, ti preghiamo di citare come fonte il podcast e/o questo repository.

---

<div align="center">
  <p>Realizzato con ❤️ da <strong>Valerio Galano</strong></p>
  <p>
    <a href="https://valeriogalano.it/">Sito Web</a> |
    <a href="https://daredevel.com/">Blog</a> |
    <a href="https://pensieriincodice.it/">Podcast</a>
  </p>
</div>
