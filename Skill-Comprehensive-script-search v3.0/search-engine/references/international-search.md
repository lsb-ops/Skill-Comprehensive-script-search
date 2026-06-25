# International Search Engines — Deep Search Guide

## 🔍 Google deep search

### 1.1 Basic advanced search operators

| Operator | Function | Example | URL |
|----------|----------|---------|-----|
| `""` | Exact match | `"machine learning"` | `https://www.google.com/search?q=%22machine+learning%22` |
| `-` | Exclude keyword | `python -snake` | `https://www.google.com/search?q=python+-snake` |
| `OR` | Logical OR | `machine learning OR deep learning` | `https://www.google.com/search?q=machine+learning+OR+deep+learning` |
| `*` | Wildcard | `machine * algorithms` | `https://www.google.com/search?q=machine+*+algorithms` |
| `()` | Grouping | `(apple OR microsoft) phones` | `https://www.google.com/search?q=(apple+OR+microsoft)+phones` |
| `..` | Numeric range | `laptop $500..$1000` | `https://www.google.com/search?q=laptop+%24500..%241000` |

### 1.2 Site and file search

| Operator | Function | Example |
|----------|----------|---------|
| `site:` | Site-restricted search | `site:github.com python projects` |
| `filetype:` | File-type filter | `filetype:pdf annual report` |
| `inurl:` | URL contains | `inurl:login admin` |
| `intitle:` | Title contains | `intitle:"index of" mp3` |
| `intext:` | Body contains | `intext:password filetype:txt` |
| `cache:` | View cached page | `cache:example.com` |
| `related:` | Related websites | `related:github.com` |
| `info:` | Site info | `info:example.com` |

### 1.3 Time filter parameters

| Parameter | Meaning | URL example |
|-----------|---------|-------------|
| `tbs=qdr:h` | Past 1 hour | `https://www.google.com/search?q=news&tbs=qdr:h` |
| `tbs=qdr:d` | Past 24 hours | `https://www.google.com/search?q=news&tbs=qdr:d` |
| `tbs=qdr:w` | Past 1 week | `https://www.google.com/search?q=news&tbs=qdr:w` |
| `tbs=qdr:m` | Past 1 month | `https://www.google.com/search?q=news&tbs=qdr:m` |
| `tbs=qdr:y` | Past 1 year | `https://www.google.com/search?q=news&tbs=qdr:y` |
| `tbs=cdr:1,cd_min:1/1/2024,cd_max:12/31/2024` | Custom date range | All of 2024 |

### 1.4 Language and region filters

| Parameter | Function | Example |
|-----------|----------|---------|
| `hl=en` | UI language | `https://www.google.com/search?q=test&hl=en` |
| `lr=lang_zh-CN` | Result language | `https://www.google.com/search?q=test&lr=lang_zh-CN` |
| `cr=countryCN` | Country/region | `https://www.google.com/search?q=test&cr=countryCN` |
| `gl=us` | Geo location | `https://www.google.com/search?q=test&gl=us` |

### 1.5 Special search types

| Type | URL | Description |
|------|-----|-------------|
| Image search | `https://www.google.com/search?q={keyword}&tbm=isch` | `tbm=isch` = images |
| News search | `https://www.google.com/search?q={keyword}&tbm=nws` | `tbm=nws` = news |
| Video search | `https://www.google.com/search?q={keyword}&tbm=vid` | `tbm=vid` = videos |
| Maps search | `https://www.google.com/search?q={keyword}&tbm=map` | `tbm=map` = maps |
| Shopping search | `https://www.google.com/search?q={keyword}&tbm=shop` | `tbm=shop` = shopping |
| Books search | `https://www.google.com/search?q={keyword}&tbm=bks` | `tbm=bks` = books |
| Scholar | `https://scholar.google.com/scholar?q={keyword}` | Google Scholar |

### 1.6 Google deep search examples

