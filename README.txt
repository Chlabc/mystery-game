Run the game through the backend server instead of Live Server.

1. Keep your Groq key in `/Users/isi/mystery game/mystery-game/.env` as `GROQ_API_KEY=...`
2. Start the app with `npm start`
3. Open [http://localhost:3000](http://localhost:3000)

This serves the game files and proxies Groq requests through the backend so the API key is not exposed in the browser.
