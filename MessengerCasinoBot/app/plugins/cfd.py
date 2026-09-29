import os
import time
import requests
from PIL import Image, ImageDraw
from base_game_plugin import BaseGamePlugin
from logger import logger


# ============================================================
# CONFIGURATION
# ============================================================

YAHOO_BASE = "https://query1.finance.yahoo.com/v8/finance/chart/"
YAHOO_SEARCH = "https://query1.finance.yahoo.com/v1/finance/search"

LEVERAGE = 10
COMMISSION_PCT = 0.001
MIN_MARGIN = 10
MAX_MARGIN = 100000
MAX_OPEN_POSITIONS = 5

CHART_RANGE = "1mo"
CHART_INTERVAL = "1d"

ITEMS_PER_PAGE = 15

OVERLAY_FONT_SCALE = 0.7
OVERLAY_AVATAR_SIZE = 60
OVERLAY_MARGIN = 10

CATEGORY_NAMES = {
    "stock_us": "US stocks",
    "stock_pl": "Polish stocks (GPW)",
    "commodity": "Commodities",
    "crypto": "Crypto",
}

CATEGORY_SHORT = {
    "stock_us": "us",
    "stock_pl": "pl",
    "commodity": "com",
    "crypto": "crypto",
    "all": "all",
}

CATEGORY_INPUT_MAP = {
    "us": "stock_us", "usa": "stock_us", "stocks": "stock_us",
    "pl": "stock_pl", "gpw": "stock_pl", "polish": "stock_pl",
    "com": "commodity", "commodities": "commodity", "surowce": "commodity",
    "crypto": "crypto", "krypto": "crypto",
}

CATEGORY_ORDER = {
    "stock_us": 0,
    "stock_pl": 1,
    "commodity": 2,
    "crypto": 3,
    "yahoo": 99,
}

COMMAND_ALIASES = {
    "p": "price", "c": "price", "q": "price", "quote": "price", "chart": "price",
    "l": "long",
    "s": "short",
    "cl": "close", "sell": "close",
    "pos": "positions", "my": "positions", "status": "positions",
    "ls": "list", "symbols": "list", "markets": "list",
    "f": "search", "find": "search",
    "h": "help", "?": "help",
}

POPULAR_SYMBOLS = {
    # --- US stocks (30) ---
    "AAPL":  ("Apple Inc.", "NASDAQ", "stock_us"),
    "MSFT":  ("Microsoft Corp.", "NASDAQ", "stock_us"),
    "TSLA":  ("Tesla Inc.", "NASDAQ", "stock_us"),
    "NVDA":  ("NVIDIA Corp.", "NASDAQ", "stock_us"),
    "AMZN":  ("Amazon.com Inc.", "NASDAQ", "stock_us"),
    "GOOGL": ("Alphabet Inc.", "NASDAQ", "stock_us"),
    "META":  ("Meta Platforms Inc.", "NASDAQ", "stock_us"),
    "NFLX":  ("Netflix Inc.", "NASDAQ", "stock_us"),
    "AMD":   ("Advanced Micro Devices", "NASDAQ", "stock_us"),
    "INTC":  ("Intel Corp.", "NASDAQ", "stock_us"),
    "JPM":   ("JPMorgan Chase & Co.", "NYSE", "stock_us"),
    "V":     ("Visa Inc.", "NYSE", "stock_us"),
    "WMT":   ("Walmart Inc.", "NYSE", "stock_us"),
    "DIS":   ("Walt Disney Co.", "NYSE", "stock_us"),
    "BA":    ("Boeing Co.", "NYSE", "stock_us"),
    "KO":    ("Coca-Cola Co.", "NYSE", "stock_us"),
    "PEP":   ("PepsiCo Inc.", "NASDAQ", "stock_us"),
    "XOM":   ("Exxon Mobil Corp.", "NYSE", "stock_us"),
    "CVX":   ("Chevron Corp.", "NYSE", "stock_us"),
    "PFE":   ("Pfizer Inc.", "NYSE", "stock_us"),
    "PYPL":  ("PayPal Holdings", "NASDAQ", "stock_us"),
    "ADBE":  ("Adobe Inc.", "NASDAQ", "stock_us"),
    "CRM":   ("Salesforce Inc.", "NYSE", "stock_us"),
    "ORCL":  ("Oracle Corp.", "NYSE", "stock_us"),
    "CSCO":  ("Cisco Systems", "NASDAQ", "stock_us"),
    "QCOM":  ("Qualcomm Inc.", "NASDAQ", "stock_us"),
    "TXN":   ("Texas Instruments", "NASDAQ", "stock_us"),
    "COST":  ("Costco Wholesale", "NASDAQ", "stock_us"),
    "NKE":   ("Nike Inc.", "NYSE", "stock_us"),
    "MCD":   ("McDonald's Corp.", "NYSE", "stock_us"),

    # --- Polish stocks (30) ---
    "PKN.WA":  ("PKN Orlen", "GPW", "stock_pl"),
    "PKO.WA":  ("PKO BP", "GPW", "stock_pl"),
    "PZU.WA":  ("PZU", "GPW", "stock_pl"),
    "KGH.WA":  ("KGHM", "GPW", "stock_pl"),
    "LPP.WA":  ("LPP", "GPW", "stock_pl"),
    "CDR.WA":  ("CD Projekt", "GPW", "stock_pl"),
    "DNP.WA":  ("Dino Polska", "GPW", "stock_pl"),
    "MBK.WA":  ("mBank", "GPW", "stock_pl"),
    "PEO.WA":  ("Bank Pekao", "GPW", "stock_pl"),
    "SPL.WA":  ("Santander Bank Polska", "GPW", "stock_pl"),
    "ALE.WA":  ("Allegro", "GPW", "stock_pl"),
    "CPS.WA":  ("Cyfrowy Polsat", "GPW", "stock_pl"),
    "OPL.WA":  ("Orange Polska", "GPW", "stock_pl"),
    "PGN.WA":  ("PGNiG", "GPW", "stock_pl"),
    "TPE.WA":  ("Tauron", "GPW", "stock_pl"),
    "ENG.WA":  ("Enea", "GPW", "stock_pl"),
    "JSW.WA":  ("JSW", "GPW", "stock_pl"),
    "CCC.WA":  ("CCC", "GPW", "stock_pl"),
    "PLW.WA":  ("PlayWay", "GPW", "stock_pl"),
    "ATT.WA":  ("Atende", "GPW", "stock_pl"),
    "ASB.WA":  ("ASBIS", "GPW", "stock_pl"),
    "MIL.WA":  ("Milkiland", "GPW", "stock_pl"),
    "KTY.WA":  ("Kety", "GPW", "stock_pl"),
    "BHW.WA":  ("Bank Handlowy", "GPW", "stock_pl"),
    "BNP.WA":  ("BNP Paribas Polska", "GPW", "stock_pl"),
    "ING.WA":  ("ING Bank Slaski", "GPW", "stock_pl"),
    "ALR.WA":  ("Alior Bank", "GPW", "stock_pl"),
    "GTC.WA":  ("GTC", "GPW", "stock_pl"),
    "ECH.WA":  ("Echo Investment", "GPW", "stock_pl"),
    "TEN.WA":  ("Ten Square Games", "GPW", "stock_pl"),

    # --- Commodities (30) ---
    "GC=F":  ("Gold", "COMEX", "commodity"),
    "SI=F":  ("Silver", "COMEX", "commodity"),
    "PL=F":  ("Platinum", "NYMEX", "commodity"),
    "HG=F":  ("Copper", "COMEX", "commodity"),
    "CL=F":  ("Crude Oil WTI", "NYMEX", "commodity"),
    "BZ=F":  ("Brent Crude Oil", "NYMEX", "commodity"),
    "NG=F":  ("Natural Gas", "NYMEX", "commodity"),
    "ZC=F":  ("Corn", "CBOT", "commodity"),
    "ZW=F":  ("Wheat", "CBOT", "commodity"),
    "ZS=F":  ("Soybean", "CBOT", "commodity"),
    "CC=F":  ("Cocoa", "ICE", "commodity"),
    "KC=F":  ("Coffee", "ICE", "commodity"),
    "SB=F":  ("Sugar", "ICE", "commodity"),
    "CT=F":  ("Cotton", "ICE", "commodity"),
    "LE=F":  ("Live Cattle", "CME", "commodity"),
    "HE=F":  ("Lean Hogs", "CME", "commodity"),
    "GF=F":  ("Feeder Cattle", "CME", "commodity"),
    "ZL=F":  ("Soybean Oil", "CBOT", "commodity"),
    "ZM=F":  ("Soybean Meal", "CBOT", "commodity"),
    "ZR=F":  ("Rough Rice", "CBOT", "commodity"),
    "ZO=F":  ("Oats", "CBOT", "commodity"),
    "KE=F":  ("Kansas Wheat", "CBOT", "commodity"),
    "PA=F":  ("Palladium", "NYMEX", "commodity"),
    "RB=F":  ("RBOB Gasoline", "NYMEX", "commodity"),
    "HO=F":  ("Heating Oil", "NYMEX", "commodity"),
    "OA=F":  ("Oat Futures", "CBOT", "commodity"),
    "DX=F":  ("US Dollar Index", "ICE", "commodity"),
    "VX=F":  ("VIX Futures", "CBOE", "commodity"),
    "ES=F":  ("S&P 500 Futures", "CME", "commodity"),
    "NQ=F":  ("Nasdaq 100 Futures", "CME", "commodity"),

    # --- Crypto (30) ---
    "BTC-USD": ("Bitcoin", "CCC", "crypto"),
    "ETH-USD": ("Ethereum", "CCC", "crypto"),
    "SOL-USD": ("Solana", "CCC", "crypto"),
    "BNB-USD": ("Binance Coin", "CCC", "crypto"),
    "XRP-USD": ("Ripple", "CCC", "crypto"),
    "ADA-USD": ("Cardano", "CCC", "crypto"),
    "DOGE-USD":("Dogecoin", "CCC", "crypto"),
    "DOT-USD": ("Polkadot", "CCC", "crypto"),
    "LTC-USD": ("Litecoin", "CCC", "crypto"),
    "LINK-USD":("Chainlink", "CCC", "crypto"),
    "MATIC-USD":("Polygon", "CCC", "crypto"),
    "AVAX-USD":("Avalanche", "CCC", "crypto"),
    "ATOM-USD":("Cosmos", "CCC", "crypto"),
    "XLM-USD": ("Stellar", "CCC", "crypto"),
    "ALGO-USD":("Algorand", "CCC", "crypto"),
    "VET-USD": ("VeChain", "CCC", "crypto"),
    "FIL-USD": ("Filecoin", "CCC", "crypto"),
    "TRX-USD": ("TRON", "CCC", "crypto"),
    "ETC-USD": ("Ethereum Classic", "CCC", "crypto"),
    "AAVE-USD":("Aave", "CCC", "crypto"),
    "UNI-USD": ("Uniswap", "CCC", "crypto"),
    "MKR-USD": ("Maker", "CCC", "crypto"),
    "COMP-USD":("Compound", "CCC", "crypto"),
    "SNX-USD": ("Synthetix", "CCC", "crypto"),
    "CRV-USD": ("Curve DAO", "CCC", "crypto"),
    "BAT-USD": ("Basic Attention", "CCC", "crypto"),
    "ZEC-USD": ("Zcash", "CCC", "crypto"),
    "DASH-USD":("Dash", "CCC", "crypto"),
    "XMR-USD": ("Monero", "CCC", "crypto"),
    "EOS-USD": ("EOS", "CCC", "crypto"),
}


