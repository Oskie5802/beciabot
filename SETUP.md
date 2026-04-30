# Becia – Bot Statutowy | Instrukcja wdrożenia

## Wymagania

- Konto Discord (Developerskie: discord.com/developers)
- Konto Google (do Gemini API)
- Konto na Render.com (darmowy hosting)
- Konto na GitHub (do deploymentu)

---

## Krok 1 – Stwórz bota na Discordzie

1. Wejdź na https://discord.com/developers/applications
2. Kliknij **New Application** → nadaj nazwę (np. "Becia")
3. Przejdź do zakładki **Bot** → kliknij **Add Bot**
4. W sekcji **Privileged Gateway Intents** włącz:
   - `SERVER MEMBERS INTENT`
   - `MESSAGE CONTENT INTENT`
5. Kliknij **Reset Token** i **skopiuj token** → to jest `DISCORD_TOKEN`
6. Przejdź do **OAuth2 → URL Generator**:
   - Zaznacz scope: `bot`, `applications.commands`
   - Zaznacz permissions: `Send Messages`, `Embed Links`, `Read Message History`, `Use Slash Commands`
   - Skopiuj wygenerowany URL i wejdź na niego, żeby dodać bota do serwera

---

## Krok 2 – Pobierz klucz Gemini API (darmowy)

1. Wejdź na https://aistudio.google.com/app/apikey
2. Zaloguj się kontem Google
3. Kliknij **Create API Key**
4. Skopiuj klucz → to jest `GEMINI_API_KEY`

**Darmowy limit:** 15 zapytań/minutę, 1 milion tokenów/dzień — wystarczy w zupełności.

---

## Krok 3 – Wrzuć kod na GitHub

```bash
cd /Users/oskar/Desktop/beciabot
git init
git add .
git commit -m "Becia bot"
# Stwórz repo na github.com, potem:
git remote add origin https://github.com/TWOJ_NICK/beciabot.git
git push -u origin main
```

---

## Krok 4 – Deploy na Render.com (darmowy, 24/7)

1. Wejdź na https://render.com i zaloguj się przez GitHub
2. Kliknij **New → Web Service**
3. Wybierz swoje repozytorium `beciabot`
4. Ustaw:
   - **Environment:** `Docker`
   - **Region:** Frankfurt (bliżej Polski)
   - **Instance Type:** `Free`
5. W sekcji **Environment Variables** dodaj:
   - `DISCORD_TOKEN` = (twój token bota)
   - `GEMINI_API_KEY` = (twój klucz Gemini)
6. Kliknij **Create Web Service**

---

## Krok 5 – Keep-alive (żeby bot nie zasypiał)

Render.com na darmowym planie usypia serwis po 15 minutach braku ruchu HTTP.
Bot ma wbudowany serwer HTTP na porcie 8080.

Skonfiguruj darmowy ping na https://uptimerobot.com:
1. Zarejestruj się
2. **New Monitor** → **HTTP(s)**
3. URL: `https://NAZWA-TWOJEGO-SERWISU.onrender.com`
4. Interval: **5 minutes**

To wystarczy, żeby bot działał 24/7.

---

## Użycie bota

| Komenda | Opis |
|---------|------|
| `!szukaj <pytanie>` | Szuka w statucie i odpowiada |
| `/szukaj <pytanie>` | To samo, ale jako slash command |
| `!pomoc` | Wyświetla pomoc |
| `@Becia <pytanie>` | Możesz też tagować bota bezpośrednio |

### Przykłady pytań:
- `!szukaj jakie są prawa ucznia?`
- `!szukaj ile nieusprawiedliwionych godzin można mieć?`
- `!szukaj jak wygląda rekrutacja do szkoły?`
- `!szukaj kiedy można dostać stypendium?`
- `!szukaj co robi samorząd uczniowski?`

---

## Jak działa bez internetu (tryb offline)

Jeśli nie podasz `GEMINI_API_KEY`, bot nadal działa – zwraca najlepiej pasujący
fragment ze statutu bez przetwarzania przez AI.
