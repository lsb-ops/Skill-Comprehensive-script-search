# Domestic Search Engines — Deep Search Guide

## 🔍 Baidu

### Features

| Feature | Description | URL |
|---------|-------------|-----|
| **Chinese optimization** | Most comprehensive Chinese content index | `https://www.baidu.com/s?wd={keyword}` |
| **Baidu Scholar** | Academic resource search | `https://xueshu.baidu.com/s?wd={keyword}` |
| **Baidu News** | News aggregation | `https://news.baidu.com/` |

### Search examples

```javascript
// 1. Basic search
web_fetch({"url": "https://www.baidu.com/s?wd=Python+tutorial"})

// 2. Site-restricted search
web_fetch({"url": "https://www.baidu.com/s?wd=site:github.com+python"})

// 3. File-type search
web_fetch({"url": "https://www.baidu.com/s?wd=machine+learning+filetype:pdf"})

// 4. Academic search
web_fetch({"url": "https://xueshu.baidu.com/s?wd=deep+learning+image+recognition"})
```

---

## 🔎 Bing CN / Bing INT

### Features

| Feature | Description | URL |
|---------|-------------|-----|
| **Chinese results** | `ensearch=0` returns Chinese results | `https://cn.bing.com/search?q={keyword}&ensearch=0` |
| **English results** | `ensearch=1` returns English results | `https://cn.bing.com/search?q={keyword}&ensearch=1` |
| **Academic search** | Academic resources | `https://cn.bing.com/academic/search?q={keyword}` |

### Search examples

```javascript
// 1. Chinese results
web_fetch({"url": "https://cn.bing.com/search?q=AI+technology&ensearch=0"})

// 2. English results (via CN server)
web_fetch({"url": "https://cn.bing.com/search?q=artificial+intelligence&ensearch=1"})

// 3. Academic search
web_fetch({"url": "https://cn.bing.com/academic/search?q=machine+learning+algorithms"})
```

---

## 🔍 360 Search

### Features

| Feature | Description | URL |
|---------|-------------|-----|
| **Safe search** | Built-in safety protection | Enabled by default |
| **Basic search** | Web search | `https://www.so.com/s?q={keyword}` |

### Search examples

```javascript
// 1. Basic search
web_fetch({"url": "https://www.so.com/s?q=cybersecurity"})

// 2. Site-restricted search
web_fetch({"url": "https://www.so.com/s?q=site:zhihu.com+python"})
```

---

## 🔍 Sogou + WeChat Search

### Features

| Feature | Description | URL |
|---------|-------------|-----|
| **Web search** | General search | `https://sogou.com/web?query={keyword}` |
| **WeChat Official Accounts** | Search public-account articles (the only channel) | `https://wx.sogou.com/weixin?type=2&query={keyword}` |
| **Zhihu optimization** | Strong Zhihu index | Combine with `site:zhihu.com` |

### Search examples

```javascript
// 1. Web search
web_fetch({"url": "https://sogou.com/web?query=python+tutorial"})

// 2. WeChat Official Account article search
web_fetch({"url": "https://wx.sogou.com/weixin?type=2&query=Python+programming"})

// 3. Search a specific public account
web_fetch({"url": "https://wx.sogou.com/weixin?type=2&query=account:Synced"})

// 4. Zhihu content search
web_fetch({"url": "https://www.sogou.com/web?query=site:zhihu.com+machine+learning"})
```

---

## 📱 Shenma (Mobile search)

### Features

| Feature | Description | URL |
|---------|-------------|-----|
| **Mobile optimization** | Mobile-first search experience | `https://m.sm.cn/s?q={keyword}` |
| **Alibaba ecosystem** | Integrated Alibaba content | Default search engine in UC Browser |

### Search examples

```javascript
// 1. Mobile search
web_fetch({"url": "https://m.sm.cn/s?q=python+getting+started"})

// 2. Mobile site-restricted search
web_fetch({"url": "https://m.sm.cn/s?q=site:zhuanlan.zhihu.com+AI"})
```

---

## 🌍 Domestic search strategy

### Pick an engine by search goal

| Search goal | First choice | Why |
|-------------|--------------|-----|
| **General Chinese content** | Baidu | Most comprehensive Chinese index |
| **WeChat public-account articles** | Sogou WeChat | Only channel supporting public-account search |
| **Zhihu content** | Sogou | Best Zhihu coverage |
| **Mobile content** | Shenma | Mobile-first optimization |
| **Academic resources** | Bing Academic | Academic index |
| **Bilingual CN/EN** | Bing CN / Bing INT | Switch with `ensearch` param |
| **News** | Baidu News | News aggregation |

---

## 📚 References

- [Baidu search advanced syntax](https://baike.baidu.com/item/%E6%90%9C%E7%B4%A2%E8%AF%AD%E6%B3%95)
- [Bing search tips](https://cn.bing.com/tips)
- [Sogou search help](https://help.sogou.com/)
