# KB06 — AI 视频平台矩阵

> 即梦 / 可灵 / Sora / Runway 能力对比与提示词适配

---

## 一、平台总览

| 平台 | 单次生成上限 | 总长上限 | 优势 | 劣势 | 推荐用途 |
|---|---|---|---|---|---|
| 即梦 | 10 秒 | 90 秒 | 中文友好、动作理解强、电影感强 | 长镜头稍弱 | 通用首选 |
| 可灵 | 10 秒 | 60 秒 | 写实风格、物理真实 | 中文支持较弱 | 动作戏 |
| Sora | 15 秒 | 60 秒 | 物理真实、复杂场景 | 中文支持弱、价格高 | 高端作品 |
| Runway | 10 秒 | 60 秒 | 风格多样、灵活 | 中文支持弱 | 实验/风格化 |

---

## 二、即梦（即梦 Dreamina / ByteDance）

### 特点
- 中文母语级理解
- 12 核心参数 + 5 段式结构最佳适配
- 人物一致性优秀（图片资产）
- 国产平台，无需翻墙

### 提示词最佳实践
- 中文为主
- 详细分段（0-X秒 / X-Y秒）
- 具体物理量级（米/秒、K 值、光比）
- 参考电影名称可用
- 风格参考库丰富

### 限制
- 单镜最长时间：10 秒
- 单次生成：10 秒
- 长镜头需分段生成

### 适配模板
使用 5 段式完整结构（KB01）。

---

## 三、可灵（Kling / Kuaishou）

### 特点
- 物理真实度高
- 动作连贯性优秀
- 复杂动作戏表现好
- 运镜理解强

### 提示词最佳实践
- 中文为主，英文为辅
- 强调物理细节（速度、角度、力度）
- 减少文学性描述
- 多用动词，少用形容词
- 参考电影名称可用

### 限制
- 中文支持比即梦稍弱
- 长对话表现一般
- 人物一致性需强化

### 适配模板
5 段式可简化光影描述，强化物理参数。

---

## 四、Sora（OpenAI）

### 特点
- 物理真实度顶级
- 复杂场景理解强
- 长镜头连贯性优秀
- 英文优先

### 提示词最佳实践
- **英文为主**
- 自然语言优先
- 电影术语（key light, fill light, dolly in）
- 少用数字编号，多用描述性语言
- 风格参考库丰富

### 限制
- 中文支持弱
- 价格高
- 访问受限

### 适配模板
中文 5 段式 → 英文自然语言：

```
Cinematic medium shot, 9:16 aspect ratio.
Two characters: 刘一鸣 (left third) and 小仇 (right third).
180-degree axis established.
刘一鸣 wears all-black suit with Prada tie.
Sunglasses tucked in suit pocket.

Camera: 35mm lens, MS, fixed position.
Lighting: Key light 4000K from upper left 45 degrees, fill light 4500K, back light 5000K.
Color grading: Fuji Eterna, 35mm film grain, no halation.

0-3s: 刘一鸣 walks toward 小仇 at 1.5 m/s.
3-5s: 小仇 trembles, arms crossed, fearful.
5-7s: 刘一鸣 shakes head and sighs.
7s: 刘一鸣 turns and walks away.
```

---

## 五、Runway Gen-3

### 特点
- 风格化强
- 实验性表现好
- 适合概念艺术
- 灵活

### 提示词最佳实践
- 英文为主
- 简明指令
- 风格关键词强（如 "cinematic, hyperrealistic, 8K"）
- 减少复杂分段

### 限制
- 物理真实度一般
- 长对话弱
- 人物一致性需强化

### 适配模板
简明 5 段式：

```
Cinematic shot, two characters facing each other.
Left: man in black suit (180cm, short black hair, Prada tie).
Right: man in light blue jacket (short messy hair, silver glasses).

Medium shot, 35mm, fixed camera.
Cool blue lighting from left, 4000K.
Fuji Eterna color grading.

Action: Left character shakes head, sighs, turns and walks away. Right character trembles and hugs himself.
```

---

## 六、平台选择决策树

```
Q1: 作品主要语言是中文？
  Yes → 即梦（首选）/ 可灵
  No → Sora / Runway

Q2: 重点是动作戏/追逐？
  Yes → 可灵
  No → 即梦

Q3: 预算充足 + 高端作品？
  Yes → Sora
  No → 即梦

Q4: 概念艺术/实验风格？
  Yes → Runway
  No → 即梦
```

### 默认推荐
**即梦**（中文作品首选）

---

## 七、跨平台提示词适配

### 中文 → 英文转换规则

