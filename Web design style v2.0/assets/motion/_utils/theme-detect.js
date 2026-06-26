/**
 * ⚠️  DEPRECATED in v3.15 · 已被 archetype-detect.js 取代
 * ⚠️  替代: assets/composition/archetype-detect.js
 * ⚠️  原因: 关键词匹配仍是模板思维, v3.15 从内容结构识别 archetype
 * ⚠️  保留此文件仅为 v3.14 回归测试, 不再用于生产
 *
 * WebPPT Maker v3.14 · 智能主题识别 (Theme Auto-Detect)
 *
 * 根据内容自动判定 PPT 主题 (商务/科技/教育/时尚)
 * 应用: 用户给 PPT 主题/关键词 → 系统自动套用对应设计
 *
 * 判定方法:
 * 1. 关键词匹配 (zh/en) - 加权打分
 * 2. 内容情感分析 (积极/消极/中性)
 * 3. 行业词库映射
 *
 * 用法:
 *   const theme = WebPPT_ThemeDetect.detect('Q3 业务复盘 收入增长');
 *   // → "business"
 *   const theme = WebPPT_ThemeDetect.detect('AI 大模型 神经网络 架构');
 *   // → "tech"
 *
 *   // 自动应用 (调用 theme-applier)
 *   WebPPT_ThemeDetect.applyTo(content, rootEl);
 */