```javascript
// 1. Search Python ML projects on GitHub
web_fetch({"url": "https://www.google.com/search?q=site:github.com+python+machine+learning"})

// 2. Find 2024 PDF ML tutorials
web_fetch({"url": "https://www.google.com/search?q=machine+learning+tutorial+filetype:pdf&tbs=cdr:1,cd_min:1/1/2024"})

// 3. Pages with "tutorial" in the title and "python" anywhere
web_fetch({"url": "https://www.google.com/search?q=intitle:tutorial+python"})

// 4. Past week's news
web_fetch({"url": "https://www.google.com/search?q=AI+breakthrough&tbs=qdr:w&tbm=nws"})

// 5. Chinese results with English UI
web_fetch({"url": "https://www.google.com/search?q=artificial+intelligence&lr=lang_zh-CN&hl=en"})

// 6. Laptops in a specific price range
web_fetch({"url": "https://www.google.com/search?q=laptop+%241000..%242000+best+rating"})

// 7. Exclude Wikipedia
web_fetch({"url": "https://www.google.com/search?q=python+programming+-wikipedia"})

// 8. Academic literature
web_fetch({"url": "https://scholar.google.com/scholar?q=deep+learning+optimization"})

// 9. Cached page (view deleted content)
web_fetch({"url": "https://webcache.googleusercontent.com/search?q=cache:example.com"})

// 10. Related sites
web_fetch({"url": "https://www.google.com/search?q=related:stackoverflow.com"})
```

---

## 🦆 DuckDuckGo deep search

### 2.1 DuckDuckGo features

| Feature | Syntax | Example |
|---------|--------|---------|
| **Bangs shortcut** | `!shortcut` | `!g python` → jump to Google |
| **Password generation** | `password` | `https://duckduckgo.com/?q=password+20` |
| **Color conversion** | `color` | `https://duckduckgo.com/?q=+%23FF5733` |
| **URL shortener** | `shorten` | `https://duckduckgo.com/?q=shorten+example.com` |
| **QR code** | `qr` | `https://duckduckgo.com/?q=qr+hello+world` |
| **UUID generator** | `uuid` | `https://duckduckgo.com/?q=uuid` |
| **Base64 encode/decode** | `base64` | `https://duckduckgo.com/?q=base64+hello` |

### 2.2 DuckDuckGo Bangs reference

#### Search engines

| Bang | Destination | Example |
|------|-------------|---------|
| `!g` | Google | `!g python tutorial` |
| `!b` | Bing | `!b weather` |
| `!y` | Yahoo | `!y finance` |
| `!sp` | Startpage | `!sp privacy` |
| `!brave` | Brave Search | `!brave tech` |

#### Developer tools

| Bang | Destination | Example |
|------|-------------|---------|
| `!gh` | GitHub | `!gh tensorflow` |
| `!so` | Stack Overflow | `!so javascript error` |
| `!npm` | npmjs.com | `!npm express` |
| `!pypi` | PyPI | `!pypi requests` |
| `!mdn` | MDN Web Docs | `!mdn fetch api` |
| `!docs` | DevDocs | `!docs python` |
| `!docker` | Docker Hub | `!docker nginx` |

#### Knowledge

| Bang | Destination | Example |
|------|-------------|---------|
| `!w` | Wikipedia | `!w machine learning` |
| `!wen` | Wikipedia (EN) | `!wen artificial intelligence` |
| `!wt` | Wiktionary | `!wt serendipity` |
| `!imdb` | IMDb | `!imdb inception` |

#### Shopping

| Bang | Destination | Example |
|------|-------------|---------|
| `!a` | Amazon | `!a wireless headphones` |
| `!e` | eBay | `!e vintage watch` |
| `!ali` | AliExpress | `!ali phone case` |

#### Maps

| Bang | Destination | Example |
|------|-------------|---------|
| `!m` | Google Maps | `!m Beijing` |
| `!maps` | OpenStreetMap | `!maps Paris` |

### 2.3 DuckDuckGo search parameters

| Parameter | Function | Example |
|-----------|----------|---------|
| `kp=1` | Strict safe search | `https://duckduckgo.com/html/?q=test&kp=1` |
| `kp=-1` | Disable safe search | `https://duckduckgo.com/html/?q=test&kp=-1` |
| `kl=cn` | China region | `https://duckduckgo.com/html/?q=news&kl=cn` |
| `kl=us-en` | US English | `https://duckduckgo.com/html/?q=news&kl=us-en` |
| `ia=web` | Web results | `https://duckduckgo.com/?q=test&ia=web` |
| `ia=images` | Image results | `https://duckduckgo.com/?q=test&ia=images` |
| `ia=news` | News results | `https://duckduckgo.com/?q=test&ia=news` |
| `ia=videos` | Video results | `https://duckduckgo.com/?q=test&ia=videos` |

### 2.4 DuckDuckGo deep search examples