#### 1. 镜头参数
```
MS 中景 → Medium shot (MS)
CU 近景 → Close-up (CU)
ECU 极致特写 → Extreme close-up (ECU)
LS 远景 → Long shot (LS)
Dolly In → Push in / dolly in
Dolly Out → Pull back / dolly out
```

#### 2. 光影
```
主光 Key Light → Key light
辅光 Fill Light → Fill light
轮廓光 Back Light → Back light / rim light
色温4000K → color temperature 4000K
光比1:2 → 1:2 lighting ratio
```

#### 3. 动作
```
缓推 0.3 米/每秒 → slow push in at 0.3 m/s
走路 1.5 米/每秒 → walking at 1.5 m/s
转身脚跟为轴 → pivot on heel, shoulder leading
```

#### 4. 风格参考
```
教父 → The Godfather
阿拉伯的劳伦斯 → Lawrence of Arabia
天堂电影院 → Cinema Paradiso
功夫 → Kung Fu Hustle
```

---

## 八、单次生成时长策略

### 即梦/可灵 10 秒上限
- 单镜 5-8 秒：直接生成
- 单镜 9-10 秒：直接生成
- 单镜 >10 秒：拆分为多镜

### 长镜头的拆分技巧
```
单镜 12 秒：
  镜 A：前 6 秒（场景建立）
  镜 B：后 6 秒（动作延续）
  合并策略：
    - 镜 A 结尾：人物到画面中心偏右
    - 镜 B 开头：人物在画面中心偏左（Dolly In 推进）
    - 后期剪辑时画面叠加实现无缝
```

### Sora 15 秒上限
- 单镜可生成更复杂场景
- 长动作戏一次性完成
- 后期衔接相对容易

---

## 九、平台能力对比（细化）

### 人物一致性
| 平台 | 单镜内 | 多镜之间 |
|---|---|---|
| 即梦 | 优秀 | 优秀（图片资产） |
| 可灵 | 良好 | 良好 |
| Sora | 优秀 | 一般 |
| Runway | 良好 | 一般 |

### 物理真实
| 平台 | 走路 | 跑步 | 复杂动作 |
|---|---|---|---|
| 即梦 | 优秀 | 良好 | 良好 |
| 可灵 | 优秀 | 优秀 | 优秀 |
| Sora | 优秀 | 优秀 | 优秀 |
| Runway | 良好 | 良好 | 一般 |

### 运镜理解
| 平台 | 推拉 | 摇移 | 跟拍 |
|---|---|---|---|
| 即梦 | 优秀 | 良好 | 良好 |
| 可灵 | 优秀 | 优秀 | 优秀 |
| Sora | 优秀 | 优秀 | 优秀 |
| Runway | 良好 | 良好 | 良好 |

### 中文理解
| 平台 | 等级 |
|---|---|
| 即梦 | ★★★★★ |
| 可灵 | ★★★★ |
| Sora | ★★ |
| Runway | ★★ |

### 光影理解
| 平台 | 等级 |
|---|---|
| 即梦 | ★★★★★ |
| 可灵 | ★★★★ |
| Sora | ★★★★ |
| Runway | ★★★ |

---

## 十、平台特定的提示词技巧

### 即梦独家技巧
- "v3.0 强化" 关键词可强化物理细节
- "AI 后期逆光晕" 触发 Halation
- "真实物理" 强调物理真实
- "教化者温度" 描述特殊情绪

### 可灵独家技巧
- "物理正确" 强调物理
- "真实速度" 强调速度
- "动态连贯" 强调连贯

### Sora 独家技巧
- 详细自然语言
- 物理描述
- 电影术语
- "Cinematic" 关键词

### Runway 独家技巧
- 简明风格关键词
- "Hyperrealistic, cinematic"
- 减少分段

---

## 十一、混合使用策略

### 方案1：主平台 + 辅助平台
- 即梦生成主镜头
- 可灵生成动作戏
- Sora 生成关键升华

### 方案2：分阶段使用
- 前期镜头：即梦
- 关键镜头：Sora
- 收尾镜头：即梦

### 方案3：单平台工作流
- 全部镜头同一平台
- 保持一致性
- 简化后期

### 推荐
**短剧首选单一平台**（即梦），保证一致性。

---

## 十二、检验清单

- [ ] 平台是否匹配作品语言？
- [ ] 单镜时长是否在平台上限内？
- [ ] 提示词是否适配平台特性？
- [ ] 是否考虑人物一致性方案？
- [ ] 长镜头是否合理拆分？
- [ ] 跨平台时是否做了提示词转换？
