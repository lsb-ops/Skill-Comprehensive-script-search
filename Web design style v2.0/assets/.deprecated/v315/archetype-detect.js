/**
 * WebPPT Maker v3.15 · Archetype Detector (原型智能识别)
 *
 * 核心: 不是关键词匹配, 是从内容**结构**判断应该用哪个原型
 *
 * 识别维度 (4 个结构信号):
 * 1. 数字存在 + 是否有单位 → big-number
 * 2. 是否疑问/惊叹/命令开头 → hero (开场hook)
 * 3. 是否包含对比词 (before/after, vs, 而, 从前) → comparison
 * 4. 是否以 " 开头 → quote
 * 5. 是否带步骤/序号 (第一步/步骤1/1.) → flow
 * 6. 是否包含行动动词 + 价值 (免费试用/立即/现在) → cta
 * 7. 完整句子标题 + 证据数据 → action-title
 *
 * 用法:
 *   const arch = ArchetypeDetect.detect({
 *     title: "我们完成了 Q3 营收目标 1.2 亿",
 *     body: "...",
 *     numbers: ["1.2 亿"],
 *     sequence: 1  // 第几张, 用于判断 hook
 *   });
 *   // → "big-number"
 */

(function () {
  'use strict';

  // === 结构信号定义 (每个 archetype 识别条件) ===
  var SIGNALS = {
    'big-number': {
      weight: 0,
      test: function (ctx) {
        // 条件: 有大数字 (>3 位) + 上下文短
        if (!ctx.numbers || ctx.numbers.length === 0) return false;
        var hasBigNumber = ctx.numbers.some(function (n) {
          // 提取数字
          var digits = String(n).replace(/[^\d.]/g, '');
          return digits.length >= 3 || /[亿万%％]/.test(n);
        });
        if (!hasBigNumber) return false;
        // 且无多个数字竞争 (否则是数据列表)
        var totalNums = (ctx.title + ' ' + ctx.body).match(/\d+\.?\d*[亿万%％]?/g) || [];
        return totalNums.length <= 2 && (ctx.title.length + ctx.body.length) < 80;
      },
      weightFn: function (ctx) {
        return 10; // 大数字 = 强信号
      }
    },

    'hero': {
      weight: 0,
      test: function (ctx) {
        // 条件: 第 1 张 OR 标题短 (< 10 字) 且无数据
        if (ctx.sequence === 1) return true;
        var isShortTitle = ctx.title && ctx.title.length < 10;
        var hasNoData = !ctx.numbers || ctx.numbers.length === 0;
        return isShortTitle && hasNoData;
      },
      weightFn: function (ctx) {
        return ctx.sequence === 1 ? 15 : (ctx.title && ctx.title.length < 10 ? 5 : 0);
      }
    },

    'comparison': {
      weight: 0,
      test: function (ctx) {
        // 条件: 包含对比词
        var text = ctx.title + ' ' + ctx.body;
        var compareWords = /(之前|之后|以前|现在|before|after|vs|versus|对比|对比|从.*?到|原来.*?现在)/i;
        return compareWords.test(text);
      },
      weightFn: function () { return 8; }
    },

    'quote': {
      weight: 0,
      test: function (ctx) {
        // 条件: 以 " 开头 OR 明确标 quote
        if (ctx.type === 'quote') return true;
        var t = (ctx.title || '').trim();
        if (t.startsWith('"') || t.startsWith('"') || t.startsWith('"')) return true;
        // 标题极短 (< 30 字) 且是陈述句, 无数字无列表
        var hasNumber = /\d/.test(t);
        var isStatement = !/[?？!！]/.test(t);
        return t.length < 30 && !hasNumber && isStatement && ctx.body && ctx.body.length < 100;
      },
      weightFn: function () { return 7; }
    },

    'flow': {
      weight: 0,
      test: function (ctx) {
        // 条件: 包含步骤/序号
        var text = ctx.title + ' ' + ctx.body;
        var flowPatterns = /(第[一二三四五六七八九十\d]+步|步骤\s*\d|step\s*\d|^[一二三四五六七八九十\d]+[\.、:：])/i;
        return flowPatterns.test(text);
      },
      weightFn: function () { return 9; }
    },

    'cta': {
      weight: 0,
      test: function (ctx) {
        // 条件: 末尾 + 行动动词
        var isLast = ctx.sequence && ctx.total && ctx.sequence >= ctx.total;
        if (!isLast) return false;
        var text = ctx.title + ' ' + ctx.body;
        var actionWords = /(立即|马上|现在|免费|试用|注册|订阅|下载|开始|join|get|start|try|sign|download|click)/i;
        return actionWords.test(text);
      },
      weightFn: function (ctx) {
        return ctx.sequence && ctx.total && ctx.sequence >= ctx.total ? 12 : 0;
      }
    },

    'action-title': {
      weight: 0,
      test: function (ctx) {
        // 条件: 标题是完整句子 (含动词) + 有证据数据
        if (!ctx.title || ctx.title.length < 8) return false;
        var t = ctx.title;
        // 含动词特征 (中文: 的/是/了/在, 英文: is/are/was/will/has)
        var hasVerb = /(的|是|了|在|有|能|会|将|应该|需要|应该|让|使)/.test(t) ||
                      /(is|are|was|were|will|has|have|can|must|should)/i.test(t);
        // 有数据/证据
        var hasEvidence = (ctx.numbers && ctx.numbers.length > 0) || (ctx.body && ctx.body.length > 30);
        return hasVerb && hasEvidence && t.length < 50;
      },
      weightFn: function () { return 6; }
    }
  };

  // === 提取数字 ===
  function extractNumbers(text) {
    if (!text) return [];
    var matches = text.match(/\d+\.?\d*[亿万kKmMbB%％万千百]?/g) || [];
    return matches.filter(function (n) {
      // 过滤太小的数字 (年份 2024 也算, 但单数字 "1" 不算)
      var digits = n.replace(/[^\d.]/g, '');
      return digits.length >= 1;
    });
  }

  // === 主检测函数 ===
  function detect(ctx) {
    if (!ctx || typeof ctx !== 'object') return 'hero';
    ctx.title = ctx.title || '';
    ctx.body = ctx.body || '';
    ctx.numbers = ctx.numbers || extractNumbers(ctx.title + ' ' + ctx.body);

    var scores = {};
    Object.keys(SIGNALS).forEach(function (arch) {
      var signal = SIGNALS[arch];
      try {
        if (signal.test(ctx)) {
          scores[arch] = signal.weightFn(ctx);
        } else {
          scores[arch] = 0;
        }
      } catch (e) {
        scores[arch] = 0;
      }
    });

    // 找最高分
    var best = 'hero';
    var bestScore = -1;
    Object.keys(scores).forEach(function (arch) {
      if (scores[arch] > bestScore) {
        bestScore = scores[arch];
        best = arch;
      }
    });

    // 分数为 0 → 默认 hero
    if (bestScore <= 0) best = 'hero';

    return best;
  }

  // === 分析多张幻灯片, 给出序列感知结果 ===
  function analyzeSequence(slides) {
    if (!Array.isArray(slides) || slides.length === 0) return [];
    var total = slides.length;

    return slides.map(function (slide, idx) {
      var ctx = {
        title: slide.title || '',
        body: slide.body || '',
        type: slide.type,
        sequence: idx + 1,
        total: total,
        numbers: slide.numbers || extractNumbers((slide.title || '') + ' ' + (slide.body || ''))
      };
      var archetype = detect(ctx);
      // 推断叙事角色
      var role = inferRole(ctx, archetype);
      return {
        index: idx,
        archetype: archetype,
        role: role,
        title: ctx.title,
        numbers: ctx.numbers
      };
    });
  }

  // === 推断叙事角色 (Hook/Value/Proof/CTA) ===
  function inferRole(ctx, archetype) {
    if (archetype === 'cta') return 'cta';
    if (ctx.sequence === 1) return 'hook';
    if (archetype === 'hero') return 'hook';
    if (archetype === 'big-number') return 'proof';
    if (archetype === 'quote') return 'proof';
    if (archetype === 'comparison') return 'proof';
    if (archetype === 'flow') return 'value';
    if (archetype === 'action-title') {
      // 第一张非 hero 的 action-title → value
      // 中间的 → proof
      var ratio = ctx.sequence / ctx.total;
      if (ratio < 0.4) return 'value';
      return 'proof';
    }
    // 默认
    var ratio = ctx.sequence / ctx.total;
    if (ratio < 0.3) return 'value';
    if (ratio > 0.8) return 'cta';
    return 'proof';
  }

  // === 暴露 API ===
  window.WebPPT_ArchetypeDetect = {
    detect: detect,
    analyzeSequence: analyzeSequence,
    inferRole: inferRole,
    extractNumbers: extractNumbers,
    SIGNALS: SIGNALS
  };
})();