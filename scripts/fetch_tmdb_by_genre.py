"""
TMDB API로 장르별 인기 영화 1,000편씩 수집.
출력: data/tmdb_movies.json (Movie 테이블 스키마에 맞춤, tmdb_id 기준 중복 제거)

필요: TMDB_API_KEY 환경 변수
실행: python scripts/fetch_tmdb_by_genre.py
"""

import os
import json
import time
from pathlib import Path

try:
    import requests
except ImportError:
    raise SystemExit("pip install requests 후 다시 실행하세요.")

BASE_URL = "https://api.themoviedb.org/3"
PER_GENRE = 1000
PAGE_SIZE = 20
PAGES_PER_GENRE = (PER_GENRE + PAGE_SIZE - 1) // PAGE_SIZE  # 50


def get_api_key():
    key = os.environ.get("TMDB_API_KEY", "").strip()
    if not key:
        raise SystemExit("TMDB_API_KEY 환경 변수를 설정하세요.")
    return key


def fetch_genres(api_key: str, language: str = "ko") -> list[dict]:
    r = requests.get(
        f"{BASE_URL}/genre/movie/list",
        params={"language": language, "api_key": api_key},
        timeout=30,
    )
    r.raise_for_status()
    return r.json().get("genres", [])


def fetch_discover_page(
    api_key: str, genre_id: int, page: int, language: str = "ko"
) -> list[dict]:
    r = requests.get(
        f"{BASE_URL}/discover/movie",
        params={
            "api_key": api_key,
            "with_genres": genre_id,
            "sort_by": "popularity.desc",
            "language": language,
            "page": page,
        },
        timeout=30,
    )
    r.raise_for_status()
    return r.json().get("results", [])


def to_movie_record(item: dict, extra_genre_ids: set | None = None) -> dict:
    genre_ids = set(item.get("genre_ids") or [])
    if extra_genre_ids:
        genre_ids |= extra_genre_ids
    return {
        "tmdb_id": item["id"],
        "title": item.get("title") or item.get("original_title") or "",
        "title_en": item.get("original_title") or None,
        "overview": item.get("overview") or None,
        "poster_path": item.get("poster_path") or None,
        "backdrop_path": item.get("backdrop_path") or None,
        "release_date": item.get("release_date") or None,
        "popularity": item.get("popularity"),
        "vote_average": item.get("vote_average"),
        "vote_count": item.get("vote_count"),
        "genre_ids": sorted(genre_ids),
    }


def main():
    api_key = get_api_key()
    data_dir = Path(__file__).resolve().parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    out_path = data_dir / "tmdb_movies.json"

    genres = fetch_genres(api_key)
    print(f"장르 수: {len(genres)}")

    # tmdb_id -> record (genre_ids는 합침)
    by_id: dict[int, dict] = {}

    for g in genres:
        gid = g["id"]
        gname = g["name"]
        print(f"  장르: {gname} (id={gid}) ...", end=" ", flush=True)
        count = 0
        for page in range(1, PAGES_PER_GENRE + 1):
            items = fetch_discover_page(api_key, gid, page)
            for item in items:
                mid = item["id"]
                if mid in by_id:
                    by_id[mid]["genre_ids"] = sorted(
                        set(by_id[mid]["genre_ids"]) | set(item.get("genre_ids") or [])
                    )
                else:
                    by_id[mid] = to_movie_record(item)
                count += 1
            time.sleep(0.25)
        print(count)
        time.sleep(0.3)

    movies = list(by_id.values())
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(movies, f, ensure_ascii=False, indent=2)

    print(f"총 고유 영화 수: {len(movies)}")
    print(f"저장: {out_path}")


if __name__ == "__main__":
    main()
