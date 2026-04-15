#!/usr/bin/env python3
"""
Backtest Debug Tool — 驗證回測計算的正確性並導出原始數據

用途：
1. 從 Yahoo Finance 或其他來源獲取歷史數據
2. 驗證 backtest 引擎的計算結果
3. 導出每年的原始數據到 CSV
4. 生成詳細的驗證報告

使用示例：
    python tests/debug_backtest.py --symbol VTI --start 2020-01-01 --end 2024-01-01
    python tests/debug_backtest.py --symbols VTI BND --weights 70 30 --start 2020-01-01 --end 2024-01-01
"""

import sys
import os
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import json
import logging
from typing import Dict, List, Tuple, Any
import argparse

# 添加後端模塊到路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.services.market_data import get_historical_prices, get_symbol_currency
from app.services.backtest_engine import run_backtest
import yfinance as yf

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 創建臨時輸出目錄
TEMP_DIR = Path(__file__).parent.parent / "temp"
TEMP_DIR.mkdir(exist_ok=True)


class BacktestDebugger:
    """回測調試工具"""
    
    def __init__(self, symbols: List[str], weights: List[float], start_date: str, end_date: str):
        """初始化調試器"""
        self.symbols = symbols
        self.weights = np.array(weights) / sum(weights)  # 正規化權重
        self.start_date = start_date
        self.end_date = end_date
        self.price_data = {}
        self.raw_data_frames = {}
        self.results = {}
        self.report = {}
    
    async def fetch_data(self) -> bool:
        """從 Yahoo Finance 獲取數據"""
        logger.info(f"正在獲取 {len(self.symbols)} 個符號的數據...")
        
        try:
            tasks = [get_historical_prices(sym, self.start_date, self.end_date) for sym in self.symbols]
            results = await asyncio.gather(*tasks)
            
            for sym, series in zip(self.symbols, results):
                if not series.empty:
                    self.price_data[sym] = series
                    logger.info(f"✓ {sym}: 獲取 {len(series)} 筆數據 ({series.index[0].date()} - {series.index[-1].date()})")
                else:
                    logger.warning(f"✗ {sym}: 未獲取到數據")
                    return False
            
            return len(self.price_data) > 0
        except Exception as e:
            logger.error(f"獲取數據失敗: {str(e)}")
            return False
    
    def _align_dates(self) -> pd.DataFrame:
        """對齊多個符號的日期"""
        logger.info("正在對齊日期...")
        
        # 轉換為 DataFrame
        df = pd.DataFrame(self.price_data)
        original_rows = len(df)
        
        # 使用前向填充和後向填充來處理節假日
        df = df.ffill().bfill()
        df = df.dropna(how='all')
        
        logger.info(f"  原始行數: {original_rows}, 對齊後: {len(df)}")
        logger.info(f"  日期範圍: {df.index[0].date()} - {df.index[-1].date()}")
        
        return df
    
    def _calculate_returns(self, prices_df: pd.DataFrame) -> pd.DataFrame:
        """計算日收益率"""
        returns = prices_df.pct_change().dropna()
        logger.info(f"計算收益率: {len(returns)} 個交易日")
        return returns
    
    def _export_yearly_data(self, prices_df: pd.DataFrame) -> Dict[int, pd.DataFrame]:
        """按年導出原始數據"""
        yearly_data = {}
        
        logger.info("\n正在按年導出原始數據...")
        
        for year, group in prices_df.groupby(prices_df.index.year):
            yearly_data[year] = group.copy()
            filename = TEMP_DIR / f"backtest_raw_data_{year}.csv"
            
            # 添加年回報計算
            returns = group.pct_change().dropna()
            group_with_returns = group.copy()
            
            for col in group.columns:
                group_with_returns[f"{col}_daily_return"] = returns[col]
            
            # 計算年末收益
            yearly_return = (1 + returns).prod() - 1
            
            group_with_returns.to_csv(filename)
            logger.info(f"✓ {year} 年: {len(group)} 筆數據 -> {filename}")
            logger.info(f"    日期範圍: {group.index[0].date()} - {group.index[-1].date()}")
            logger.info(f"    年回報率: {yearly_return.to_dict()}")
        
        return yearly_data
    
    def _validate_calculations(self, prices_df: pd.DataFrame) -> Dict[str, Any]:
        """驗證計算的正確性"""
        logger.info("\n驗證計算結果...")
        validation_report = {}
        
        # 1. 驗證價格數據
        validation_report['price_validation'] = {
            'symbols': list(prices_df.columns),
            'total_rows': len(prices_df),
            'date_range': {
                'start': prices_df.index[0].strftime('%Y-%m-%d'),
                'end': prices_df.index[-1].strftime('%Y-%m-%d')
            }
        }
        
        # 2. 計算收益率
        returns = prices_df.pct_change().dropna()
        
        # 3. 計算組合收益率
        portfolio_returns = (returns * self.weights).sum(axis=1)
        
        # 4. 計算關鍵指標
        years = len(returns) / 252
        total_return = (1 + portfolio_returns).prod() - 1
        cagr = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0
        ann_std = portfolio_returns.std() * np.sqrt(252)
        
        # 5. 計算最大回撤
        cumulative = (1 + portfolio_returns).cumprod()
        rolling_max = cumulative.cummax()
        max_dd = ((cumulative - rolling_max) / rolling_max).min()
        
        # 6. 計算夏普比例
        annual_ret = portfolio_returns.mean() * 252
        risk_free = 0.02
        if ann_std > 0:
            sharpe = (annual_ret - risk_free) / ann_std
        else:
            sharpe = 0
        
        validation_report['portfolio_metrics'] = {
            'total_return': float(total_return),
            'cagr': float(cagr),
            'annual_volatility': float(ann_std),
            'max_drawdown': float(max_dd),
            'sharpe_ratio': float(sharpe),
            'trading_days': len(returns),
            'years': float(years)
        }
        
        # 7. 按年回報
        annual_returns = {}
        for year, grp in returns.groupby(returns.index.year):
            yr_port = (grp * self.weights).sum(axis=1)
            annual_returns[str(year)] = float((1 + yr_port).prod() - 1)
        
        validation_report['annual_returns'] = annual_returns
        
        # 8. 各符號統計
        symbol_stats = {}
        for sym in prices_df.columns:
            sym_returns = returns[sym]
            symbol_stats[sym] = {
                'total_return': float((1 + sym_returns).prod() - 1),
                'annual_return': float(sym_returns.mean() * 252),
                'volatility': float(sym_returns.std() * np.sqrt(252)),
                'min_daily_return': float(sym_returns.min()),
                'max_daily_return': float(sym_returns.max()),
                'weight': float(self.weights[list(prices_df.columns).index(sym)])
            }
        
        validation_report['symbol_statistics'] = symbol_stats
        
        return validation_report
    
    def _export_validation_report(self, validation_report: Dict[str, Any]):
        """導出驗證報告"""
        report_file = TEMP_DIR / "backtest_validation_report.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(validation_report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n✓ 驗證報告已導出到: {report_file}")
        
        # 同時導出為人類可讀的格式
        text_report_file = TEMP_DIR / "backtest_validation_report.txt"
        with open(text_report_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("回測調試驗證報告\n")
            f.write("=" * 80 + "\n\n")
            
            f.write("📊 價格數據驗證\n")
            f.write("-" * 40 + "\n")
            pv = validation_report['price_validation']
            f.write(f"符號: {', '.join(pv['symbols'])}\n")
            f.write(f"總行數: {pv['total_rows']}\n")
            f.write(f"日期範圍: {pv['date_range']['start']} 至 {pv['date_range']['end']}\n\n")
            
            f.write("📈 組合績效指標\n")
            f.write("-" * 40 + "\n")
            pm = validation_report['portfolio_metrics']
            f.write(f"總回報: {pm['total_return']:.2%}\n")
            f.write(f"年化回報 (CAGR): {pm['cagr']:.2%}\n")
            f.write(f"年波動率: {pm['annual_volatility']:.2%}\n")
            f.write(f"最大回撤: {pm['max_drawdown']:.2%}\n")
            f.write(f"夏普比例: {pm['sharpe_ratio']:.2f}\n")
            f.write(f"交易天數: {pm['trading_days']}\n")
            f.write(f"年數: {pm['years']:.2f}\n\n")
            
            f.write("📅 按年回報率\n")
            f.write("-" * 40 + "\n")
            for year, ret in sorted(validation_report['annual_returns'].items()):
                f.write(f"{year}: {ret:.2%}\n")
            f.write("\n")
            
            f.write("📊 各符號統計\n")
            f.write("-" * 40 + "\n")
            for sym, stats in validation_report['symbol_statistics'].items():
                f.write(f"\n{sym} (權重: {stats['weight']:.1%})\n")
                f.write(f"  總回報: {stats['total_return']:.2%}\n")
                f.write(f"  年化回報: {stats['annual_return']:.2%}\n")
                f.write(f"  波動率: {stats['volatility']:.2%}\n")
                f.write(f"  最小日收益: {stats['min_daily_return']:.2%}\n")
                f.write(f"  最大日收益: {stats['max_daily_return']:.2%}\n")
            
            f.write("\n" + "=" * 80 + "\n")
        
        logger.info(f"✓ 文本報告已導出到: {text_report_file}")
    
    def _export_portfolio_value(self, prices_df: pd.DataFrame):
        """導出組合價值曲線"""
        returns = prices_df.pct_change().dropna()
        portfolio_returns = (returns * self.weights).sum(axis=1)
        portfolio_value = (1 + portfolio_returns).cumprod()
        
        portfolio_df = pd.DataFrame({
            'date': portfolio_value.index,
            'portfolio_value': portfolio_value.values,
            'cumulative_return': portfolio_value.values - 1
        })
        
        # 計算每日回報
        portfolio_df['daily_return'] = portfolio_returns.values
        
        # 計算滾動最大值和回撤
        rolling_max = portfolio_value.cummax()
        portfolio_df['drawdown'] = (portfolio_value.values - rolling_max.values) / rolling_max.values
        
        output_file = TEMP_DIR / "backtest_portfolio_value.csv"
        portfolio_df.to_csv(output_file, index=False)
        logger.info(f"✓ 組合價值曲線已導出到: {output_file}")
    
    async def run_debug(self):
        """運行完整的調試流程"""
        logger.info(f"\n{'='*80}")
        logger.info(f"🔍 Backtest 調試工具")
        logger.info(f"{'='*80}\n")
        
        logger.info(f"參數配置:")
        logger.info(f"  符號: {', '.join(self.symbols)}")
        logger.info(f"  權重: {dict(zip(self.symbols, self.weights.tolist()))}")
        logger.info(f"  日期範圍: {self.start_date} 至 {self.end_date}\n")
        
        # 第一步：獲取數據
        logger.info("第一步：獲取歷史數據")
        logger.info("-" * 80)
        if not await self.fetch_data():
            logger.error("❌ 無法獲取必要的數據")
            return False
        
        # 第二步：對齊日期
        logger.info("\n第二步：對齊日期")
        logger.info("-" * 80)
        prices_df = self._align_dates()
        
        # 第三步：驗證計算
        logger.info("\n第三步：驗證計算結果")
        logger.info("-" * 80)
        validation_report = self._validate_calculations(prices_df)
        
        # 第四步：導出數據
        logger.info("\n第四步：導出原始數據")
        logger.info("-" * 80)
        yearly_data = self._export_yearly_data(prices_df)
        
        # 第五步：導出組合價值
        logger.info("\n第五步：導出組合價值曲線")
        logger.info("-" * 80)
        self._export_portfolio_value(prices_df)
        
        # 第六步：導出驗證報告
        logger.info("\n第六步：導出驗證報告")
        logger.info("-" * 80)
        self._export_validation_report(validation_report)
        
        logger.info(f"\n{'='*80}")
        logger.info("✅ 調試完成！")
        logger.info(f"📁 所有數據已導出到: {TEMP_DIR}")
        logger.info(f"{'='*80}\n")
        
        return True


def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description='Backtest 調試工具 - 驗證回測計算並導出原始數據'
    )
    
    parser.add_argument(
        '--symbols',
        nargs='+',
        required=True,
        help='符號列表 (例: VTI BND SPY)'
    )
    
    parser.add_argument(
        '--weights',
        nargs='+',
        type=float,
        help='權重列表 (例: 70 30) - 不指定則等權'
    )
    
    parser.add_argument(
        '--start',
        required=True,
        help='起始日期 (例: 2020-01-01)'
    )
    
    parser.add_argument(
        '--end',
        required=True,
        help='結束日期 (例: 2024-01-01)'
    )
    
    args = parser.parse_args()
    
    # 驗證輸入
    symbols = args.symbols
    if args.weights:
        weights = args.weights
        if len(weights) != len(symbols):
            logger.error(f"❌ 權重數量 ({len(weights)}) 必須等於符號數量 ({len(symbols)})")
            sys.exit(1)
    else:
        weights = [1] * len(symbols)
    
    # 創建調試器並運行
    debugger = BacktestDebugger(symbols, weights, args.start, args.end)
    success = asyncio.run(debugger.run_debug())
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