# ============================================================
# YAHOO CLIENT
# ============================================================

class YahooClient:
    def __init__(self):
        self.base_url = YAHOO_BASE
        self.search_url = YAHOO_SEARCH
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0 Safari/537.36"
        })

    def fetch_chart(self, symbol, range_=CHART_RANGE, interval=CHART_INTERVAL):
        try:
            url = f"{self.base_url}{symbol}"
            params = {"range": range_, "interval": interval}
            resp = self.session.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            result = data.get("chart", {}).get("result")
            if not result:
                return None
            return result[0]
        except requests.exceptions.RequestException as e:
            logger.error(f"[CFD] Yahoo error for {symbol}: {e}")
            return None
        except Exception as e:
            logger.error(f"[CFD] Yahoo unexpected error: {e}")
            return None

    def get_quote(self, symbol):
        chart = self.fetch_chart(symbol, range_="5d", interval="1d")
        if not chart:
            return None
        meta = chart.get("meta", {})
        price = meta.get("regularMarketPrice")
        if not price:
            return None

        current = float(price)
        prev_close = float(
            meta.get("previousClose", 0)
            or meta.get("chartPreviousClose", 0)
            or 0
        )

        if prev_close:
            change = current - prev_close
            change_pct = (change / prev_close) * 100
        else:
            change = 0.0
            change_pct = 0.0

        return {
            "c": current,
            "d": change,
            "dp": change_pct,
            "o": float(meta.get("regularMarketOpen", 0) or prev_close or 0),
            "h": float(meta.get("regularMarketDayHigh", 0) or 0),
            "l": float(meta.get("regularMarketDayLow", 0) or 0),
            "pc": prev_close,
            "volume": float(meta.get("regularMarketVolume", 0) or 0),
            "name": meta.get("longName") or meta.get("shortName") or symbol,
            "currency": meta.get("currency", "USD"),
            "exchange": meta.get("fullExchangeName", ""),
        }

    def get_price(self, symbol):
        chart = self.fetch_chart(symbol, range_="5d", interval="1d")
        if not chart:
            return None
        price = chart.get("meta", {}).get("regularMarketPrice")
        return float(price) if price else None

    def get_candles(self, symbol, range_=CHART_RANGE, interval=CHART_INTERVAL):
        chart = self.fetch_chart(symbol, range_, interval)
        if not chart:
            return []

        timestamps = chart.get("timestamp", [])
        quote = chart.get("indicators", {}).get("quote", [{}])
        if not quote:
            return []
        quote = quote[0]

        opens = quote.get("open", [])
        highs = quote.get("high", [])
        lows = quote.get("low", [])
        closes = quote.get("close", [])

        candles = []
        for i, ts in enumerate(timestamps):
            if i >= len(opens) or i >= len(closes):
                break
            o, h, l, c = opens[i], highs[i], lows[i], closes[i]
            if None in (o, h, l, c):
                continue
            candles.append({
                "open": float(o),
                "high": float(h),
                "low": float(l),
                "close": float(c),
                "start": float(ts),
                "interpolated": False,
            })
        return candles

    def search_symbols(self, query, max_results=20):
        try:
            url = self.search_url
            params = {
                "q": query,
                "quotesCount": max_results,
                "newsCount": 0,
                "listsCount": 0,
            }
            resp = self.session.get(url, params=params, timeout=8)
            resp.raise_for_status()
            data = resp.json()
            quotes = data.get("quotes", [])
            results = []
            for item in quotes:
                qtype = (item.get("quoteType") or "").upper()
                if qtype not in ("EQUITY", "ETF", "FUTURE", "CRYPTOCURRENCY"):
                    continue
                sym = item.get("symbol")
                if not sym:
                    continue
                name = item.get("longname") or item.get("shortname") or sym
                exch = item.get("exchDisp") or item.get("exchange") or ""
                results.append((sym, name, exch, "yahoo"))
            return results
        except Exception as e:
            logger.error(f"[CFD] Yahoo search error for '{query}': {e}")
            return []


# ============================================================
# CFD POSITION
# ============================================================

