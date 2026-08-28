import os
import time
from datetime import datetime, timedelta
from collections import deque, Counter
from atproto import Client
from dotenv import load_dotenv

load_dotenv()

REGION_COORDINATES = {
    "北海道": [141.3469, 43.0641],
    "東京":   [139.6917, 35.6895],
    "京都":   [135.7681, 35.0116],
    "大阪":   [135.5021, 34.6937],
    "福岡":   [130.4180, 33.6063],
    "沖縄":   [127.6809, 26.2124],
}

def connect_to_bluesky():
    client = Client()
    # 環境変数からログイン情報を取得
    handle = os.getenv("BSKY_HANDLE")
    password = os.getenv("BSKY_PASSWORD")
    
    if not handle or not password:
        raise ValueError(".env ファイルに BSKY_HANDLE と BSKY_PASSWORD を設定してください。")
        
    client.login(handle, password)
    print("Blueskyへのログインに成功しました！")
    return client

class PostTracker:
    def __init__(self, hours_to_keep=1):
        self.hours_to_keep = hours_to_keep
        self.history = deque()

    def add_post(self, region: str):
        now = datetime.now()
        self.history.append((now, region))
        print(f"[{now.strftime('%H:%M:%S')}] '{region}' の投稿を検知しました")
        self._clean_old_posts()

    def _clean_old_posts(self):
        now = datetime.now()
        time_limit = now - timedelta(hours=self.hours_to_keep)

        while self.history and self.history[0][0] < time_limit:
            removed_time, removed_region = self.history.popleft()
            print(f"{self.hours_to_keep}時間を経過したため古いデータを削除: {removed_region}({removed_time.strftime('%H:%M:%S')})")

    def get_geojson_data(self):
        self._clean_old_posts()
        regions = [region for timestamp, region in self.history]
        scores = Counter(regions)
        
        max_count = max(scores.values()) if scores else 1

        features = []
        for region, count in scores.items():
            if region in REGION_COORDINATES:
                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": REGION_COORDINATES[region]
                    },
                    "properties": {
                        "region_name": region,
                        "count": count,
                        "intensity": count / max_count
                    }
                }
                features.append(feature)

        return {
            "type": "FeatureCollection",
            "features": features
        }
        
    def get_activity_scores(self):
        self._clean_old_posts()
        regions = [region for timestamp, region in self.history]
        return Counter(regions)

if __name__ == "__main__":
    try:
        client = connect_to_bluesky()
    except Exception as e:
        print(f"ログインに失敗しました: {e}")
        exit()

    tracker = PostTracker(hours_to_keep=1)
    
    SEARCH_QUERY = "ラーメン" 
    TARGET_REGIONS = ["京都", "大阪", "東京", "北海道", "福岡", "沖縄"]
    
    # 過去に処理したURIを保持するデック（最大200件保持）
    seen_uris = deque(maxlen=200)

    print(f"\n🚀 Bluesky全体から「{SEARCH_QUERY}」に関する投稿の監視を開始します... (Ctrl+C で停止)")
    print("----------------------------------------------------------------")

    try:
        while True:
            try:
                search_results = client.app.bsky.feed.search_posts(
                    params={'q': SEARCH_QUERY, 'limit': 30}
                )
                
                # 新しい順で取得されるため、重複していないものを抽出
                new_posts = [p for p in search_results.posts if p.uri not in seen_uris]

                if new_posts:
                    # 古い投稿から順に処理
                    for post in reversed(new_posts):
                        seen_uris.append(post.uri)
                        
                        text = post.record.text
                        user = post.author.handle
                        
                        matched_regions = [r for r in TARGET_REGIONS if r in text]
                        
                        if matched_regions:
                            print(f"\n[ユーザー: @{user}] 投稿: {text.strip()}")
                            for region in matched_regions:
                                tracker.add_post(region)

                # 集計の表示
                scores = tracker.get_activity_scores()
                if scores:
                    print(f"\n📊 【現在の地域活性度（「{SEARCH_QUERY}」を含む過去{tracker.hours_to_keep}時間以内）】")
                    print(dict(scores))
                
            except Exception as api_error:
                print(f"\n⚠️ エラーが発生しました（自動リトライします）: {api_error}")

            # API制限対策のため待機時間を30秒に変更
            time.sleep(30)

    except KeyboardInterrupt:
        print("\n🛑 監視を終了しました。")