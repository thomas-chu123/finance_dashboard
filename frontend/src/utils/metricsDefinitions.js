/**
 * Metrics Definitions - Shared across multiple views
 * Provides labels, tooltips, and configuration for financial metrics
 */

export const metricsDefinitions = {
  cagr: {
    label: 'CAGR',
    labelZh: '年化報酬',
    tooltip: '年化報酬率 (Compound Annual Growth Rate) = 代表投資組合在回測期間內的平均年化報酬率。高於 10% 被視為優異',
    suffix: '%',
  },
  sharpe_ratio: {
    label: 'SHARPE RATIO',
    labelZh: '夏普比例',
    tooltip: '夏普比例 = (年化報酬 - 無風險利率) ÷ 標準差，衡量每單位風險獲得的超額報酬。> 1 為良好，> 2 為優秀',
    suffix: '',
  },
  sortino_ratio: {
    label: 'SORTINO RATIO',
    labelZh: '索丁諾比例',
    tooltip: '索丁諾比例 = (年化報酬 - 無風險利率) ÷ 下方標準差，僅考慮向下風險。> 1 為良好，> 2 為優秀',
    suffix: '',
  },
  beta: {
    label: 'BETA',
    labelZh: '貝他係數',
    tooltip: '貝他係數 = 衡量組合相對於基準指數的波動性。Beta = 1 表示與指數同步；> 1 表示風險更高；< 1 表示風險更低',
    suffix: '',
  },
  max_drawdown: {
    label: 'MAX DRAWDOWN',
    labelZh: '最大回撤',
    tooltip: '最大回撤 = 從高點到低點的最大虧損百分比。反映投資組合在最差情況下的虧損程度',
    suffix: '%',
  },
  annual_std: {
    label: 'VOLATILITY (STD)',
    labelZh: '標準差',
    tooltip: '標準差 = 衡量投資組合報酬波動程度。值越高表示波動性越大，風險越高',
    suffix: '%',
  },
  var_95: {
    label: 'VAR (95%)',
    labelZh: '風險值',
    tooltip: '風險值 (Value at Risk) = 在 95% 信心水準下，單日可能的最大虧損百分比',
    suffix: '%',
  },
  final_amount: {
    label: 'FINAL AMOUNT',
    labelZh: '最終金額',
    tooltip: '最終金額 = 初始投資額加上投資收益的最終總額',
    suffix: '',
  },
  
  // Additional metrics for performance summary / comparison
  best_year: {
    label: '最佳年度',
    labelZh: '最佳年度',
    tooltip: '最佳年度 = 投資組合在單一年度中表現最好的報酬率',
    suffix: '%',
  },
  worst_year: {
    label: '最差年度',
    labelZh: '最差年度',
    tooltip: '最差年度 = 投資組合在單一年度中表現最差的報酬率',
    suffix: '%',
  },
}

/**
 * Get metric definition by key
 * @param {string} key - Metric key (e.g., 'cagr', 'sharpe_ratio')
 * @returns {Object} Metric definition with label, labelZh, tooltip, suffix
 */
export function getMetricDefinition(key) {
  return metricsDefinitions[key] || {
    label: key.toUpperCase(),
    labelZh: key,
    tooltip: 'No description available',
    suffix: '',
  }
}
