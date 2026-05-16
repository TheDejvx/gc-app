# GC App – Gentlemen Challenge

## Project
Flask + vanilla JS scoring app for annual 3-klan golf/shooting/dart competition.
- **Live:** https://gc-app-sascheckin.up.railway.app
- **Repo:** https://github.com/TheDejvx/gc-app
- **Local:** `C:\Users\David\Desktop\GC\gc-app\`
- **Run locally:** `python app.py` → http://localhost:5001

## Stack
- Backend: Python/Flask, served with Waitress on Railway
- Frontend: Single-page HTML/JS (templates/index.html), no build step
- Data: MongoDB Atlas (`gc_app` database, `gc_state` collection), fallback to `gc_data.json`
- Deploy: push to `main` → Railway auto-deploys

## GC1 – 2v2 Scramble Feature (2026+)

### Format
- Each klan plays against every other klan (3 matchups: Selander–Norrby, Selander–Lyrinder, Norrby–Lyrinder)
- Each matchup = 2 rounds of 9 holes
- Points per round: Win = 3, Draw = 1.5 each, Loss = 0
- Scramble enabled/disabled per year via toggle (`scramble_enabled` flag in data)

### Course: Nässjö GK
- Slope: 121 | Course Rating: 70.7 | Par 18: 72 | Par 9: 36
- For 9-hole rounds: slope = 121, course rating = 35.35 (half of 70.7), par = 36
- Spelhandicap formula: `round(HCP_index × (121 ÷ 113) + (CR − par))`
  - For 18h: `round(hcp × 1.0708 + (70.7 − 72))` = `round(hcp × 1.0708 − 1.3)`
  - For 9h use half CR and half par (same slope): `round(hcp × 1.0708 + (35.35 − 36))`

### SGF 2-Man Scramble Team HCP (confirmed SGF formula)
1. Calculate each player's spelhandicap using Nässjö slope
2. Team HCP = `round(lower_spelHCP × 0.5 + higher_spelHCP × 0.2)`
3. For 9-hole play: use half the team HCP (round to nearest 0.5 or whole)

### Data model additions (per year object)
```json
{
  "scramble_enabled": true,
  "scramble_course": "nassjo_gk",
  "scramble_matches": [
    {
      "id": "selander_norrby",
      "klanA": "selander",
      "klanB": "norrby",
      "playersA": ["David Selander", "Joacim Rustas"],
      "playersB": ["Magnus Norrby", "Christopher Eklund"],
      "rounds": [
        { "scoreA": null, "scoreB": null },
        { "scoreA": null, "scoreB": null }
      ]
    }
  ]
}
```

### UI additions
- Toggle "Aktivera Scramble" (stored per year, hidden if off)
- Scramble section below klan cards: one card per matchup
- Each card: player dropdowns (from klan roster), calculated team HCP, score inputs per round, auto-calculated points
- Scramble points added to klan total in rankings

### Other features (GC1)
- **Auto-save:** debounced (800ms) on every input change — no need to click Spara
- **Create new year:** button copies teams/players/settings, resets all scores
- **Delete year:** only allowed if year has zero manually entered data (all fields null/empty)

## Klaner
- Klan Selander – green (#2e7d32)
- Klan Norrby – blue (#1565c0)
- Klan Lyrinder – red (#b71c1c)