(function () {
  'use strict';

  // === 主题关键词库 (加权) ===
  // 来源: DESIGN_PHILOSOPHY.md §2.2 + 行业语料
  var THEME_KEYWORDS = {
    business: {
      label: '商务',
      zh: {
        // 高权重 (核心商务词)
        high: ['商业', '商务', '汇报', '战略', '收入', '利润', 'KPI', '财报', '季度', '年度',
               '复盘', '战略', '目标', '管理', '运营', '市场', '营销', '销售', '客户',
               '金融', '银行', '投资', '股票', '股权', '资本', '上市', 'IPO', '估值',
               '提案', '路演', '尽调', '风控', '合规'],
        medium: ['增长', '提升', '降低', '优化', '效率', '成本', '预算', 'ROI',
                 'GMV', '营收', '毛利', '净利', '用户', '客户', '供应链'],
        low: ['计划', '数据', '分析', '报告', '会议', '总结', '项目']
      },
      en: {
        high: ['business', 'revenue', 'profit', 'strategy', 'KPI', 'financial',
               'quarterly', 'annual', 'investor', 'IPO', 'valuation', 'stakeholder'],
        medium: ['growth', 'optimization', 'efficiency', 'cost', 'budget', 'ROI',
                 'GMV', 'margin', 'stakeholder', 'customer'],
        low: ['plan', 'data', 'analysis', 'report', 'meeting', 'summary']
      },
      weight: { high: 3, medium: 2, low: 1 }
    },

    tech: {
      label: '科技',
      zh: {
        high: ['AI', '人工智能', '大模型', 'LLM', 'GPT', '机器学习', '深度学习', '神经网络',
               '算法', '架构', '区块链', 'Web3', 'SaaS', '云', '云原生', '微服务',
               '量子', '芯片', '半导体', 'GPU', 'TPU', '数据库', 'API'],
        medium: ['技术', '系统', '开发', '代码', '编程', '开源', 'GitHub',
                 '前端', '后端', '全栈', 'DevOps', 'CI/CD', '容器', 'Docker', 'K8s'],
        low: ['数据', '创新', '智能', '数字', '工程', '平台']
      },
      en: {
        high: ['AI', 'machine learning', 'deep learning', 'neural network', 'LLM',
               'blockchain', 'cloud', 'microservices', 'API', 'GPU', 'database',
               'kubernetes', 'docker', 'devops'],
        medium: ['technology', 'system', 'develop', 'code', 'programming', 'open source',
                 'frontend', 'backend', 'fullstack', 'engineering', 'platform'],
        low: ['data', 'innovation', 'digital', 'engineering', 'platform']
      },
      weight: { high: 3, medium: 2, low: 1 }
    },

    education: {
      label: '教育',
      zh: {
        high: ['课程', '教学', '教材', '课件', '学生', '老师', '教师', '学校', '大学',
               '学院', '学科', '知识', '原理', '概念', '理论', '公式', '定律'],
        medium: ['学习', '培训', '讲座', '演讲', '分享', '科普', '入门', '进阶',
                 '基础', '高级', '实验', '案例', '习题'],
        low: ['内容', '主题', '问题', '答案', '解析', '总结', '回顾']
      },
      en: {
        high: ['course', 'curriculum', 'syllabus', 'lecture', 'student', 'teacher',
               'professor', 'university', 'school', 'knowledge', 'theory', 'concept',
               'principle', 'formula'],
        medium: ['learning', 'training', 'tutorial', 'lesson', 'guide', 'introduction',
                 'beginner', 'advanced', 'experiment', 'case study', 'exercise'],
        low: ['topic', 'content', 'question', 'answer', 'summary', 'review']
      },
      weight: { high: 3, medium: 2, low: 1 }
    },

    fashion: {
      label: '时尚',
      zh: {
        high: ['时尚', '服装', '服饰', '奢侈品', '品牌', '设计师', '时装周', '走秀',
               '潮流', '搭配', '风格', '美妆', '护肤', '香水', '珠宝', '腕表'],
        medium: ['设计', '美', '艺术', '创意', '美学', '色彩', '质感', '纹理',
                 '优雅', '高端', '精致', '奢华'],
        low: ['色彩', '氛围', '情绪', '故事', '灵感', '系列']
      },
      en: {
        high: ['fashion', 'luxury', 'designer', 'couture', 'runway', 'style',
               'brand', 'beauty', 'skincare', 'perfume', 'jewelry', 'watch'],
        medium: ['design', 'art', 'creative', 'aesthetic', 'elegant', 'premium',
                 'sophisticated', 'craftsmanship', 'texture'],
        low: ['color', 'mood', 'story', 'inspiration', 'collection']
      },
      weight: { high: 3, medium: 2, low: 1 }
    }
  };

  // === 默认主题 ===
  var DEFAULT_THEME = 'business';

  // === 计算文本匹配得分 ===
  function scoreText(text, themeKey) {
    var theme = THEME_KEYWORDS[themeKey];
    if (!theme) return 0;

    var lowerText = text.toLowerCase();
    var score = 0;

    // 中文
    ['high', 'medium', 'low'].forEach(function (level) {
      var words = (theme.zh[level] || []).concat(theme.en[level] || []);
      words.forEach(function (word) {
        var lowerWord = word.toLowerCase();
        // 多次出现累计
        var idx = 0;
        while ((idx = lowerText.indexOf(lowerWord, idx)) !== -1) {
          score += theme.weight[level];
          idx += lowerWord.length;
        }
      });
    });

    return score;
  }

  // === 主题检测主函数 ===
  function detect(text) {
    if (!text || typeof text !== 'string') return DEFAULT_THEME;

    var scores = {};
    Object.keys(THEME_KEYWORDS).forEach(function (themeKey) {
      scores[themeKey] = scoreText(text, themeKey);
    });

    // 找最高分
    var bestTheme = DEFAULT_THEME;
    var bestScore = 0;
    Object.keys(scores).forEach(function (themeKey) {
      if (scores[themeKey] > bestScore) {
        bestScore = scores[themeKey];
        bestTheme = themeKey;
      }
    });

    // 如果最高分 < 2, 用默认主题 (避免误判)
    if (bestScore < 2) return DEFAULT_THEME;

    return bestTheme;
  }

  // === 检测多个内容 (返回各主题占比) ===
  function analyze(contentList) {
    var counts = { business: 0, tech: 0, education: 0, fashion: 0 };
    var total = contentList.length;

    contentList.forEach(function (content) {
      var t = detect(content);
      counts[t]++;
    });

    return {
      counts: counts,
      ratios: {
        business: counts.business / total,
        tech: counts.tech / total,
        education: counts.education / total,
        fashion: counts.fashion / total
      },
      dominant: Object.keys(counts).reduce(function (a, b) {
        return counts[a] > counts[b] ? a : b;
      })
    };
  }

  // === 暴露 API ===
  window.WebPPT_ThemeDetect = {
    detect: detect,
    analyze: analyze,
    themes: THEME_KEYWORDS,
    DEFAULT_THEME: DEFAULT_THEME
  };
})();