import requests

url = "https://api.coinbase.com/v2/currencies"

print(f"Mencoba menghubungkan ke: {url} (tanpa header khusus)")

try:
    # Panggilan requests standar tanpa header User-Agent
    response = requests.get(url, timeout=10)
    
    print(f"\n✅ KONEKSI BERHASIL!")
    print(f"Status Code: {response.status_code}")
    
    data = response.json()
    print(f"Contoh data: {data['data'][0]}")

except requests.exceptions.RequestException as e:
    print(f"\n❌ KONEKSI GAGAL dengan library requests.")
    print(f"Ini akan aneh jika gagal, karena membuktikan ada yang tidak konsisten.")
    print(f"Detail Error: {e}")