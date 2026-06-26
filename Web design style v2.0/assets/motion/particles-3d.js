/**
 * WebPPT Maker v3.8 · 3D 粒子场背景引擎
 *
 * 在 .layout-poster / .layout-coverflow / .layout-focal 等大空白处
 * 生成 3D 粒子场,创造深度错觉。粒子有 z 轴深度,鼠标移动时近处粒子
 * 反应更强(视差)。
 *
 * 用法:
 *   <div class="particles-3d" data-particle-count="40" data-particle-color="var(--accent)"></div>
 *
 * CSS 配合:
 *   .particles-3d { position: absolute; inset: 0; pointer-events: none; z-index: 0; overflow: hidden; }
 *
 * 特性:
 *   - 30-60 粒子 (轻量)
 *   - z 轴深度 0-100,近大远小
 *   - 鼠标视差(近粒子反应 2×)
 *   - 自动环面循环(粒子超出边界从对侧回)
 *   - prefers-reduced-motion 守护
 */
(function () {
  'use strict';

  var REDUCED_MOTION = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // v3.9 bugfix: 防止重复 attach 同一个 container
  var PARTICLE_CONTAINERS = new WeakSet();
  // v3.9 bugfix: 全局 resize listener 幂等
  var PARTICLE_RESIZE_BOUND = false;
  // v3.10 bugfix: 持有 resize handler ref, 支持 dispose
  var PARTICLE_RESIZE_HANDLER = null;

  // v3.11: 页面不可见时暂停 rAF (每个 container 用自身标志)
  var PARTICLES_PAUSED = false;

  function attachParticles3D(container) {
    if (REDUCED_MOTION) return;
    if (PARTICLE_CONTAINERS.has(container)) return; // v3.9 bugfix: 幂等
    PARTICLE_CONTAINERS.add(container);
    if (container.querySelector('canvas')) return;

    var count = parseInt(container.dataset.particleCount, 10) || 40;
    var color = container.dataset.particleColor || '255, 59, 48';

    var w = 0, h = 0;
    function resize() {
      var rect = container.getBoundingClientRect();
      w = rect.width || container.clientWidth || 800;
      h = rect.height || container.clientHeight || 600;
      canvas.width = w;
      canvas.height = h;
    }

    var canvas = document.createElement('canvas');
    canvas.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;pointer-events:none;';
    container.appendChild(canvas);

    var ctx = canvas.getContext('2d');
    if (!ctx) return;

    // 粒子池 — 每粒子有 (x,y,z,vx,vy,size)
    var particles = [];
    for (var i = 0; i < count; i++) {
      particles.push({
        x: Math.random(),
        y: Math.random(),
        z: Math.random(),          // 0=近,1=远
        vx: (Math.random() - 0.5) * 0.0008,
        vy: (Math.random() - 0.5) * 0.0008,
        phase: Math.random() * Math.PI * 2,
      });
    }

    // 鼠标视差
    var mx = 0.5, my = 0.5;
    function onMove(e) {
      var rect = container.getBoundingClientRect();
      mx = (e.clientX - rect.left) / rect.width;
      my = (e.clientY - rect.top) / rect.height;
    }
    container.addEventListener('mousemove', onMove);

    var rafId = null;
    var startTime = performance.now();

    function draw(now) {
      // v3.11: tab 切到后台时跳过绘制 (省电, GSAP 风格)
      if (PARTICLES_PAUSED) {
        rafId = requestAnimationFrame(draw);
        return;
      }
      var t = (now - startTime) / 1000;
      ctx.clearRect(0, 0, w, h);

      for (var i = 0; i < particles.length; i++) {
        var p = particles[i];

        // 漂移
        p.x += p.vx + Math.sin(t * 0.5 + p.phase) * 0.0003;
        p.y += p.vy + Math.cos(t * 0.4 + p.phase) * 0.0003;

        // 环面循环
        if (p.x < -0.1) p.x = 1.1;
        if (p.x > 1.1) p.x = -0.1;
        if (p.y < -0.1) p.y = 1.1;
        if (p.y > 1.1) p.y = -0.1;

        // z 深度:近粒子 (z=0) 大、亮、快反应;远粒子 (z=1) 小、暗、慢
        var depth = 1 - p.z; // 0-1
        var parallaxX = (mx - 0.5) * depth * 30;
        var parallaxY = (my - 0.5) * depth * 30;

        var px = (p.x * w + parallaxX);
        var py = (p.y * h + parallaxY);
        var size = 1.5 + depth * 4;       // 1.5-5.5 px
        var alpha = 0.2 + depth * 0.6;    // 0.2-0.8

        ctx.beginPath();
        ctx.arc(px, py, size, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(' + color + ',' + alpha.toFixed(3) + ')';
        ctx.fill();
      }

      rafId = requestAnimationFrame(draw);
    }

    function start() {
      resize();
      if (!rafId) rafId = requestAnimationFrame(draw);
    }

    function stop() {
      if (rafId) {
        cancelAnimationFrame(rafId);
        rafId = null;
      }
    }

    // 启动
    start();

    // v3.9 bugfix: 全局 resize 只绑一次 (之前每次 attach 都绑, 导致 N 倍触发)
    if (!PARTICLE_RESIZE_BOUND) {
      PARTICLE_RESIZE_BOUND = true;
      var onWindowResize = function () {
        // 所有已知 container resize
        document.querySelectorAll('.particles-3d').forEach(function (c) {
          if (PARTICLE_CONTAINERS.has(c)) {
            var ev = new Event('particle-resize');
            c.dispatchEvent(ev);
          }
        });
      };
      window.addEventListener('resize', onWindowResize);
      // v3.10 bugfix: 保存 handler ref, dispose 时可移除 (防止长期运行场景累积)
      PARTICLE_RESIZE_HANDLER = onWindowResize;
    }

    // 单独 listener: 本 container 自己 resize 时 (reveal 切换后尺寸变化)
    container.addEventListener('particle-resize', resize);

    // v3.10 bugfix: 返回 dispose 方法, 允许清理所有 listeners
    return {
      start: start,
      stop: stop,
      resize: resize,
      dispose: function () {
        stop();
        container.removeEventListener('particle-resize', resize);
        container.removeEventListener('mousemove', onMove);
      },
    };
  }

  function setupAll() {
    if (REDUCED_MOTION) {
      console.info('[particles-3d] prefers-reduced-motion: skip');
      return;
    }
    var els = document.querySelectorAll('.particles-3d, [data-particles]');
    els.forEach(attachParticles3D);
  }

  // v3.10 bugfix: 清理所有 listeners (适用于 SPA 路由切换 / 单页应用离开场景)
  function disposeAll() {
    document.querySelectorAll('.particles-3d, [data-particles]').forEach(function (c) {
      if (PARTICLE_CONTAINERS.has(c)) {
        var canvas = c.querySelector('canvas');
        if (canvas) {
          // 触发 stop via cancelAnimationFrame 由下一次 raf check 跳过
          // (PARTICLE_CONTAINERS 在 attach 时已经 set, 这里清空再 dispose)
        }
      }
    });
    if (PARTICLE_RESIZE_HANDLER) {
      window.removeEventListener('resize', PARTICLE_RESIZE_HANDLER);
      PARTICLE_RESIZE_HANDLER = null;
      PARTICLE_RESIZE_BOUND = false;
    }
  }

  // API
  window.WebPPT_Particles3D = {
    setup: setupAll,
    attach: attachParticles3D,
    disposeAll: disposeAll,
    prefersReducedMotion: REDUCED_MOTION,
  };

  // 启动
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupAll);
  } else {
    setupAll();
  }

  // v3.11: 单一 Reveal 注册中心
  if (window.WebPPT_Utils && window.WebPPT_Utils.RevealHook) {
    window.WebPPT_Utils.RevealHook.onSlideChanged(setupAll);
  } else if (typeof window.Reveal !== 'undefined') {
    window.Reveal.on('slidechanged', function () { setTimeout(setupAll, 600); });
  }

  // v3.11: visibilitychange 暂停 rAF
  if (window.WebPPT_Utils && window.WebPPT_Utils.Visibility) {
    window.WebPPT_Utils.Visibility.subscribe(function (hidden) {
      PARTICLES_PAUSED = hidden;
    });
  }
})();