class CFDPosition:
    def __init__(self, user_id, symbol, direction, margin, entry_price,
                 leverage=LEVERAGE, stop_loss_pct=None, take_profit_pct=None):
        self.user_id = user_id
        self.symbol = symbol.upper()
        self.direction = direction.upper()
        self.margin = margin
        self.entry_price = entry_price
        self.leverage = leverage
        self.size = margin * leverage
        self.opened_at = time.time()
        self.position_id = f"{symbol}_{direction}_{int(self.opened_at)}"
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct

    def current_pnl(self, current_price):
        if self.direction == "LONG":
            pct = (current_price - self.entry_price) / self.entry_price
        else:
            pct = (self.entry_price - current_price) / self.entry_price
        pnl = self.size * pct
        commission = self.size * COMMISSION_PCT * 2
        return pnl - commission

    def to_dict(self):
        return {
            "position_id": self.position_id,
            "user_id": self.user_id,
            "symbol": self.symbol,
            "direction": self.direction,
            "margin": self.margin,
            "entry_price": self.entry_price,
            "leverage": self.leverage,
            "size": self.size,
            "opened_at": self.opened_at,
            "stop_loss_pct": self.stop_loss_pct,
            "take_profit_pct": self.take_profit_pct,
        }

    @staticmethod
    def from_dict(data):
        pos = CFDPosition(
            user_id=data.get("user_id", ""),
            symbol=data.get("symbol", "UNKNOWN"),
            direction=data.get("direction", "LONG"),
            margin=float(data.get("margin", 0)),
            entry_price=float(data.get("entry_price", 0)),
            leverage=int(data.get("leverage", LEVERAGE)),
            stop_loss_pct=data.get("stop_loss_pct"),
            take_profit_pct=data.get("take_profit_pct"),
        )
        pos.opened_at = data.get("opened_at", time.time())
        pos.position_id = data.get("position_id", pos.position_id)
        pos.size = data.get("size", pos.margin * pos.leverage)
        return pos


# ============================================================
# TABLE GENERATOR
# ============================================================

class TableGenerator:
    PADDING = 20
    HEADER_H = 50
    ROW_H = 34
    FONT_SIZE = 15
    HEADER_FONT_SIZE = 16
    TITLE_FONT_SIZE = 20

    COLORS = {
        "bg": (18, 20, 28, 255),
        "panel": (28, 31, 42, 255),
        "header_bg": (40, 44, 58, 255),
        "border": (60, 65, 85, 255),
        "row_alt": (24, 27, 36, 255),
        "text": (240, 240, 245, 255),
        "muted": (160, 165, 180, 255),
        "green": (76, 200, 120, 255),
        "red": (230, 80, 80, 255),
        "gold": (255, 200, 90, 255),
    }

    def __init__(self, text_renderer):
        self.text_renderer = text_renderer

    def _text(self, text, size, color):
        if self.text_renderer:
            return self.text_renderer.render_text(
                text=str(text), font_size=int(size), color=color,
                stroke_width=0, stroke_color=(0, 0, 0, 0)
            )
        return None

    def generate(self, title, columns, rows, output_path,
                 col_align=None, col_colors=None, footer=None):
        if not columns:
            return None

        n_cols = len(columns)
        if col_align is None:
            col_align = ["left"] * n_cols

        col_widths = []
        for c in range(n_cols):
            hdr_img = self._text(columns[c], self.HEADER_FONT_SIZE, self.COLORS["text"])
            w = hdr_img.width if hdr_img else len(columns[c]) * 10
            for row in rows:
                if c < len(row):
                    cell_img = self._text(row[c], self.FONT_SIZE, self.COLORS["text"])
                    cw = cell_img.width if cell_img else len(str(row[c])) * 9
                    if cw > w:
                        w = cw
            col_widths.append(w + 24)

        total_width = sum(col_widths) + 2 * self.PADDING
        title_h = 50 if title else 0
        footer_h = 30 if footer else 0
        total_height = (
            self.PADDING + title_h + self.HEADER_H
            + len(rows) * self.ROW_H + self.PADDING + footer_h
        )
        total_width = max(total_width, 500)

        img = Image.new("RGBA", (int(total_width), int(total_height)), self.COLORS["bg"])
        draw = ImageDraw.Draw(img)

        draw.rectangle([1, 1, int(total_width) - 2, int(total_height) - 2],
                       outline=self.COLORS["border"], width=2)

        y = self.PADDING

        if title:
            title_img = self._text(title, self.TITLE_FONT_SIZE, self.COLORS["gold"])
            if title_img:
                img.alpha_composite(title_img, (int(self.PADDING), int(y)))
            y += title_h

        table_x = self.PADDING
        table_w = total_width - 2 * self.PADDING

        draw.rectangle([int(table_x), int(y), int(table_x + table_w),
                        int(y + self.HEADER_H)], fill=self.COLORS["header_bg"])

        cx = table_x
        for c in range(n_cols):
            cw = col_widths[c]
            hdr_img = self._text(columns[c], self.HEADER_FONT_SIZE, self.COLORS["text"])
            if hdr_img:
                if col_align[c] == "right":
                    tx = cx + cw - hdr_img.width - 12
                elif col_align[c] == "center":
                    tx = cx + (cw - hdr_img.width) // 2
                else:
                    tx = cx + 12
                ty = y + (self.HEADER_H - hdr_img.height) // 2
                img.alpha_composite(hdr_img, (int(tx), int(ty)))
            cx += cw

        y += self.HEADER_H

        for r_idx, row in enumerate(rows):
            row_bg = self.COLORS["panel"] if r_idx % 2 == 0 else self.COLORS["row_alt"]
            draw.rectangle([int(table_x), int(y), int(table_x + table_w),
                            int(y + self.ROW_H)], fill=row_bg)

            cx = table_x
            for c in range(n_cols):
                cw = col_widths[c]
                val = row[c] if c < len(row) else ""
                color = self.COLORS["text"]
                if col_colors and r_idx in col_colors and c in col_colors[r_idx]:
                    color = col_colors[r_idx][c]

                cell_img = self._text(val, self.FONT_SIZE, color)
                if cell_img:
                    if col_align[c] == "right":
                        tx = cx + cw - cell_img.width - 12
                    elif col_align[c] == "center":
                        tx = cx + (cw - cell_img.width) // 2
                    else:
                        tx = cx + 12
                    ty = y + (self.ROW_H - cell_img.height) // 2
                    img.alpha_composite(cell_img, (int(tx), int(ty)))
                cx += cw

            draw.line([(int(table_x), int(y + self.ROW_H)),
                       (int(table_x + table_w), int(y + self.ROW_H))],
                      fill=self.COLORS["border"], width=1)

            y += self.ROW_H

        if footer:
            footer_img = self._text(footer, 13, self.COLORS["muted"])
            if footer_img:
                img.alpha_composite(footer_img,
                    (int(self.PADDING),
                     int(total_height - self.PADDING - footer_img.height + 10)))

        img.convert("RGB").save(output_path, format="PNG", optimize=True)
        return output_path


# ============================================================
# CHART GENERATOR
# ============================================================

