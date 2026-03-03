# 영화 추천·리뷰 플랫폼 ERD

> 데이터셋(TMDB) 준비 전에 도메인 모델과 ERD를 먼저 정의합니다.

---

## 1. 엔티티 요약

| 엔티티 | 설명 |
|--------|------|
| **User** | 회원 (리뷰·팔로우·취향 분석 주체) |
| **Movie** | 영화 (TMDB에서 가져오는 메타데이터만) |
| **MovieScore** | 영화별 Heaviness/Satisfaction (우리 생성) |
| **Review** | 리뷰 (별점, 텍스트, ChromaDB 임베딩 원본) |
| **Watchlist** | 보고싶은 영화 목록 (User–Movie N:M) |
| **Follow** | 팔로우 관계 (User → User) |
| **ReviewLike** | 리뷰 좋아요 (User–Review N:M) |

**외부/별도 저장소**
- **ChromaDB**: 리뷰 텍스트 임베딩 벡터 (검색용, ERD에는 테이블로 안 둠)
- **TMDB API**: 영화 메타데이터 소스 (Movie 테이블은 여기서 가져온 데이터만 저장)

**참고**  
- **가져오는 경로(URL)** 는 테이블에 넣지 않음. `tmdb_id`만 저장하고, 이미지/상세 조회 시 TMDB 기준 URL + `poster_path` 등으로 조합.
- Heaviness, Satisfaction 등 **우리가 생성하는 값**은 Movie가 아니라 **MovieScore** 테이블로 분리.

---

## 2. ER 다이어그램 (Mermaid)

```mermaid
erDiagram
    User ||--o{ Review : writes
    User ||--o{ Watchlist : has
    User ||--o{ Follow : "follows (follower)"
    User ||--o{ Follow : "followed by (following)"
    User ||--o{ ReviewLike : likes

    Movie ||--o| MovieScore : "has (optional)"
    Movie ||--o{ Review : "has"
    Movie ||--o{ Watchlist : "in"

    Review ||--o{ ReviewLike : receives

    User {
        int id PK
        string username
        string email
        string password_hash
        string display_name
        string avatar_url "nullable"
        datetime created_at
        datetime updated_at
    }

    Movie {
        int id PK
        int tmdb_id UK "TMDB API id"
        string title
        string title_en "nullable"
        string overview
        string poster_path "nullable"
        string backdrop_path "nullable"
        date release_date "nullable"
        float popularity "nullable"
        float vote_average "nullable"
        int vote_count "nullable"
        jsonb genres "또는 별도 Genre, MovieGenre 테이블"
        datetime created_at
        datetime updated_at
    }

    MovieScore {
        int id PK
        int movie_id FK UK
        int heaviness "0-100"
        int satisfaction "0-100"
        datetime updated_at
    }

    Review {
        int id PK
        int user_id FK
        int movie_id FK
        float rating "0.0-5.0"
        text content "nullable"
        text content_for_embedding "보강/정제 텍스트, nullable"
        boolean has_spoiler
        datetime created_at
        datetime updated_at
    }

    Watchlist {
        int id PK
        int user_id FK
        int movie_id FK
        datetime created_at
    }

    Follow {
        int id PK
        int follower_id FK "User"
        int following_id FK "User"
        datetime created_at
    }

    ReviewLike {
        int id PK
        int user_id FK
        int review_id FK
        datetime created_at
    }
```

---

## 3. 테이블별 상세

### 3.1 User

| 컬럼 | 타입 | 제약 | 비고 |
|------|------|------|------|
| id | PK | | |
| username | string | UK, NOT NULL | 로그인 ID |
| email | string | UK, NOT NULL | |
| password_hash | string | NOT NULL | |
| display_name | string | | 닉네임 |
| avatar_url | string | nullable | 프로필 이미지 |
| created_at | datetime | | |
| updated_at | datetime | | |

- **Review**: 1:N (한 유저가 여러 리뷰)
- **Watchlist**: 1:N
- **Follow**: follower_id / following_id 로 self N:M
- **ReviewLike**: 1:N

---

### 3.2 Movie (TMDB에서 가져오는 데이터만)

**가져오는 경로(URL)는 저장하지 않음.** `tmdb_id`만 저장하고, 이미지가 필요할 때 TMDB 이미지 베이스 URL + `poster_path`를 붙여서 사용.

| 컬럼 | 타입 | 제약 | 비고 |
|------|------|------|------|
| id | PK | | 내부 ID |
| tmdb_id | int | UK, NOT NULL | TMDB API id (상세/이미지 조회 시 사용) |
| title | string | NOT NULL | 한글 제목 우선 |
| title_en | string | nullable | |
| overview | text | nullable | 줄거리 |
| poster_path | string | nullable | TMDB 이미지 path (URL 아님) |
| backdrop_path | string | nullable | |
| release_date | date | nullable | |
| popularity | float | nullable | TMDB |
| vote_average | float | nullable | TMDB |
| vote_count | int | nullable | TMDB |
| genres | jsonb 등 | nullable | 옵션: Genre + MovieGenre N:M 대체 |
| created_at | datetime | | |
| updated_at | datetime | | |