```javascript
// 1. Use Bang to jump to Google
web_fetch({"url": "https://duckduckgo.com/html/?q=!g+machine+learning"})

// 2. Search GitHub projects directly
web_fetch({"url": "https://duckduckgo.com/html/?q=!gh+react"})

// 3. Look up Stack Overflow answers
web_fetch({"url": "https://duckduckgo.com/html/?q=!so+python+list+comprehension"})

// 4. Generate a password
web_fetch({"url": "https://duckduckgo.com/?q=password+16"})

// 5. Base64 encode
web_fetch({"url": "https://duckduckgo.com/?q=base64+hello+world"})

// 6. Color code conversion
web_fetch({"url": "https://duckduckgo.com/?q=%23FF5733"})

// 7. Search YouTube videos
web_fetch({"url": "https://duckduckgo.com/html/?q=!yt+python+tutorial"})

// 8. Look up Wikipedia
web_fetch({"url": "https://duckduckgo.com/html/?q=!w+artificial+intelligence"})

// 9. Amazon product search
web_fetch({"url": "https://duckduckgo.com/html/?q=!a+laptop"})

// 10. Generate a QR code
web_fetch({"url": "https://duckduckgo.com/?q=qr+https://github.com"})
```

---

## 🔎 Brave Search deep search

### 3.1 Brave Search features

| Feature | Parameter | Example |
|---------|-----------|---------|
| **Independent index** | No dependency on Google/Bing | Own crawler index |
| **Goggles** | Custom search rules | Build personalized filters |
| **Discussions** | Forum discussions | Aggregates Reddit and others |
| **News** | News aggregation | Independent news index |

### 3.2 Brave Search parameters

| Parameter | Function | Example |
|-----------|----------|---------|
| `tf=pw` | Past week | `https://search.brave.com/search?q=news&tf=pw` |
| `tf=pm` | Past month | `https://search.brave.com/search?q=tech&tf=pm` |
| `tf=py` | Past year | `https://search.brave.com/search?q=AI&tf=py` |
| `safesearch=strict` | Strict safe search | `https://search.brave.com/search?q=test&safesearch=strict` |
| `source=web` | Web search | Default |
| `source=news` | News search | `https://search.brave.com/search?q=tech&source=news` |
| `source=images` | Image search | `https://search.brave.com/search?q=cat&source=images` |
| `source=videos` | Video search | `https://search.brave.com/search?q=music&source=videos` |

### 3.3 Brave Search Goggles (custom filters)

Goggles let you create custom search rules:

```
$discard  // discard everything
$boost,site=stackoverflow.com  // boost Stack Overflow
$boost,site=github.com  // boost GitHub
$boost,site=docs.python.org  // boost Python docs
```

### 3.4 Brave Search deep search examples

```javascript
// 1. Past week's tech news
web_fetch({"url": "https://search.brave.com/search?q=technology&tf=pw&source=news"})

// 2. Past month's AI developments
web_fetch({"url": "https://search.brave.com/search?q=artificial+intelligence&tf=pm"})

// 3. Image search
web_fetch({"url": "https://search.brave.com/search?q=machine+learning&source=images"})

// 4. Video tutorials
web_fetch({"url": "https://search.brave.com/search?q=python+tutorial&source=videos"})

// 5. Independent index search
web_fetch({"url": "https://search.brave.com/search?q=privacy+tools"})
```

---

## 📊 WolframAlpha knowledge computation

### 4.1 WolframAlpha data types

| Type | Query example | URL |
|------|---------------|-----|
| **Math computation** | `integrate x^2 dx` | `https://www.wolframalpha.com/input?i=integrate+x%5E2+dx` |
| **Unit conversion** | `100 miles to km` | `https://www.wolframalpha.com/input?i=100+miles+to+km` |
| **Currency conversion** | `100 USD to CNY` | `https://www.wolframalpha.com/input?i=100+USD+to+CNY` |
| **Stock data** | `AAPL stock` | `https://www.wolframalpha.com/input?i=AAPL+stock` |
| **Weather query** | `weather in Beijing` | `https://www.wolframalpha.com/input?i=weather+in+Beijing` |
| **Population data** | `population of China` | `https://www.wolframalpha.com/input?i=population+of+China` |
| **Chemical elements** | `properties of gold` | `https://www.wolframalpha.com/input?i=properties+of+gold` |
| **Nutrition** | `nutrition of apple` | `https://www.wolframalpha.com/input?i=nutrition+of+apple` |
| **Date calculation** | `days between Jan 1 2020 and Dec 31 2024` | Date interval calculation |
| **Time-zone conversion** | `10am Beijing to New York` | Time-zone conversion |
| **IP address** | `8.8.8.8` | IP info lookup |
| **Barcode** | `scan barcode 123456789` | Barcode info |
| **Flight** | `flight AA123` | Flight info |

