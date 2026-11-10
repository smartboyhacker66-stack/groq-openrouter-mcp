# Groq + OpenRouter + Kotlin MCP Server  (Docker ki zaroorat nahi)

Do tareeke hain. **Tareeka A** (laptop par) sabse aasaan hai. **Tareeka B** (Render) ek baar karo to laptop band rakh sakte ho.

---------------------------------------------------------------------

## Tareeka A: Laptop par chalao (Windows)

### Ek baar ka setup
1. **Python install** karo: https://www.python.org/downloads/  ->  install me **"Add python.exe to PATH" tick** zaroor karna.
2. **(Optional, sirf Kotlin check ke liye)**
   - JDK 17: PowerShell me  `winget install EclipseAdoptium.Temurin.17.JDK`
   - kotlinc: https://github.com/JetBrains/kotlin/releases  se `kotlin-compiler-2.0.21.zip` download -> extract karo -> uske `kotlinc\bin` folder ko Windows PATH me jodo.
   - Ye na karo to baaki sab tools chalenge, bas `kotlin_check` "kotlinc nahi mila" bolega.

### Server chalao
1. ZIP ko **Extract** karo (zip ke andar se mat chalao).
2. **start_server.bat** double-click karo.
3. **API key yahin maangega** (sirf pehli baar):
   - `Groq API key paste karo:`  -> https://console.groq.com/keys se banao
   - `OpenRouter API key paste karo:` -> https://openrouter.ai/keys se banao
   - Jo nahi hai us par Enter. Keys `.env` file me save ho jati hain, dobara nahi poochega.
   - `MCP_SECRET` (aapka fixed token) script **khud bana deti hai**.
4. Packages install hone do. Phir window me aisa dikhega:
   ```
   Connector path : /s/AbCd...XyZ/mcp
   ```
   Ye **path copy** karke rakho.
5. Browser me `http://localhost:8000/health` kholo -> `"status":"ok"` dikhna chahiye.

### Internet par lao (Claude ko tumhare laptop tak pahunchne ke liye zaroori)
Claude ka connector `localhost` nahi dekh sakta, isliye tunnel chahiye.
1. **start_tunnel.bat** double-click karo (pehli baar `cloudflared` khud install karega, phir bolega "dobara chalao").
2. Window me ye link aayega: `https://kuch-random-naam.trycloudflare.com` -> **copy** karo.
3. **Final URL** = tunnel link + connector path, jaise:
   `https://kuch-random-naam.trycloudflare.com/s/AbCd...XyZ/mcp`

Dhyan: dono windows (server + tunnel) khuli rahni chahiye aur laptop on. Tunnel ka link **har restart par badalta hai**, tab connector ka URL naya daalna padega. Fixed link chahiye to Tareeka B lo.

---------------------------------------------------------------------

## Tareeka B: Render par deploy (fixed URL, laptop band ho to bhi chalega)

Laptop me Docker nahi chahiye, Render apne server par khud build karta hai.

1. **Git** install karo: https://git-scm.com/download/win  aur **GitHub CLI**: https://cli.github.com
2. **deploy_to_render.bat** double-click karo. Ye khud:
   - GitHub login karwata hai (`gh auth login`, browser me allow kar do)
   - naya repo banata hai aur code push karta hai (repo **public** hota hai, `.env`/keys push nahi hoti)
   - Render ka deploy page browser me khol deta hai
3. **Render page par API keys yahin maangega**: `GROQ_API_KEY` aur `OPENROUTER_API_KEY` paste karo -> **Apply / Deploy Blueprint**.
4. 5-10 minute baad `https://<naam>.onrender.com/health` kholo -> `status: ok`.
5. Render me service -> **Environment** tab -> `MCP_SECRET` ki value copy karo.
6. **Final URL** = `https://<naam>.onrender.com/s/<MCP_SECRET>/mcp`

Render free plan: 15 minute idle ke baad so jata hai, pehla request ~50 second leta hai. Pehle `/health` khol kar jagao.

---------------------------------------------------------------------

## Claude me connect karna (mobile ke liye)

Connector **claude.ai (web ya desktop)** se jodo, wahi account mobile app me apne aap aa jayega.

1. https://claude.ai kholo (same account jo mobile me hai).
2. **Settings -> Connectors -> Add custom connector**.
3. **Name**: `Groq-OpenRouter-Kotlin`
4. **URL**: ooper wala **Final URL** (poora, `/s/.../mcp` samet).
5. **Advanced / OAuth Client ID & Secret: khali chhodo.** (Yahi "bina sign-in" wala tareeka hai, isse 401 nahi aata.)
6. **Add** dabao. Agar "Connect" ka button aaye to dabao.
7. **Mobile app** kholo -> naya chat -> tools/connectors menu me is connector ko **ON** karo.
8. Test karo:
   - "ask_groq se bolo: hello"
   - "kotlin_check se ye compile karo: fun main() { println(1) }"

(Custom connector milega ya nahi, ye aapke plan par depend kar sakta hai. Option na dikhe to support.claude.com dekho.)

---------------------------------------------------------------------

## Error aaye to

| Dikkat | Kaaran / Hal |
|---|---|
| 401 / "auth" error | URL me `/s/<token>/mcp` poora aur sahi hona chahiye. OAuth ke khane khali rakho. |
| 404 | URL ka token ya `/mcp` galat. Server window me "Connector path" dobara dekho. |
| Connector add hote hi fail | Server aur tunnel dono chal rahe hon? Pehle `<URL-ka-base>/health` browser me kholo. |
| Tunnel restart ke baad band | Naya trycloudflare link aaya hoga, connector hata kar naye URL se jodo. |
| `http://` | Hamesha `https://` |
| `kotlinc nahi mila` | Optional step 2 (JDK + kotlinc + PATH) karo, phir server restart. |
| Groq/OpenRouter 401/429 | Key galat/limit khatam. `.env` me key badlo, server restart. `ask_auto` khud doosre par chala jata hai. |
| OpenRouter model nahi mila | Free model badalte rehte hain. `list_models` se naya naam lo, `.env` me `OPENROUTER_DEFAULT_MODEL=...` likho. |

## Token badalna
Laptop: `.env` me `MCP_SECRET=` nayi lambi value, server restart, connector naye URL se jodo.
Render: Environment me `MCP_SECRET` badlo, Save, connector naye URL se jodo.

## Suraksha
- Poora URL password jaisa hai, kisi ko mat bhejo / screenshot me mat daalo.
- Keys sirf `.env` ya Render Environment me rakho.

## Ek zaroori baat
Ye Claude ki usage limit **hatata nahi**. Ye bhari kaam Groq/OpenRouter ko bhej kar Claude ke tokens bachata hai. Chat aur tool-call phir bhi Claude ki limit me ginte hain.