class ChartGenerator:
    WIDTH = 720
    HEIGHT = 480
    PADDING = 30
    HEADER_H = 90
    STATS_H = 130
    CHART_TOP_MARGIN = 15

    COLORS = {
        "bg": (18, 20, 28, 255),
        "panel": (28, 31, 42, 255),
        "border": (60, 65, 85, 255),
        "text": (240, 240, 245, 255),
        "muted": (160, 165, 180, 255),
        "green": (76, 200, 120, 255),
        "red": (230, 80, 80, 255),
        "grid": (45, 50, 65, 255),
        "gold": (255, 200, 90, 255),
        "wick": (200, 205, 220, 255),
        "long": (76, 200, 120, 255),
        "short": (230, 80, 80, 255),
        "sl": (255, 150, 60, 255),
        "tp": (100, 200, 255, 255),
    }

    def __init__(self, text_renderer):
        self.text_renderer = text_renderer

    def _text(self, text, size, color):
        if self.text_renderer:
            return self.text_renderer.render_text(
                text=str(text), font_size=int(size), color=color,
                stroke_width=0, stroke_color=(0, 0, 0, 0)
            )
        return None

    def _to_y_factory(self, min_p, max_p, chart_y1, chart_y2):
        def to_y(price):
            if max_p == min_p:
                return int((chart_y1 + chart_y2) // 2)
            ratio = (price - min_p) / (max_p - min_p)
            return int(chart_y2 - ratio * (chart_y2 - chart_y1))
        return to_y

    def _draw_candles(self, img, draw, candles,
                      chart_x1, chart_x2, chart_y1, chart_y2, min_p, max_p):
        n = len(candles)
        if n == 0:
            return

        to_y = self._to_y_factory(min_p, max_p, chart_y1, chart_y2)
        total_w = chart_x2 - chart_x1

        if n == 1:
            body_w = 90
            cx = int((chart_x1 + chart_x2) // 2)
            positions = [cx]
        else:
            slot_w = total_w / n
            body_w = max(3, int(slot_w * 0.65))
            positions = [int(chart_x1 + (i + 0.5) * slot_w) for i in range(n)]

        wick_w = max(1, body_w // 12)

        for i, c in enumerate(candles):
            cx = positions[i]
            y_high = to_y(c["high"])
            y_low = to_y(c["low"])
            y_open = to_y(c["open"])
            y_close = to_y(c["close"])

            draw.line([(cx, y_high), (cx, y_low)],
                      fill=self.COLORS["wick"], width=wick_w)

            body_top = min(y_open, y_close)
            body_bot = max(y_open, y_close)
            if body_bot - body_top < 2:
                body_bot = body_top + 2

            is_bullish = c["close"] >= c["open"]
            body_color = self.COLORS["green"] if is_bullish else self.COLORS["red"]

            outline_color = (255, 255, 255, 255) if n == 1 else body_color
            outline_w = 2 if n == 1 else 1

            draw.rectangle([cx - body_w // 2, body_top,
                            cx + body_w // 2, body_bot],
                           fill=body_color, outline=outline_color, width=outline_w)

    def _draw_dashed_hline(self, draw, x1, x2, y, color, dash=8, gap=4, width=2):
        x = int(x1)
        while x < int(x2):
            draw.line([(x, y), (min(x + dash, int(x2)), y)], fill=color, width=width)
            x += dash + gap

    def _draw_entry_lines(self, img, draw, positions, current,
                          chart_x1, chart_x2, chart_y1, chart_y2, min_p, max_p):
        if not positions:
            return

        to_y = self._to_y_factory(min_p, max_p, chart_y1, chart_y2)
        sorted_positions = sorted(
            positions,
            key=lambda p: 0 if p.direction == "LONG" else 1
        )

        used_labels = []

        for position in sorted_positions:
            entry = position.entry_price
            if not (min_p <= entry <= max_p):
                continue

            ey = to_y(entry)

            if position.direction == "LONG":
                color = self.COLORS["long"]
                arrow_up = True
            else:
                color = self.COLORS["short"]
                arrow_up = False

            self._draw_dashed_hline(draw, chart_x1, chart_x2, ey, color)

            arrow_x = int(chart_x2) - 14
            if arrow_up:
                draw.polygon(
                    [(arrow_x, ey - 6), (arrow_x + 8, ey), (arrow_x, ey + 6)],
                    fill=color
                )
            else:
                draw.polygon(
                    [(arrow_x, ey + 6), (arrow_x + 8, ey), (arrow_x, ey - 6)],
                    fill=color
                )

            self._draw_sl_tp_lines(img, draw, position, to_y, current,
                                   chart_x1, chart_x2, min_p, max_p)

            label = f"{position.direction} {entry:,.2f}"
            label_img = self._text(label, 12, color)
            if not label_img:
                continue

            lx = int(chart_x1) + 6
            ly = ey - label_img.height - 3

            offset_attempts = 0
            while offset_attempts < 6:
                collision = False
                for (uy1, uy2) in used_labels:
                    if not (ly + label_img.height < uy1 or ly > uy2):
                        collision = True
                        break
                if not collision:
                    break
                ly += label_img.height + 4
                offset_attempts += 1

            used_labels.append((ly, ly + label_img.height))

            draw.rectangle(
                [lx - 3, ly - 2,
                 lx + label_img.width + 3, ly + label_img.height + 2],
                fill=(0, 0, 0, 200)
            )
            img.alpha_composite(label_img, (lx, ly))

    def _draw_sl_tp_lines(self, img, draw, position, to_y, current,
                          chart_x1, chart_x2, min_p, max_p):
        try:
            if position.direction == "LONG":
                if position.stop_loss_pct:
                    sl_price = position.entry_price * (1 - (position.stop_loss_pct * position.margin) / (position.size * 100))
                else:
                    sl_price = None
                if position.take_profit_pct:
                    tp_price = position.entry_price * (1 + (position.take_profit_pct * position.margin) / (position.size * 100))
                else:
                    tp_price = None
            else:
                if position.stop_loss_pct:
                    sl_price = position.entry_price * (1 + (position.stop_loss_pct * position.margin) / (position.size * 100))
                else:
                    sl_price = None
                if position.take_profit_pct:
                    tp_price = position.entry_price * (1 - (position.take_profit_pct * position.margin) / (position.size * 100))
                else:
                    tp_price = None

            if sl_price and min_p <= sl_price <= max_p:
                y = to_y(sl_price)
                for x in range(int(chart_x1), int(chart_x2), 4):
                    draw.point((x, y), fill=self.COLORS["sl"])
                    draw.point((x, y + 1), fill=self.COLORS["sl"])
                lbl = self._text(f"SL {sl_price:,.2f}", 10, self.COLORS["sl"])
                if lbl:
                    img.alpha_composite(lbl, (int(chart_x2) - lbl.width - 20, y - 12))

            if tp_price and min_p <= tp_price <= max_p:
                y = to_y(tp_price)
                for x in range(int(chart_x1), int(chart_x2), 4):
                    draw.point((x, y), fill=self.COLORS["tp"])
                    draw.point((x, y + 1), fill=self.COLORS["tp"])
                lbl = self._text(f"TP {tp_price:,.2f}", 10, self.COLORS["tp"])
                if lbl:
                    img.alpha_composite(lbl, (int(chart_x2) - lbl.width - 20, y + 2))
        except Exception as e:
            logger.error(f"[CFD] SL/TP draw error: {e}")

    def generate(self, symbol, name, quote, candles, output_path,
                 positions=None, currency="USD"):
        img = Image.new("RGBA", (self.WIDTH, self.HEIGHT), self.COLORS["bg"])
        draw = ImageDraw.Draw(img)

        draw.rectangle([1, 1, self.WIDTH - 2, self.HEIGHT - 2],
                       outline=self.COLORS["border"], width=2)

        y = 20
        sym_img = self._text(symbol, 32, self.COLORS["text"])
        if sym_img:
            img.alpha_composite(sym_img, (self.PADDING, int(y)))

        name_img = self._text(name[:50], 16, self.COLORS["muted"])
        if name_img:
            img.alpha_composite(name_img, (self.PADDING, int(y + 40)))

        current = quote.get("c", 0)
        change = quote.get("d", 0) or 0
        change_pct = quote.get("dp", 0) or 0
        color = self.COLORS["green"] if change_pct >= 0 else self.COLORS["red"]

        price_img = self._text(f"{current:,.2f} {currency}", 32, self.COLORS["text"])
        if price_img:
            img.alpha_composite(price_img, (int(self.WIDTH - self.PADDING - price_img.width),
                                            int(y - 5)))

        change_text = f"{change:+,.2f} ({change_pct:+.2f}%)"
        change_img = self._text(change_text, 18, color)
        if change_img:
            img.alpha_composite(change_img, (int(self.WIDTH - self.PADDING - change_img.width),
                                             int(y + 45)))

        draw.line([(self.PADDING, self.HEADER_H),
                   (self.WIDTH - self.PADDING, self.HEADER_H)],
                  fill=self.COLORS["border"], width=1)

        stats_y = self.HEADER_H + 15
        stats = [
            ("OPEN", quote.get("o", 0)),
            ("HIGH", quote.get("h", 0)),
            ("LOW", quote.get("l", 0)),
            ("PREV CLOSE", quote.get("pc", 0)),
        ]

        col_w = (self.WIDTH - 2 * self.PADDING) // 4
        for i, (label, value) in enumerate(stats):
            x = self.PADDING + i * col_w
            lbl = self._text(label, 12, self.COLORS["muted"])
            if lbl:
                img.alpha_composite(lbl, (int(x), int(stats_y)))
            val = self._text(f"{value:,.2f}", 18, self.COLORS["text"])
            if val:
                img.alpha_composite(val, (int(x), int(stats_y + 20)))

        chart_top = self.HEADER_H + self.STATS_H

        # --- Positions summary (below stats, above chart divider) ---
        if positions:
            relevant = [p for p in positions if p.symbol == symbol]
            if relevant:
                total_margin = sum(p.margin for p in relevant)
                total_pnl = sum(p.current_pnl(current) for p in relevant)

                pnl_color = self.COLORS["green"] if total_pnl >= 0 else self.COLORS["red"]
                summary_text = (
                    f"POS: {len(relevant)} | "
                    f"MARGIN: {total_margin:,.0f} | "
                    f"P&L: {total_pnl:+,.2f}"
                )
                summary_img = self._text(summary_text, 16, pnl_color)
                if summary_img:
                    sx = int((self.WIDTH - summary_img.width) // 2)
                    sy = int(chart_top - summary_img.height - 8)
                    draw.rectangle(
                        [sx - 8, sy - 3,
                         sx + summary_img.width + 8, sy + summary_img.height + 3],
                        fill=(0, 0, 0, 180)
                    )
                    img.alpha_composite(summary_img, (sx, sy))

        draw.line([(self.PADDING, chart_top),
                   (self.WIDTH - self.PADDING, chart_top)],
                  fill=self.COLORS["border"], width=1)

        chart_x1 = self.PADDING + 10
        chart_x2 = self.WIDTH - self.PADDING - 10
        chart_y1 = chart_top + self.CHART_TOP_MARGIN
        chart_y2 = self.HEIGHT - self.PADDING - 20

        draw.rectangle([chart_x1, chart_y1, chart_x2, chart_y2],
                       fill=self.COLORS["panel"], outline=self.COLORS["border"], width=1)

        candles_to_draw = list(candles)

        if not candles_to_draw:
            o = quote.get("o", current)
            h = quote.get("h", current)
            l = quote.get("l", current)
            c = quote.get("c", current)
            if all(p and p > 0 for p in [o, h, l, c]):
                candles_to_draw = [{
                    "open": o, "high": h, "low": l, "close": c,
                    "start": time.time(), "interpolated": False,
                }]

        if not candles_to_draw:
            msg = self._text("No chart data", 20, self.COLORS["muted"])
            if msg:
                img.alpha_composite(msg, ((self.WIDTH - msg.width) // 2,
                                          int((chart_y1 + chart_y2) // 2 - msg.height // 2)))
        else:
            all_prices = []
            for c in candles_to_draw:
                all_prices.extend([c["high"], c["low"]])
            all_prices.extend([quote.get("h", 0), quote.get("l", 0),
                               quote.get("o", 0), quote.get("pc", 0)])
            if positions:
                for p in positions:
                    if p.symbol == symbol:
                        all_prices.append(p.entry_price)
            all_prices = [p for p in all_prices if p and p > 0]
            if not all_prices:
                all_prices = [current]

            min_p = min(all_prices)
            max_p = max(all_prices)
            if max_p == min_p:
                max_p = min_p + 1
            span = max_p - min_p
            min_span = current * 0.003
            if span < min_span:
                center = (max_p + min_p) / 2
                min_p = center - min_span / 2
                max_p = center + min_span / 2
                span = min_span
            min_p -= span * 0.05
            max_p += span * 0.05

            to_y = self._to_y_factory(min_p, max_p, chart_y1, chart_y2)

            for i in range(5):
                gy = chart_y1 + i * (chart_y2 - chart_y1) // 4
                draw.line([(chart_x1, gy), (chart_x2, gy)],
                          fill=self.COLORS["grid"], width=1)
                price_label = max_p - (max_p - min_p) * i / 4
                lbl = self._text(f"{price_label:,.2f}", 11, self.COLORS["muted"])
                if lbl:
                    img.alpha_composite(lbl, (int(chart_x2 + 2),
                                              int(gy - lbl.height // 2)))

            pc = candles_to_draw[-1]["close"] if candles_to_draw else quote.get("pc", 0)
            if pc and min_p <= pc <= max_p:
                py = to_y(pc)
                for xx in range(int(chart_x1), int(chart_x2), 6):
                    draw.line([(xx, py), (xx + 3, py)],
                              fill=self.COLORS["gold"], width=1)

            self._draw_candles(img, draw, candles_to_draw,
                               chart_x1, chart_x2, chart_y1, chart_y2, min_p, max_p)

            if positions:
                relevant = [p for p in positions if p.symbol == symbol]
                if relevant:
                    self._draw_entry_lines(img, draw, relevant, current,
                                           chart_x1, chart_x2, chart_y1, chart_y2,
                                           min_p, max_p)

        time_label = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())
        tl = self._text(time_label, 11, self.COLORS["muted"])
        if tl:
            img.alpha_composite(tl, (self.PADDING, int(self.HEIGHT - 20)))

        lev_text = f"CFD x{LEVERAGE} | Commission {COMMISSION_PCT*100:.2f}%"
        lev_img = self._text(lev_text, 11, self.COLORS["muted"])
        if lev_img:
            img.alpha_composite(lev_img,
                (int(self.WIDTH - self.PADDING - lev_img.width),
                 int(self.HEIGHT - 20)))

        img.convert("RGB").save(output_path, format="PNG", optimize=True)
        return output_path


# ============================================================
# PLUGIN
# ============================================================

class CFDPlugin(BaseGamePlugin):
    def __init__(self):
        logger.info("[CFD] Initializing CFDPlugin")
        super().__init__(game_name="cfd")

        self.yahoo = YahooClient()
        self.SETTING_KEY = "cfd_positions"

        self.chart_gen = ChartGenerator(self.text_renderer)
        self.table_gen = TableGenerator(self.text_renderer)

    # ---------- SYMBOLS ----------

    def _find_symbol(self, raw):
        if not raw:
            return None, None, None, None
        key = raw.strip().upper()
        if key in POPULAR_SYMBOLS:
            name, exch, cat = POPULAR_SYMBOLS[key]
            return key, name, exch, cat
        matches = self._search(raw)
        if matches:
            sym, name, exch, cat = matches[0]
            return sym, name, exch, cat
        return key, key, "?", "yahoo"

    def _search(self, query):
        q = query.lower().strip()
        if not q:
            return []
        matches = []
        for sym, (name, exch, cat) in POPULAR_SYMBOLS.items():
            if q in sym.lower() or q in name.lower():
                matches.append((sym, name, exch, cat))
        matches.sort(key=lambda x: (CATEGORY_ORDER.get(x[3], 99), x[0]))
        return matches

    def _search_with_yahoo(self, query):
        if not query:
            return []
        return self.yahoo.search_symbols(query, max_results=20)

    def _filter_by_category(self, category):
        return {sym: data for sym, data in POPULAR_SYMBOLS.items()
                if data[2] == category}

    # ---------- POSITION PERSISTENCE ----------

    def _load_positions(self):
        if not self.cache:
            return {}
        data = self.cache.get_setting(self.SETTING_KEY, {})
        return data if isinstance(data, dict) else {}

    def _save_positions(self, positions):
        if not self.cache:
            return
        self.cache.set_setting(self.SETTING_KEY, positions)

    def _get_user_positions(self, user_id):
        all_pos = self._load_positions()
        raw = all_pos.get(str(user_id), [])
        result = []
        for p in raw:
            if isinstance(p, CFDPosition):
                result.append(p)
            elif isinstance(p, dict):
                try:
                    result.append(CFDPosition.from_dict(p))
                except Exception as e:
                    logger.error(f"[CFD] Position deserialize error: {e}")
        return result

    def _set_user_positions(self, user_id, positions):
        all_pos = self._load_positions()
        all_pos[str(user_id)] = [
            p.to_dict() if isinstance(p, CFDPosition) else p for p in positions
        ]
        self._save_positions(all_pos)

    def _get_positions_for_symbol(self, user_id, symbol):
        return [p for p in self._get_user_positions(user_id) if p.symbol == symbol]

    # ---------- AUTO CLOSE ----------

    def _check_auto_close(self, user_id, sender, file_queue, user, balance):
        positions = self._get_user_positions(user_id)
        if not positions:
            return balance

        closed = []
        remaining = []
        total_returned = 0

        for pos in positions:
            current_price = self.yahoo.get_price(pos.symbol)
            if not current_price:
                remaining.append(pos)
                continue

            pnl = pos.current_pnl(current_price)
            reason = None

            if pnl <= -pos.margin:
                reason = "STOP OUT"
            elif pos.stop_loss_pct and pnl <= -(pos.margin * pos.stop_loss_pct / 100.0):
                reason = f"STOP LOSS ({pos.stop_loss_pct}%)"
            elif pos.take_profit_pct and pnl >= (pos.margin * pos.take_profit_pct / 100.0):
                reason = f"TAKE PROFIT ({pos.take_profit_pct}%)"

            if reason:
                returned = pos.margin + pnl
                if returned < 0:
                    returned = 0
                returned = round(returned)
                total_returned += returned
                closed.append((pos, current_price, pnl, returned, reason))
            else:
                remaining.append(pos)

        if not closed:
            return balance

        self._set_user_positions(user_id, remaining)

        if total_returned > 0:
            new_balance = balance + total_returned
            self.update_user_balance(user_id, new_balance)
        else:
            new_balance = balance

        lines = ["Auto-closed positions:", ""]
        total_pnl = 0
        for pos, price, pnl, returned, reason in closed:
            total_pnl += pnl
            lines.append(
                f"{pos.symbol} {pos.direction} | "
                f"entry {pos.entry_price:,.2f} -> {price:,.2f} | "
                f"P&L {pnl:+,.2f} | {reason}"
            )

        lines.append("")
        lines.append(f"Total P&L: {total_pnl:+,.2f}")
        lines.append(f"Returned: {total_returned:,.0f}")
        lines.append(f"New balance: {new_balance:,.0f}")

        self.send_message_image(
            sender, file_queue, "\n".join(lines),
            "CFD - Auto Close", self.cache, user_id
        )

        try:
            self.cache.add_experience(user_id, int(total_pnl), sender, file_queue)
        except Exception as e:
            logger.error(f"[CFD] add_experience error: {e}")

        return new_balance

    # ---------- IMAGE HELPERS ----------

    def _add_transparent_margin(self, image_path, margin=OVERLAY_MARGIN):
        try:
            img = Image.open(image_path).convert("RGBA")
            new_w = img.width + margin * 2
            new_h = img.height + margin * 2
            canvas = Image.new("RGBA", (new_w, new_h), (0, 0, 0, 0))
            canvas.paste(img, (margin, margin), img)
            canvas.save(image_path, format="PNG", optimize=True)
            return True
        except Exception as e:
            logger.error(f"[CFD] Margin wrap error: {e}")
            return False

    # ---------- IMAGE GENERATION ----------

    def _send_chart(self, user_id, sender, symbol, name, quote, candles,
                    file_queue, user, balance, currency="USD", positions=None):
        try:
            img_path = os.path.join(
                self.results_folder,
                f"cfd_chart_{user_id}_{int(time.time())}.png"
            )
            self.chart_gen.generate(
                symbol, name, quote, candles, img_path,
                positions=positions, currency=currency
            )

            self._add_transparent_margin(img_path)

            if positions:
                relevant = [p for p in positions if p.symbol == symbol]
                bet = int(sum(p.margin for p in relevant)) if relevant else 0
                win = int(sum(p.current_pnl(quote.get("c", 0)) for p in relevant)) if relevant else 0
            else:
                bet = 0
                win = 0

            overlay_path, error = self.apply_user_overlay(
                img_path, user_id, sender, bet, win, balance, user,
                show_win_text=False,
                show_bet_amount=False,
                font_scale=OVERLAY_FONT_SCALE,
                avatar_size=OVERLAY_AVATAR_SIZE,
                win_text_height=-1
            )
            if overlay_path:
                file_queue.put(overlay_path)
            else:
                logger.warning(f"[CFD] Overlay failed for chart: {error}")
                file_queue.put(img_path)
            return True
        except Exception as e:
            logger.error(f"[CFD] Chart generation error: {e}")
            return False

    def _send_table(self, user_id, sender, user, balance, title, columns, rows,
                    file_queue, col_align=None, col_colors=None, footer=None):
        try:
            img_path = os.path.join(
                self.results_folder,
                f"cfd_table_{user_id}_{int(time.time())}.png"
            )
            self.table_gen.generate(
                title, columns, rows, img_path,
                col_align=col_align, col_colors=col_colors, footer=footer
            )

            self._add_transparent_margin(img_path)

            overlay_path, error = self.apply_user_overlay(
                img_path, user_id, sender, 0, 0, balance, user,
                show_win_text=False,
                show_bet_amount=False,
                font_scale=OVERLAY_FONT_SCALE,
                avatar_size=OVERLAY_AVATAR_SIZE,
                win_text_height=-1
            )
            if overlay_path:
                file_queue.put(overlay_path)
            else:
                logger.warning(f"[CFD] Overlay failed for table: {error}")
                file_queue.put(img_path)
            return True
        except Exception as e:
            logger.error(f"[CFD] Table generation error: {e}")
            return False

    def _send_paginated_list(self, user_id, sender, user, balance,
                              symbols_dict, category, page, file_queue,
                              title_prefix):
        try:
            all_items = sorted(
                symbols_dict.items(),
                key=lambda x: (CATEGORY_ORDER.get(x[1][2], 99), x[0])
            )
            total = len(all_items)
            total_pages = max(1, (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
            page = max(1, min(page, total_pages))

            start = (page - 1) * ITEMS_PER_PAGE
            end = start + ITEMS_PER_PAGE
            page_items = all_items[start:end]

            columns = ["SYMBOL", "NAME"]
            rows = []
            for sym, (name, exch, cat) in page_items:
                short_name = name if len(name) <= 40 else name[:37] + "..."
                rows.append([sym, short_name])

            title = f"{title_prefix} ({total} symbols, page {page}/{total_pages})"

            cat_short = CATEGORY_SHORT.get(category, "us")
            if total_pages > 1:
                next_page = page + 1 if page < total_pages else 1
                prev_page = page - 1 if page > 1 else total_pages
                footer = (f"Next: /cfd list {cat_short} {next_page} | "
                          f"Prev: /cfd list {cat_short} {prev_page}")
            else:
                footer = "Use /cfd price <SYMBOL> for chart"

            self._send_table(
                user_id, sender, user, balance, title, columns, rows,
                file_queue, col_align=["left", "left"], footer=footer
            )
            return True
        except Exception as e:
            logger.error(f"[CFD] Paginated list error: {e}")
            return False

    def _send_search_results(self, user_id, sender, user, balance,
                             local_matches, yahoo_matches, query, page, file_queue):
        try:
            seen_syms = set()
            combined = []

            for sym, name, exch, cat in local_matches:
                if sym in seen_syms:
                    continue
                seen_syms.add(sym)
                combined.append((sym, name, exch, cat))

            for sym, name, exch, cat in yahoo_matches:
                if sym in seen_syms:
                    continue
                seen_syms.add(sym)
                combined.append((sym, name, exch, cat))

            total = len(combined)
            total_pages = max(1, (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
            page = max(1, min(page, total_pages))

            start = (page - 1) * ITEMS_PER_PAGE
            end = start + ITEMS_PER_PAGE
            page_items = combined[start:end]

            columns = ["SYMBOL", "NAME"]
            rows = []
            for sym, name, exch, cat in page_items:
                short_name = name if len(name) <= 45 else name[:42] + "..."
                rows.append([sym, short_name])

            title = f"Search: '{query}' ({total} results, page {page}/{total_pages})"

            if total_pages > 1:
                next_page = page + 1 if page < total_pages else 1
                footer = f"Next: /cfd search {query} {next_page}"
            else:
                footer = "Use /cfd price <SYMBOL> for chart"

            self._send_table(
                user_id, sender, user, balance, title, columns, rows,
                file_queue, col_align=["left", "left"], footer=footer
            )
            return True
        except Exception as e:
            logger.error(f"[CFD] Search list error: {e}")
            return False

    def _send_positions(self, user_id, sender, user, balance, positions, file_queue):
        try:
            columns = ["SYMBOL", "DIR", "ENTRY", "NOW", "MARGIN", "P&L", "SL/TP"]
            rows = []
            col_colors = {}
            total_pnl = 0
            total_margin = 0

            for r_idx, pos in enumerate(positions):
                quote = self.yahoo.get_quote(pos.symbol)
                if not quote:
                    rows.append([pos.symbol, pos.direction, "-", "-",
                                 f"{pos.margin:,.2f}", "-", "-"])
                    continue

                current = quote.get("c", 0)
                pnl = pos.current_pnl(current)
                total_pnl += pnl
                total_margin += pos.margin

                dir_color = (self.table_gen.COLORS["green"] if pos.direction == "LONG"
                             else self.table_gen.COLORS["red"])
                pnl_color = self.table_gen.COLORS["green"] if pnl >= 0 else self.table_gen.COLORS["red"]
                col_colors[r_idx] = {1: dir_color, 5: pnl_color}

                sl_tp = []
                if pos.stop_loss_pct:
                    sl_tp.append(f"SL{pos.stop_loss_pct}")
                if pos.take_profit_pct:
                    sl_tp.append(f"TP{pos.take_profit_pct}")
                sl_tp_str = " ".join(sl_tp) if sl_tp else "-"

                rows.append([
                    pos.symbol,
                    pos.direction,
                    f"{pos.entry_price:,.2f}",
                    f"{current:,.2f}",
                    f"{pos.margin:,.2f}",
                    f"{pnl:+,.2f}",
                    sl_tp_str,
                ])

            title = "Your open CFD positions"
            footer = f"Total margin: {total_margin:,.2f} | Total P&L: {total_pnl:+,.2f}"

            self._send_table(
                user_id, sender, user, balance, title, columns, rows,
                file_queue,
                col_align=["left", "center", "right", "right", "right", "right", "center"],
                col_colors=col_colors,
                footer=footer
            )
            return True
        except Exception as e:
            logger.error(f"[CFD] Positions generation error: {e}")
            return False

    # ---------- MAIN ----------

    def execute_game(self, command_name, args, file_queue, cache=None,
                     sender=None, avatar_url=None):
        self.cache = cache

        user_id, user, error = self.validate_user(cache, sender, avatar_url)
        if error:
            self.send_message_image(sender, file_queue, error, "CFD - Error", cache, user_id)
            return ""

        balance = user.get("balance", 0)

        if not args:
            self._send_help(sender, file_queue, user_id)
            return ""

        raw_cmd = args[0].lower()
        cmd = COMMAND_ALIASES.get(raw_cmd, raw_cmd)

        if cmd not in ("help",):
            balance = self._check_auto_close(user_id, sender, file_queue, user, balance)
            user["balance"] = balance

        # ---------- LIST ----------
        if cmd == "list":
            category = None
            page = 1
            is_all = False

            if len(args) >= 2:
                arg1 = args[1].lower()
                if arg1 == "all":
                    is_all = True
                    if len(args) >= 3:
                        try:
                            page = int(args[2])
                        except ValueError:
                            page = 1
                elif arg1 in CATEGORY_INPUT_MAP:
                    category = CATEGORY_INPUT_MAP[arg1]
                    if len(args) >= 3:
                        try:
                            page = int(args[2])
                        except ValueError:
                            page = 1
                else:
                    try:
                        page = int(arg1)
                    except ValueError:
                        pass

            if is_all:
                self._send_paginated_list(
                    user_id, sender, user, balance,
                    POPULAR_SYMBOLS, "all", page, file_queue,
                    "All CFD instruments"
                )
                return ""

            if category is None:
                counts = {cat: 0 for cat in CATEGORY_NAMES}
                for _, (_, _, cat) in POPULAR_SYMBOLS.items():
                    if cat in counts:
                        counts[cat] += 1

                menu_text = (
                    "Popular CFD instruments\n\n"
                    "Choose a category:\n"
                    f"/cfd list us - US stocks ({counts.get('stock_us', 0)})\n"
                    f"/cfd list pl - Polish stocks GPW ({counts.get('stock_pl', 0)})\n"
                    f"/cfd list com - Commodities ({counts.get('commodity', 0)})\n"
                    f"/cfd list crypto - Crypto ({counts.get('crypto', 0)})\n"
                    f"/cfd list all - All instruments ({len(POPULAR_SYMBOLS)})\n\n"
                    "Or search: /cfd search <text>\n"
                    "(search also queries Yahoo Finance for global symbols)"
                )
                self.send_message_image(sender, file_queue, menu_text,
                                        "CFD - Instruments", cache, user_id)
                return ""

            filtered = self._filter_by_category(category)
            cat_title = CATEGORY_NAMES.get(category, "Instruments")
            self._send_paginated_list(
                user_id, sender, user, balance,
                filtered, category, page, file_queue, cat_title
            )
            return ""

        # ---------- SEARCH ----------
        if cmd == "search":
            if len(args) < 2:
                self.send_message_image(sender, file_queue,
                    "Usage: /cfd search <text>\nExample: /cfd search wawel",
                    "CFD - Search", cache, user_id)
                return ""

            query_parts = args[1:]
            page = 1
            if len(query_parts) >= 2:
                try:
                    page = int(query_parts[-1])
                    query_parts = query_parts[:-1]
                except ValueError:
                    pass

            query = " ".join(query_parts)

            local_matches = self._search(query)
            yahoo_matches = self._search_with_yahoo(query)

            if not local_matches and not yahoo_matches:
                self.send_message_image(sender, file_queue,
                    f"No results for: {query}\n"
                    "Tip: try exact ticker (e.g. WWL.WA, AAPL)",
                    "CFD - Search", cache, user_id)
                return ""

            self._send_search_results(
                user_id, sender, user, balance,
                local_matches, yahoo_matches, query, page, file_queue
            )
            return ""

        # ---------- PRICE / CHART ----------
        if cmd == "price":
            if len(args) < 2:
                self.send_message_image(sender, file_queue,
                    "Usage: /cfd price <SYMBOL>\nExample: /cfd price AAPL",
                    "CFD - Price", cache, user_id)
                return ""

            symbol, name, exch, cat = self._find_symbol(args[1])
            if not symbol:
                self.send_message_image(sender, file_queue,
                    f"Symbol not found: {args[1]}",
                    "CFD - Error", cache, user_id)
                return ""

            quote = self.yahoo.get_quote(symbol)
            if not quote:
                self.send_message_image(sender, file_queue,
                    f"Could not fetch price for {symbol}.\n"
                    "Make sure the ticker is correct (e.g. WWL.WA, AAPL, GC=F).",
                    "CFD - API Error", cache, user_id)
                return ""

            candles = self.yahoo.get_candles(symbol, range_=CHART_RANGE, interval=CHART_INTERVAL)
            display_name = quote.get("name") or name
            currency = quote.get("currency", "USD")
            positions = self._get_positions_for_symbol(user_id, symbol)

            self._send_chart(
                user_id, sender, symbol, display_name, quote, candles,
                file_queue, user, balance, currency=currency, positions=positions
            )
            return ""

        # ---------- LONG / SHORT ----------
        if cmd in ("long", "short"):
            direction = cmd.upper()
            if len(args) < 3:
                self.send_message_image(sender, file_queue,
                    f"Usage: /cfd {cmd} <SYMBOL> <MARGIN> [sl <pct>] [tp <pct>]\n"
                    f"Example: /cfd {cmd} AAPL 100 sl 30 tp 60",
                    "CFD - Open Position", cache, user_id)
                return ""

            raw_sym = args[1]
            try:
                margin = int(args[2])
            except ValueError:
                self.send_message_image(sender, file_queue, "Margin must be a number.", "CFD - Error", cache, user_id)
                return ""

            stop_loss_pct = None
            take_profit_pct = None
            i = 3
            while i < len(args):
                key = args[i].lower()
                if key in ("sl", "slp") and i + 1 < len(args):
                    try:
                        stop_loss_pct = int(args[i + 1])
                        if not (1 <= stop_loss_pct <= 99):
                            self.send_message_image(sender, file_queue,
                                "Stop loss must be between 1 and 99 (percent of margin).",
                                "CFD - Error", cache, user_id)
                            return ""
                    except ValueError:
                        self.send_message_image(sender, file_queue,
                            "Stop loss must be a number.", "CFD - Error", cache, user_id)
                        return ""
                    i += 2
                elif key in ("tp", "tpp") and i + 1 < len(args):
                    try:
                        take_profit_pct = int(args[i + 1])
                        if not (1 <= take_profit_pct <= 1000):
                            self.send_message_image(sender, file_queue,
                                "Take profit must be between 1 and 1000 (percent of margin).",
                                "CFD - Error", cache, user_id)
                            return ""
                    except ValueError:
                        self.send_message_image(sender, file_queue,
                            "Take profit must be a number.", "CFD - Error", cache, user_id)
                        return ""
                    i += 2
                else:
                    self.send_message_image(sender, file_queue,
                        f"Unknown argument: {args[i]}\n"
                        "Usage: /cfd long|short <SYMBOL> <MARGIN> [sl <pct>] [tp <pct>]",
                        "CFD - Error", cache, user_id)
                    return ""

            symbol, name, exch, cat = self._find_symbol(raw_sym)
            if not symbol:
                self.send_message_image(sender, file_queue,
                    f"Symbol not found: {raw_sym}",
                    "CFD - Error", cache, user_id)
                return ""

            if margin < MIN_MARGIN:
                self.send_message_image(sender, file_queue,
                    f"Minimum margin: ${MIN_MARGIN}",
                    "CFD - Error", cache, user_id)
                return ""
            if margin > MAX_MARGIN:
                self.send_message_image(sender, file_queue,
                    f"Maximum margin: ${MAX_MARGIN}",
                    "CFD - Error", cache, user_id)
                return ""
            if margin > balance:
                self.send_message_image(sender, file_queue,
                    f"Insufficient funds. Margin: ${margin}, balance: ${balance}",
                    "CFD - Insufficient Funds", cache, user_id)
                return ""

            user_positions = self._get_user_positions(user_id)
            if len(user_positions) >= MAX_OPEN_POSITIONS:
                self.send_message_image(sender, file_queue,
                    f"You already have {MAX_OPEN_POSITIONS} open positions.",
                    "CFD - Position Limit", cache, user_id)
                return ""

            quote = self.yahoo.get_quote(symbol)
            if not quote:
                self.send_message_image(sender, file_queue,
                    f"Could not fetch price for {symbol}.",
                    "CFD - API Error", cache, user_id)
                return ""
            entry_price = quote.get("c")

            new_balance = balance - margin
            self.update_user_balance(user_id, new_balance)
            user["balance"] = new_balance

            position = CFDPosition(
                user_id, symbol, direction, margin, entry_price,
                stop_loss_pct=stop_loss_pct,
                take_profit_pct=take_profit_pct
            )
            user_positions.append(position)
            self._set_user_positions(user_id, user_positions)

            logger.info(
                f"[CFD] {sender} opened {direction} {symbol} margin={margin} @ {entry_price}"
                f" sl={stop_loss_pct} tp={take_profit_pct}"
            )

            candles = self.yahoo.get_candles(symbol, range_=CHART_RANGE, interval=CHART_INTERVAL)
            display_name = quote.get("name") or name
            currency = quote.get("currency", "USD")
            positions = self._get_positions_for_symbol(user_id, symbol)

            self._send_chart(
                user_id, sender, symbol, display_name, quote, candles,
                file_queue, user, new_balance, currency=currency, positions=positions
            )
            return ""

        # ---------- CLOSE ----------
        if cmd == "close":
            user_positions = self._get_user_positions(user_id)
            if not user_positions:
                self.send_message_image(sender, file_queue,
                    "You have no open positions.", "CFD - No Positions", cache, user_id)
                return ""

            if len(args) < 2:
                self.send_message_image(sender, file_queue,
                    "Usage: /cfd close <SYMBOL> or /cfd close all",
                    "CFD - Close", cache, user_id)
                return ""

            target = args[1].upper()
            if target == "ALL":
                to_close = user_positions
                remaining = []
            else:
                sym_match, _, _, _ = self._find_symbol(args[1])
                lookup = sym_match if sym_match else target
                to_close = [p for p in user_positions if p.symbol == lookup]
                remaining = [p for p in user_positions if p.symbol != lookup]

            if not to_close:
                self.send_message_image(sender, file_queue,
                    f"You have no open position on {target}.",
                    "CFD - No Positions", cache, user_id)
                return ""

            total_return = 0
            lines = ["Closed positions:", ""]

            for pos in to_close:
                current_price = self.yahoo.get_price(pos.symbol)
                if not current_price:
                    remaining.append(pos)
                    continue

                pnl = pos.current_pnl(current_price)
                returned = pos.margin + pnl
                if returned < 0:
                    returned = 0
                total_return += returned

                lines.append(
                    f"{pos.symbol} {pos.direction} | "
                    f"entry {pos.entry_price:,.2f} -> "
                    f"{current_price:,.2f} | "
                    f"P&L {pnl:+,.2f}"
                )

            total_return = round(total_return)

            if total_return > 0:
                new_balance = balance + total_return
                self.update_user_balance(user_id, new_balance)
                net_profit = total_return - sum(p.margin for p in to_close)
                try:
                    self.cache.add_experience(user_id, int(net_profit), sender, file_queue)
                except Exception as e:
                    logger.error(f"[CFD] add_experience error: {e}")
            else:
                new_balance = balance

            self._set_user_positions(user_id, remaining)

            lines.append("")
            lines.append(f"Returned: {total_return:,.0f}")
            lines.append(f"New balance: {new_balance:,.0f}")

            self.send_message_image(sender, file_queue, "\n".join(lines),
                                    "CFD - Close", cache, user_id)
            return ""

        # ---------- POSITIONS ----------
        if cmd == "positions":
            user_positions = self._get_user_positions(user_id)
            if not user_positions:
                self.send_message_image(sender, file_queue,
                    "You have no open positions.\nOpen one: /cfd long AAPL 100",
                    "CFD - No Positions", cache, user_id)
                return ""

            self._send_positions(user_id, sender, user, balance, user_positions, file_queue)
            return ""

        # ---------- HELP ----------
        if cmd == "help":
            self._send_help(sender, file_queue, user_id)
            return ""

        self._send_help(sender, file_queue, user_id)
        return ""

    def _send_help(self, sender, file_queue, user_id):
        help_text = (
            "CFD Trading - Global stocks, commodities, crypto\n\n"
            "Commands:\n"
            "/cfd list - category menu\n"
            "/cfd list us|pl|com|crypto|all [page] - browse category\n"
            "/cfd search <text> [page] - search symbols (local + Yahoo)\n"
            "/cfd price <SYMBOL> - chart and price\n"
            "/cfd long <SYMBOL> <MARGIN> [sl <pct>] [tp <pct>] - open long\n"
            "/cfd short <SYMBOL> <MARGIN> [sl <pct>] [tp <pct>] - open short\n"
            "/cfd positions - your open positions\n"
            "/cfd close <SYMBOL> - close a position\n"
            "/cfd close all - close all positions\n\n"
            "Optional parameters:\n"
            "  sl <pct> - stop loss, percent of margin (1-99)\n"
            "  tp <pct> - take profit, percent of margin (1-1000)\n\n"
            "Examples:\n"
            "  /cfd price AAPL\n"
            "  /cfd price WWL.WA\n"
            "  /cfd price GC=F\n"
            "  /cfd long BTC-USD 200 sl 20 tp 100\n\n"
            "Search tips:\n"
            "  Local list covers 120 popular symbols\n"
            "  For other symbols (e.g. GPW stocks), use exact ticker:\n"
            "  WWL.WA (Wawel), KTY.WA (Kety), 0K6.F (Frankfurt)\n\n"
            f"Leverage: x{LEVERAGE}\n"
            f"Commission: {COMMISSION_PCT*100:.2f}%\n"
            f"Min margin: ${MIN_MARGIN}\n"
            f"Max positions: {MAX_OPEN_POSITIONS}\n\n"
            "Virtual simulation. Not real investment advice."
        )
        self.send_message_image(sender, file_queue, help_text, "CFD - Help", self.cache, user_id)


def register():
    logger.info("[CFD] Registering CFD plugin")
    plugin = CFDPlugin()
    return {
        "name": "cfd",
        "aliases": ["/cfd"],
        "description": (
            "CFD Trading - Global stocks, commodities, crypto\n\n"
            "Commands:\n"
            "- /cfd list - category menu\n"
            "- /cfd list us|pl|com|crypto|all [page] - browse\n"
            "- /cfd search <text> [page] - search\n"
            "- /cfd price <SYMBOL> - chart and price\n"
            "- /cfd long <SYMBOL> <MARGIN> [sl <pct>] [tp <pct>] - open long\n"
            "- /cfd short <SYMBOL> <MARGIN> [sl <pct>] [tp <pct>] - open short\n"
            "- /cfd positions - open positions\n"
            "- /cfd close <SYMBOL> - close position\n"
            "- /cfd close all - close all\n\n"
            f"Leverage x{LEVERAGE}, commission {COMMISSION_PCT*100:.2f}%\n"
        ),
        "execute": plugin.execute_game,
    }