### 4.2 WolframAlpha deep search examples

```javascript
// 1. Compute integral
web_fetch({"url": "https://www.wolframalpha.com/input?i=integrate+sin%28x%29+from+0+to+pi"})

// 2. Solve equation
web_fetch({"url": "https://www.wolframalpha.com/input?i=solve+x%5E2-5x%2B6%3D0"})

// 3. Real-time currency rate
web_fetch({"url": "https://www.wolframalpha.com/input?i=100+USD+to+CNY"})

// 4. Real-time stock data
web_fetch({"url": "https://www.wolframalpha.com/input?i=Apple+stock+price"})

// 5. City weather
web_fetch({"url": "https://www.wolframalpha.com/input?i=weather+in+Shanghai+tomorrow"})

// 6. Country statistics
web_fetch({"url": "https://www.wolframalpha.com/input?i=GDP+of+China+vs+USA"})

// 7. Chemistry calculation
web_fetch({"url": "https://www.wolframalpha.com/input?i=molar+mass+of+H2SO4"})

// 8. Physical constant
web_fetch({"url": "https://www.wolframalpha.com/input?i=speed+of+light"})

// 9. Nutrition info
web_fetch({"url": "https://www.wolframalpha.com/input?i=calories+in+banana"})

// 10. Historical date
web_fetch({"url": "https://www.wolframalpha.com/input?i=events+on+July+20+1969"})
```

---

## 🔧 Startpage privacy search

### 5.1 Startpage features

| Feature | Description | URL |
|---------|-------------|-----|
| **Proxy browsing** | Anonymous browsing of results | Click "Anonymous View" |
| **No tracking** | Does not record search history | Enabled by default |
| **EU servers** | Protected by EU privacy law | Data stays in Europe |
| **Image proxy** | Images loaded via proxy | Hides IP |

### 5.2 Startpage parameters

| Parameter | Function | Example |
|-----------|----------|---------|
| `cat=web` | Web search | Default |
| `cat=images` | Image search | `...&cat=images` |
| `cat=video` | Video search | `...&cat=video` |
| `cat=news` | News search | `...&cat=news` |
| `language=english` | English results | `...&language=english` |
| `time=day` | Past 24 hours | `...&time=day` |
| `time=week` | Past week | `...&time=week` |
| `time=month` | Past month | `...&time=month` |
| `time=year` | Past year | `...&time=year` |
| `nj=0` | Disable family filter | `...&nj=0` |

### 5.3 Startpage deep search examples

```javascript
// 1. Privacy search
web_fetch({"url": "https://www.startpage.com/sp/search?query=privacy+tools"})

// 2. Privacy image search
web_fetch({"url": "https://www.startpage.com/sp/search?query=nature&cat=images"})

// 3. This week's news (privacy mode)
web_fetch({"url": "https://www.startpage.com/sp/search?query=tech+news&time=week&cat=news"})

// 4. English-results search
web_fetch({"url": "https://www.startpage.com/sp/search?query=machine+learning&language=english"})
```

---

## 🌐 Other international search engines

### Yahoo

```javascript
web_fetch({"url": "https://search.yahoo.com/search?p={keyword}"})
```

### Ecosia (eco-friendly search)

```javascript
web_fetch({"url": "https://www.ecosia.org/search?q={keyword}"})
```

### Qwant (EU privacy search)

```javascript
web_fetch({"url": "https://www.qwant.com/?q={keyword}"})
```

---

## 🌍 International search strategy

### Pick an engine by search goal

| Search goal | First choice | Why |
|-------------|--------------|-----|
| **Academic research** | Google Scholar | Most comprehensive academic index |
| **Programming / dev** | Google + DuckDuckGo Bangs | Best tech-doc coverage |
| **Privacy-sensitive** | DuckDuckGo / Brave | No user tracking |
| **Real-time news** | Brave News | Independent news index |
| **Knowledge computation** | WolframAlpha | Structured-data calculations |
| **Privacy + Google results** | Startpage | Google results with privacy |

---

*16 engines documented 🔍 | Multi Search Engine v2.2.0*
