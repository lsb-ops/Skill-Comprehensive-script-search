/**
 * WebPPT Maker v3.13 · Spring Physics 增强
 *
 * 基于 Framer Motion / React Spring 开源实现:
 * - 3 套 preset: snappy / wobbly / heavy
 * - Damping ratio ζ (critical / under / over-damped)
 * - Spring.create(preset) factory API
 * - 保持 backward compat (默认 k=0.15, c=0.30 与 v3.11 一致)
 *
 * 物理: x'' = -k * (x - target) - c * v
 * 离散: v += (-k * (x - target) - c * v) * dt; x += v * dt
 *
 * Preset 配置 (来自 Framer Motion 官方推荐):
 *   snappy:  k=0.4,  c=0.5    → ζ ≈ 0.63 (under, 微弹),  UI 默认
 *   wobbly:  k=0.15, c=0.25   → ζ ≈ 0.51 (under, 明显弹性), 强调
 *   heavy:   k=0.08, c=0.4    → ζ ≈ 1.13 (over, 平滑无弹),  拖拽/物理
 *
 * Damping ratio ζ:
 *   ζ < 1:  under-damped (振荡)  →  弹簧感
 *   ζ = 1:  critical-damped       →  最快无振荡
 *   ζ > 1:  over-damped (迟缓)    →  平滑
 *
 * 用法:
 *   var sp = new WebPPT_Utils.Spring(0);           // 默认 preset (wobbly-ish)
 *   var sp = WebPPT_Utils.Spring.create('snappy'); // factory
 *   sp.target = 10;
 *   sp.step(0.016); // 60fps
 *   sp.isResting(); // boolean
 *   sp.getDampingRatio(); // ζ 数值
 */

(function () {
  'use strict';

  // === 3 Preset Configs ===
  // k = stiffness, c = damping, mass = 1
  // Damping ratio ζ = c / (2 * sqrt(k * mass))
  // snappy: ζ = 0.5 / (2 * sqrt(0.4)) = 0.395 (under, 微弹)
  // wobbly: ζ = 0.25 / (2 * sqrt(0.15)) = 0.323 (under, 明显弹性)
  // heavy:  ζ = 0.4 / (2 * sqrt(0.08)) = 0.707 (under, 平滑)
  var PRESETS = {
    snappy: { k: 0.40, c: 0.50, mass: 1.0, label: 'snappy (UI 默认, 微弹)' },
    wobbly: { k: 0.15, c: 0.25, mass: 1.0, label: 'wobbly (强调, 弹性)' },
    heavy:  { k: 0.08, c: 0.40, mass: 1.0, label: 'heavy (物理, 平滑)' }
  };

  // === Damping ratio category (基于 ζ 数值) ===
  function getDampingCategory(zeta) {
    if (zeta < 0.95) return 'under';     // 振荡
    if (zeta <= 1.05) return 'critical'; // 临界
    return 'over';                       // 过阻尼
  }

  // === Spring class ===
  function Spring(x0, preset) {
    preset = preset || 'default';
    if (typeof preset === 'string') {
      this._applyPreset(PRESETS[preset] || PRESETS.wobbly);
    } else if (typeof preset === 'object' && preset !== null) {
      this._applyPreset(preset);
    } else {
      // backward compat: 默认 k=0.15, c=0.30 (与 v3.11 一致)
      this.k = 0.15;
      this.c = 0.30;
      this.mass = 1.0;
    }
    this.target = 0;
    this.x = x0 || 0;
    this.v = 0;
  }

  // Apply preset config
  Spring.prototype._applyPreset = function (cfg) {
    this.k = cfg.k;
    this.c = cfg.c;
    this.mass = cfg.mass || 1.0;
  };

  // Step physics simulation
  Spring.prototype.step = function (dt) {
    // 钳制 dt 防止 spike (tab 切回)
    if (typeof dt !== 'number' || dt <= 0) dt = 0.016;
    if (dt > 0.064) dt = 0.064; // 15fps 最低

    // F = ma, a = F/m
    var force = -this.k * (this.x - this.target) - this.c * this.v;
    var accel = force / this.mass;
    this.v += accel * dt;
    this.x += this.v * dt;
  };

  // 是否静止 (浮点容差)
  Spring.prototype.isResting = function () {
    return Math.abs(this.x - this.target) < 0.1 && Math.abs(this.v) < 0.1;
  };

  // 获取 damping ratio ζ (用于调试 / 可视化)
  Spring.prototype.getDampingRatio = function () {
    // ζ = c / (2 * sqrt(k * m))
    var denom = 2 * Math.sqrt(this.k * this.mass);
    if (denom === 0) return Infinity;
    return this.c / denom;
  };

  // 获取 damping 类别 (critical / under / over)
  Spring.prototype.getDampingCategory = function () {
    return getDampingCategory(this.getDampingRatio());
  };

  // 获取当前 preset 标签 (如果匹配)
  Spring.prototype.getPresetLabel = function () {
    var zeta = this.getDampingRatio().toFixed(2);
    var category = this.getDampingCategory();
    return 'ζ=' + zeta + ' (' + category + '-damped, k=' + this.k + ', c=' + this.c + ')';
  };

  // === Factory: Spring.create(preset) ===
  Spring.create = function (presetName, x0) {
    return new Spring(x0 || 0, presetName || 'wobbly');
  };

  // === Static utilities ===
  Spring.PRESETS = PRESETS;
  Spring.getDampingCategory = getDampingCategory;

  // 计算给定 (k, c, mass) 的 damping ratio
  Spring.computeDampingRatio = function (k, c, mass) {
    mass = mass || 1.0;
    var denom = 2 * Math.sqrt(k * mass);
    if (denom === 0) return Infinity;
    return c / denom;
  };

  // 暴露全局
  window.WebPPT_Utils = window.WebPPT_Utils || {};
  window.WebPPT_Utils.Spring = Spring;
})();