- 위 컬럼은 **전부 TMDB API 응답에서 매핑**하는 값만 포함.
- **장르**: TMDB는 여러 장르 ID. 옵션 1) `genres` JSONB, 옵션 2) Genre 테이블 + MovieGenre N:M.

---

### 3.3 MovieScore (우리가 생성하는 데이터)

Heaviness/Satisfaction 등 추천 알고리즘용 점수. GPT 등으로 영화별 생성·업데이트.

| 컬럼 | 타입 | 제약 | 비고 |
|------|------|------|------|
| id | PK | | |
| movie_id | FK → Movie | UK, NOT NULL | 영화 1건당 1행 |
| heaviness | int | NOT NULL, 0–100 | 무게감/심각성 |
| satisfaction | int | NOT NULL, 0–100 | 대중성/만족도 |
| updated_at | datetime | | |

---

### 3.4 Review

| 컬럼 | 타입 | 제약 | 비고 |
|------|------|------|------|
| id | PK | | |
| user_id | FK → User | NOT NULL | |
| movie_id | FK → Movie | NOT NULL | |
| rating | float | NOT NULL, 0.0–5.0 | |
| content | text | nullable | 사용자 작성 리뷰 |
| content_for_embedding | text | nullable | 시맨틱 검색용 보강 텍스트 |
| has_spoiler | boolean | NOT NULL, default false | |
| created_at | datetime | | |
| updated_at | datetime | | |

- (user_id, movie_id) UK 고려: 한 유저가 한 영화에 리뷰 1개만 허용할지 여부.
- ChromaDB에는 `content_for_embedding`(또는 content) 기준으로 임베딩 저장. 문서 ID는 review_id 등으로 매핑.

---

### 3.5 Watchlist

| 컬럼 | 타입 | 제약 | 비고 |
|------|------|------|------|
| id | PK | | |
| user_id | FK → User | NOT NULL | |
| movie_id | FK → Movie | NOT NULL | |
| created_at | datetime | | |

- (user_id, movie_id) UK 권장.

---

### 3.6 Follow

| 컬럼 | 타입 | 제약 | 비고 |
|------|------|------|------|
| id | PK | | |
| follower_id | FK → User | NOT NULL | 팔로우하는 사람 |
| following_id | FK → User | NOT NULL | 팔로우당하는 사람 |
| created_at | datetime | | |

- (follower_id, following_id) UK.
- follower_id ≠ following_id 체크.

---

### 3.7 ReviewLike

| 컬럼 | 타입 | 제약 | 비고 |
|------|------|------|------|
| id | PK | | |
| user_id | FK → User | NOT NULL | |
| review_id | FK → Review | NOT NULL | |
| created_at | datetime | | |

- (user_id, review_id) UK.

---

## 4. TMDB API와의 매핑

- **Movie 테이블** = TMDB에서 가져온 메타데이터만 저장. **가져오는 경로(API URL)** 는 저장하지 않고, `tmdb_id`만 저장해 필요 시 상세/이미지 조회에 사용.
- **Movie 1건** ≈ TMDB `movie` 리소스 한 건. TMDB 필드 예: `id` → `tmdb_id`, `title`, `overview`, `poster_path`, `release_date`, `vote_average`, `genre_ids` 등.
- Heaviness/Satisfaction 등 우리가 생성하는 값은 **MovieScore** 테이블에만 둠.
- ERD 확정 후, “TMDB 응답 필드 → Movie 컬럼” 매핑 테이블을 한 번 더 두면 데이터셋 준비 시 헷갈리지 않음.

---

## 5. 권장 진행 순서 (데이터셋 전)

1. **ERD 확정** (이 문서)  
   - 팀원 없이 진행하므로 여기서 스키마 버전 1로 고정해도 됨.
2. **API 명세 초안**  
   - 엔드포인트 목록만 나열 (예: `GET /movies`, `POST /reviews`, `GET /search?q=...`).
3. **TMDB 데이터 매핑**  
   - TMDB 응답 필드 → `Movie`(및 Genre) 컬럼 매핑 문서.
4. **데이터셋 준비**  
   - TMDB API로 영화 목록 수집 → `Movie` 테이블에 넣을 CSV/JSON 형태로 정리.  
   - 리뷰는 시드 데이터를 만들거나, 나중에 사용자 생성으로 채움.

정리하면, **ERD(및 이 문서) 먼저 하고 → TMDB 매핑 정리한 뒤 → 데이터셋(TMDB) 준비**하는 순서가 좋습니다.
