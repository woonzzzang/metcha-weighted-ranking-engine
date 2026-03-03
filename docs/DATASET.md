# 데이터셋 수집 계획

> TMDB API로 **장르별 인기 영화 1,000편씩** 미리 수집해 DB에 넣어 두는 방식으로 진행합니다.

---

## 1. 범위

| 항목 | 내용 |
|------|------|
| **소스** | TMDB API |
| **단위** | 장르별 인기 영화 **1,000편** |
| **정렬** | 인기순(`popularity.desc`) |
| **언어** | `language=ko` (한글 제목·줄거리 when available) |

- TMDB 장르 목록은 API `GET /genre/movie/list`로 조회 (예: 액션 28, 드라마 18, 코미디 35 등).
- 장르 수만큼 × 1,000편을 요청하므로, **총 요청 건수**는 장르 수 × 50페이지(페이지당 20편) 수준.
- 같은 영화가 여러 장르에 속할 수 있어 **실제 고유 영화 수**는 (장르 수 × 1,000)보다 적을 수 있음. DB 적재 시 `tmdb_id` 기준으로 중복 제거.

---

## 2. TMDB API 제약

- **페이지당 결과**: 20편 고정 (변경 불가).
- **최대 페이지**: 500 (장르당 최대 10,000편까지 가능).
- 1,000편 = **50페이지** 요청.

---

## 3. 수집 절차

1. **장르 목록 조회**  
   `GET /genre/movie/list?language=ko`
2. **장르별 인기 영화 1,000편 수집**  
   `GET /discover/movie?with_genres={genre_id}&sort_by=popularity.desc&language=ko&page=1..50`
3. **결과 병합 및 중복 제거**  
   `tmdb_id` 기준으로 한 편만 유지 (첫 등장 시의 메타데이터 사용, `genre_ids`는 응답에 포함된 값 사용).
4. **저장**  
   Movie 테이블 스키마에 맞는 JSON(또는 CSV)으로 저장 후, DB import 시 사용.

---

## 4. 실행 방법

- **스크립트**: `scripts/fetch_tmdb_by_genre.py`
- **필요 환경 변수**: `TMDB_API_KEY` (TMDB 개발자 사이트에서 발급)
- **출력**: `data/tmdb_movies.json` (또는 스크립트에 지정된 경로)

```bash
# 예시 (프로젝트 루트에서)
set TMDB_API_KEY=your_api_key_here
python scripts/fetch_tmdb_by_genre.py
```

- 이후 백엔드/DB가 준비되면 이 JSON을 읽어서 **Movie** 테이블에 `INSERT`(또는 `get_or_create(tmdb_id=...)`) 하면 됨.

---

## 5. 출력 스키마 (Movie 테이블과 맞춤)

| 필드 | TMDB 응답 매핑 | 비고 |
|------|----------------|------|
| tmdb_id | `id` | UK |
| title | `title` (language=ko 요청 시 한글) | |
| title_en | `original_title` | |
| overview | `overview` | |
| poster_path | `poster_path` | |
| backdrop_path | `backdrop_path` | |
| release_date | `release_date` | |
| popularity | `popularity` | |
| vote_average | `vote_average` | |
| vote_count | `vote_count` | |
| genre_ids | `genre_ids` | JSON 배열로 저장 (또는 Genre 테이블과 N:M) |

- `heaviness`, `satisfaction`는 **MovieScore**에서 나중에 생성하므로 이 수집 단계에서는 제외.
