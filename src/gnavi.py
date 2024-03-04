# requestsライブラリをインポート
import requests
# pandasライブラリをインポート
import pandas as pd
# reライブラリをインポート
import re
# Beautifulsoupライブラリをインポート
from bs4 import BeautifulSoup
# timeモジュールをインポート
import time

# ユーザーエージェントを設定
user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
headers = {'User-Agent': user_agent}

# 空のデータフレームを作成
df = pd.DataFrame(columns=["店舗名", "電話番号", "メールアドレス", "都道府県", "市区町村", "番地", "建物名", "URL", "SSL"])

# 住所の分割に必要な正規表現パターンを定義
pref_pattern = "(北海道|青森県|岩手県|宮城県|秋田県|山形県|福島県|茨城県|栃木県|群馬県|埼玉県|千葉県|東京都|神奈川県|新潟県|富山県|石川県|福井県|山梨県|長野県|岐阜県|静岡県|愛知県|三重県|滋賀県|京都府|大阪府|兵庫県|奈良県|和歌山県|鳥取県|島根県|岡山県|広島県|山口県|徳島県|香川県|愛媛県|高知県|福岡県|佐賀県|長崎県|熊本県|大分県|宮崎県|鹿児島県|沖縄県)"
city_pattern = "(.*?[市区町村])"
block_pattern = r"(.*?[\d-]+)"
address_pattern = f"{pref_pattern}{city_pattern}{block_pattern}"

# 店舗ページ一覧のURLを取得
# ぐるなびの店舗一覧URL
top_url = "https://r.gnavi.co.jp/area/nara/rs/"
shop_url_pattern = "https://r.gnavi.co.jp/[0-9a-zA-Z]+/"
remove_urls = ["https://r.gnavi.co.jp/nara/"]
shop_urls = []
page = 1
while len(shop_urls) < 50:
    # 3秒待つ
    time.sleep(3)

    top_url = f"https://r.gnavi.co.jp/area/nara/rs/?p={page}"
    # HTMLデータを取得
    top_html = requests.get(top_url, headers=headers).content
    # HTMLデータをパース
    top_soup = BeautifulSoup(top_html, "html.parser")
    for a in top_soup.find_all("a"):
        class_name = a.get("class")
        href = a.get("href")
        if re.fullmatch(shop_url_pattern, href):
            shop_urls.append(href)

    # 重複と不要なURLを削除
    shop_urls = list(set(shop_urls) - set(remove_urls))
    # ページを1つ進める
    page += 1

# 店舗ページ一覧のURLをループで回す
count = 0
# レコード数をカウントする変数
for shop_url in shop_urls:
    # 3秒待つ
    time.sleep(3)
    # 各店舗ページのHTMLデータを取得
    shop_html = requests.get(shop_url)
    # レスポンスコードが200でなければスキップする
    if shop_html.status_code != 200:
        continue
    # HTMLデータをパース
    shop_soup = BeautifulSoup(shop_html.content, "html.parser")

    # 店舗名を取得
    shop_name = ""
    name_tag = shop_soup.find("p", id ="info-name")
    # 店舗名があればテキストを取得する
    if name_tag:
        shop_name = name_tag.text.replace(u"\xa0", u" ")

    # 電話番号を取得
    shop_tel = ""
    tel_tag = shop_soup.find("span", class_= "number")
    # 電話番号があればテキストを取得する
    if tel_tag:
        shop_tel = tel_tag.text

    # メールアドレスを取得
    shop_mail = ""
    mail_link = shop_soup.select("a[href^=mailto]")
    # メールアドレスがあればテキストを取得する
    if len(mail_link) > 0:
        shop_mail = mail_link[0].get("href").replace("mailto:", "")
    
    # 住所1を取得
    shop_address = ""
    address_tag = shop_soup.find("span", class_="region")
    # 住所があればテキストを取得する
    if address_tag:
        shop_address = address_tag.text

    # 住所2を取得
    shop_locality = ""
    locality_tag = shop_soup.find("span", class_="locality")
    # 住所があればテキストを取得する
    if locality_tag:
        shop_locality = locality_tag.text

    # URLを取得
    shop_url = ""
    url_link = shop_soup.find("a", class_="url go-off")
    # URLがあればテキストを取得する
    if url_link:
        shop_url = url_link.get("href")

    # SSLを判定
    shop_ssl = shop_url.startswith("https:")

    # 住所を正規表現で分割
    address_match = re.search(address_pattern, shop_address)

    # 都道府県、市区町村、番地、建物名を取得
    shop_pref = address_match.group(1) if address_match.group(1) else ""
    shop_city = address_match.group(2) if address_match.group(2)  else ""
    shop_block = address_match.group(3)  if address_match.group(3)  else ""

    # 取得したデータをデータフレームに追加
    df.loc[count] = [shop_name, shop_tel, shop_mail, shop_pref, shop_city, shop_block, shop_locality, shop_url, shop_ssl]
    count += 1 # レコード数をインクリメント
    # 50レコード分取得したらループを終了
    if count == 50:
        break

# データフレームをcsvファイルに出力
df.to_csv("gnavi.csv", index=False)
