/**
 * WebPPT Maker v3.12 · 整体搭配自动验证 (Harmony Check)
 *
 * 60-30-10 法则自动审计:
 * 1. accent 色面积占比 ≤ 15% (警告)
 * 2. critical attention 元素 ≤ 1 (单一焦点守则)
 * 3. high attention 元素 ≤ 2 (次焦点守则)
 * 4. accent-bg / btn-primary 数量 ≤ 1 (CTA 唯一性)
 * 5. visual-weight-5 元素 ≤ 1 (焦点唯一)
 *
 * 启用方式 (dev mode):
 *   <body data-harmony-check="show">      // 边角显示统计
 *   <body data-harmony-check="warn">      // 控制台 warn
 *   <body data-harmony-check="strict">    // 警告会变成红色边框
 *
 * API:
 *   WebPPT_Harmony.audit(rootEl)         // 返回 audit report
 *   WebPPT_Harmony.show(rootEl)          // 显示报告
 *   WebPPT_Harmony.config({ maxAccent: 0.10 })
 */

(function () {
  'use strict';

  var DEFAULTS = {
    maxAccentArea: 0.15,      // accent 面积占比上限
    maxCritical: 1,            // critical 元素上限
    maxHigh: 2,                // high 元素上限
    maxCTA: 1,                 // primary CTA 上限
    maxWeight5: 1,             // visual-weight-5 上限
    debounceMs: 300
  };

  var config = Object.assign({}, DEFAULTS);

  // 统计 accent 色面积
  function countAccentArea(root) {
    // BUG-06 fix: 移除 [data-attn="critical"] (critical 用 text-primary, 非 accent)
    var accentEls = root.querySelectorAll('[class*="accent"], [class*="bg-accent"], .btn-primary, .badge-accent');
    var totalArea = 0;
    var accentArea = 0;
    var all = root.querySelectorAll('*');
    var viewportArea = window.innerWidth * window.innerHeight;

    all.forEach(function (el) {
      var rect = el.getBoundingClientRect();
      var area = rect.width * rect.height;
      // BUG-07 fix: 完整视口判断 (left/right)
      if (area > 0 && rect.top < window.innerHeight && rect.bottom > 0
          && rect.left < window.innerWidth && rect.right > 0) {
        totalArea += area;
      }
    });

    accentEls.forEach(function (el) {
      var rect = el.getBoundingClientRect();
      if (rect.width > 0 && rect.height > 0 && rect.top < window.innerHeight && rect.bottom > 0
          && rect.left < window.innerWidth && rect.right > 0) {
        accentArea += rect.width * rect.height;
      }
    });

    // BUG-01 fix: 字段统一, ratio 用 viewportArea (60-30-10 法则语义)
    return {
      accentArea: accentArea,
      totalArea: totalArea,           // 真实可视元素面积
      viewportArea: viewportArea,     // 视口面积
      ratio: viewportArea > 0 ? accentArea / viewportArea : 0
    };
  }

  // 统计 attention 级别
  function countAttentionLevels(root) {
    var counts = { critical: 0, high: 0, normal: 0, low: 0, deco: 0 };
    var els = root.querySelectorAll('[data-attn]');
    els.forEach(function (el) {
      var level = el.getAttribute('data-attn');
      if (counts[level] !== undefined) counts[level]++;
    });
    return counts;
  }

  // 统计 CTA 数量
  function countCTA(root) {
    var primary = root.querySelectorAll('.btn-primary').length;
    var weight5 = root.querySelectorAll('.weight-5, [data-weight="5"]').length;
    return { primaryCTA: primary, weight5: weight5 };
  }

  // 执行审计 (v3.13 fix BUG-07: 默认 root 改为 reveal 当前 slide)
  function audit(root) {
    // BUG-07 fix: 优先审计 reveal.js 当前可见 slide
    if (!root) {
      var presentSlide = document.querySelector('.reveal .slides > section.present');
      root = presentSlide || document.body;
    }
    var accent = countAccentArea(root);
    var attention = countAttentionLevels(root);
    var cta = countCTA(root);

    var warnings = [];

    if (accent.ratio > config.maxAccentArea) {
      warnings.push({
        rule: '60-30-10',
        level: 'high',
        message: 'accent 面积占比 ' + (accent.ratio * 100).toFixed(1) + '% > ' + (config.maxAccentArea * 100) + '%, 视觉可能过载',
        actual: accent.ratio,
        expected: config.maxAccentArea
      });
    }

    if (attention.critical > config.maxCritical) {
      warnings.push({
        rule: 'single-focal',
        level: 'high',
        message: 'critical 元素 ' + attention.critical + ' 个 > ' + config.maxCritical + ' 个, 违反单一焦点守则',
        actual: attention.critical,
        expected: config.maxCritical
      });
    }

    if (attention.high > config.maxHigh) {
      warnings.push({
        rule: 'max-secondary',
        level: 'medium',
        message: 'high 元素 ' + attention.high + ' 个 > ' + config.maxHigh + ' 个, 次焦点过多',
        actual: attention.high,
        expected: config.maxHigh
      });
    }

    if (cta.primaryCTA > config.maxCTA) {
      warnings.push({
        rule: 'cta-unique',
        level: 'high',
        message: 'primary CTA ' + cta.primaryCTA + ' 个 > ' + config.maxCTA + ' 个, 多 CTA 分散注意力',
        actual: cta.primaryCTA,
        expected: config.maxCTA
      });
    }

    if (cta.weight5 > config.maxWeight5) {
      warnings.push({
        rule: 'weight-5-unique',
        level: 'medium',
        message: 'weight-5 元素 ' + cta.weight5 + ' 个 > ' + config.maxWeight5 + ' 个, 焦点冲突',
        actual: cta.weight5,
        expected: config.maxWeight5
      });
    }

    return {
      accent: accent,
      attention: attention,
      cta: cta,
      warnings: warnings,
      timestamp: Date.now()
    };
  }

  // 显示报告 (开发模式)
  function show(root) {
    var report = audit(root);

    // 移除旧的报告
    var old = document.getElementById('harmony-report');
    if (old) old.remove();

    // 创建报告元素
    var el = document.createElement('div');
    el.id = 'harmony-report';
    el.style.cssText = [
      'position: fixed',
      'bottom: 16px',
      'right: 16px',
      'background: rgba(15, 20, 25, 0.95)',
      'color: white',
      'padding: 12px 16px',
      'border-radius: 12px',
      'font-family: -apple-system, sans-serif',
      'font-size: 12px',
      'line-height: 1.5',
      'max-width: 320px',
      'z-index: 99999',
      'box-shadow: 0 8px 24px rgba(0,0,0,0.3)'
    ].join(';');

    var statusColor = report.warnings.length === 0 ? '#4ade80' : '#facc15';
    var html = '<div style="font-weight:700;margin-bottom:8px;color:' + statusColor + '">';
    html += report.warnings.length === 0 ? '✓ 搭配和谐' : '⚠ ' + report.warnings.length + ' 个警告';
    html += '</div>';

    html += '<div style="opacity:0.8;margin-bottom:4px">accent 面积: ' + (report.accent.ratio * 100).toFixed(1) + '%</div>';
    html += '<div style="opacity:0.8;margin-bottom:4px">attention: critical=' + report.attention.critical + ' high=' + report.attention.high + '</div>';
    html += '<div style="opacity:0.8;margin-bottom:8px">primary CTA: ' + report.cta.primaryCTA + '</div>';

    if (report.warnings.length > 0) {
      html += '<div style="border-top:1px solid rgba(255,255,255,0.2);padding-top:8px">';
      report.warnings.forEach(function (w) {
        var icon = w.level === 'high' ? '🛑' : '⚠️';
        html += '<div style="margin-bottom:4px">' + icon + ' ' + w.message + '</div>';
      });
      html += '</div>';
    }

    el.innerHTML = html;
    document.body.appendChild(el);
    return report;
  }

  // Console 警告
  function warn(root) {
    var report = audit(root);
    if (report.warnings.length > 0) {
      console.group('[Harmony Check] 发现 ' + report.warnings.length + ' 个搭配问题');
      report.warnings.forEach(function (w) {
        console.warn('[' + w.rule + ']', w.message);
      });
      console.groupEnd();
    } else {
      console.log('[Harmony Check] ✓ 60-30-10 / 单一焦点 / CTA 唯一 全部通过');
    }
    return report;
  }

  // 自动启动
  function autoStart() {
    var mode = document.body.getAttribute('data-harmony-check');
    if (!mode) return;

    var run = function () {
      if (mode === 'show') {
        show();
      } else if (mode === 'warn') {
        warn();
      } else if (mode === 'strict') {
        var report = audit();
        // strict 模式: 给违反规则的元素加红色边框
        report.warnings.forEach(function (w) {
          if (w.rule === 'single-focal') {
            var criticals = document.querySelectorAll('[data-attn="critical"]');
            criticals.forEach(function (el, i) {
              if (i >= config.maxCritical) el.style.outline = '2px solid red';
            });
          }
          if (w.rule === 'cta-unique') {
            var ctas = document.querySelectorAll('.btn-primary');
            ctas.forEach(function (el, i) {
              if (i >= config.maxCTA) el.style.outline = '2px solid red';
            });
          }
        });
      }
    };

    // 初次执行
    setTimeout(run, config.debounceMs);

    // 窗口变化时重新审计
    var resizeTimer = null;
    window.addEventListener('resize', function () {
      if (resizeTimer) clearTimeout(resizeTimer);
      resizeTimer = setTimeout(run, config.debounceMs);
    });
  }

  // 暴露 API
  window.WebPPT_Harmony = {
    audit: audit,
    show: show,
    warn: warn,
    config: function (opts) { config = Object.assign({}, DEFAULTS, opts); },
    autoStart: autoStart
  };

  // DOMContentLoaded 后启动
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', autoStart);
  } else {
    autoStart();
  }
})();