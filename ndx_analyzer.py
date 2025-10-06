import pandas as pd
import numpy as np
import yfinance as yf
import requests
import json
from datetime import datetime

# Telegram Bot ayarları
TELEGRAM_TOKEN = "8256592463:AAHlJ3BQSvwUDOQuKCYAhKwAwMMWUFJXE4o"
CHAT_ID = "1008660822"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

# NDX 100 sembol listesi (yfinance formatında: .IS uzantılı)
SYMBOLS = [ "AAPL", "ABNB", "ADBE", "ADI", "ADP", "ADSK", "AEP", "AMAT", "AMD", "AMGN", "AMZN", "APP", "ARM", "ASML", "AVGO", "AXON", "AZN", "BIIB", "BKNG", "BKR", "CCEP", "CDNS", "CDW", "CEG", "CHTR", "CMCSA", "COST", "CPRT", "CRWD", "CSCO", "CSGP", "CSX", "CTAS", "CTSH", "DASH", "DDOG", "DXCM", "EA", "EXC", "FANG", "FAST", "FTNT", "GEHC", "GFS", "GILD", "GOOG", "GOOGL", "HON", "IDXX", "INTC", "INTU", "ISRG", "KDP", "KHC", "KLAC", "LIN", "LRCX", "LULU", "MAR", "MCHP", "MDLZ", "MELI", "META", "MNST", "MRVL", "MSFT", "MSTR", "MU", "NFLX", "NVDA", "NXPI", "ODFL", "ON", "ORLY", "PANW", "PAYX", "PCAR", "PDD", "PEP", "PLTR", "PYPL", "QCOM", "REGN", "ROP", "ROST", "SBUX", "SHOP", "SNPS", "TEAM", "TMUS", "TRI", "TSLA", "TTD", "TTWO", "TXN", "VRSK", "VRTX", "WBD", "WDAY", "XEL", "ZS" ]


def calculate_rsi(data, periods=31):
    """RSI hesaplama fonksiyonu"""
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def send_telegram_message(message):
    """Telegram mesaj gönderme fonksiyonu"""
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(TELEGRAM_API_URL, json=payload, timeout=10)
        if response.status_code == 200:
            print("✅ Telegram mesajı başarıyla gönderildi")
        else:
            print(f"⚠️ Telegram mesajı gönderilemedi: {response.text}")
    except Exception as e:
        print(f"❌ Telegram hatası: {str(e)}")

def save_results_to_json(below_sma_results, crossover_results, filename="results.json"):
    """Sonuçları JSON dosyasına kaydet"""
    results = {
        "timestamp": datetime.now().isoformat(),
        "below_sma": below_sma_results,
        "crossovers": crossover_results
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Sonuçlar {filename} dosyasına kaydedildi")

def main():
    print("🚀 BIST 100 RSI Tarayıcı Başlatıldı")
    print(f"📅 Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 Toplam {len(SYMBOLS)} hisse analiz edilecek\n")
    
    below_sma_results = []
    crossover_results = []
    
    successful = 0
    failed = 0

    for idx, symbol in enumerate(SYMBOLS, 1):
        try:
            print(f"[{idx}/{len(SYMBOLS)}] {symbol} analiz ediliyor...", end=" ")
            
            # Haftalık veriyi çek
            stock = yf.Ticker(symbol)
            df = stock.history(period="2y", interval="1wk")
            
            if df.empty or len(df) < 32:
                print("❌ Yetersiz veri")
                failed += 1
                continue

            # RSI ve SMA hesapla
            df['RSI'] = calculate_rsi(df['Close'], periods=31)
            df['RSI_SMA'] = df['RSI'].rolling(window=31).mean()

            latest = df.iloc[-1]
            previous = df.iloc[-2]

            # RSI < SMA kontrolü
            if latest['RSI'] < latest['RSI_SMA']:
                result = {
                    "symbol": symbol.replace('.IS', ''),
                    "rsi": float(latest['RSI']),
                    "sma": float(latest['RSI_SMA'])
                }
                below_sma_results.append(result)
                print(f"✅ RSI < SMA")
            
            # Yukarı kesme kontrolü
            elif previous['RSI'] < previous['RSI_SMA'] and latest['RSI'] > latest['RSI_SMA']:
                result = {
                    "symbol": symbol.replace('.IS', ''),
                    "current_rsi": float(latest['RSI']),
                    "current_sma": float(latest['RSI_SMA']),
                    "previous_rsi": float(previous['RSI']),
                    "previous_sma": float(previous['RSI_SMA'])
                }
                crossover_results.append(result)
                print(f"✅ Yukarı kesti")
            else:
                print("⚪ Koşul sağlanmadı")
            
            successful += 1
            
        except Exception as e:
            print(f"❌ Hata: {str(e)}")
            failed += 1

    # Özet bilgileri yazdır
    print("\n" + "="*50)
    print("📊 ANALIZ SONUÇLARI")
    print("="*50)
    print(f"✅ Başarılı: {successful}")
    print(f"❌ Başarısız: {failed}")
    print(f"📉 RSI < SMA: {len(below_sma_results)} hisse")
    print(f"🚀 Yukarı Kesenler: {len(crossover_results)} hisse")
    print("="*50 + "\n")

    # Telegram mesajı oluştur
    message_parts = []
    
    # Başlık
    message_parts.append(f"*📈 BIST 100 RSI Tarayıcı*")
    message_parts.append(f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
    
    # RSI < SMA olanlar
    message_parts.append(f"*📉 RSI < SMA ({len(below_sma_results)} hisse):*")
    if below_sma_results:
        for stock in below_sma_results[:50]:  # İlk 50 hisse
            message_parts.append(
                f"• {stock['symbol']}: RSI {stock['rsi']:.2f} < SMA {stock['sma']:.2f}"
            )
        if len(below_sma_results) > 50:
            message_parts.append(f"... ve {len(below_sma_results) - 50} hisse daha")
    else:
        message_parts.append("Koşulu sağlayan hisse yok")
    
    message_parts.append("")
    
    # Yukarı kesenler
    message_parts.append(f"*🚀 Yukarı Kesenler ({len(crossover_results)} hisse):*")
    if crossover_results:
        for stock in crossover_results[:10]:  # İlk 10 hisse
            message_parts.append(
                f"• {stock['symbol']}: {stock['current_rsi']:.2f} > {stock['current_sma']:.2f}"
            )
        if len(crossover_results) > 10:
            message_parts.append(f"... ve {len(crossover_results) - 10} hisse daha")
    else:
        message_parts.append("Koşulu sağlayan hisse yok")

    message = "\n".join(message_parts)
    
    # Telegram'a gönder
    send_telegram_message(message)
    
    # JSON dosyasına kaydet
    save_results_to_json(below_sma_results, crossover_results)
    
    print("✅ Analiz tamamlandı!")

if __name__ == "__main__":
    main()
