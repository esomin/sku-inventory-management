# Requirements Document

## Introduction

GPU 가격 모니터링 ETL 시스템은 기존 SKU 재고 관리 시스템을 GPU 제품에 특화하여 확장하고, 다나와 가격 데이터 및 Reddit 커뮤니티 신호를 수집·분석하여 재고 가치 하락 위험을 조기에 감지하는 시스템입니다. 

본 시스템은 **RTX 4070 시리즈**(4070, 4070 Super, 4070 Ti, 4070 Ti Super)로 범위를 한정합니다. 이 시리즈는 현재 시장에서 가장 활발하게 거래되는 메인스트림 제품이며, 새로운 'Super' 모델 출시나 가격 인하 시 기존 일반 모델의 재고 가치 변화를 비교 분석하기에 가장 적합한 표준 데이터입니다.

이를 통해 GPU 재고 관리자는 시장 변화에 선제적으로 대응할 수 있습니다.

## Glossary

- **ETL_System**: 가격 및 커뮤니티 데이터를 추출(Extract), 변환(Transform), 적재(Load)하는 Python 기반 애플리케이션
- **SKU_Entity**: 기존 재고 관리 시스템의 제품 엔티티 (Spring Boot 백엔드)
- **Price_Crawler**: 다나와 웹사이트에서 GPU 가격 데이터를 수집하는 크롤러 모듈
- **Reddit_Collector**: Reddit RSS 피드에서 GPU 관련 커뮤니티 신호를 수집하는 모듈
- **Product_Normalizer**: 제품명을 파싱하여 Brand, Chipset, VRAM, OC 여부 등을 추출하는 변환 모듈
- **Risk_Calculator**: 가격 변동률과 커뮤니티 감성을 기반으로 재고 위험 지수를 계산하는 모듈
- **Database**: PostgreSQL 데이터베이스 (Products, Price_Logs, Market_Signals 테이블 포함)
- **Frontend**: React 기반 프론트엔드 (가격 추이 시각화 및 대시보드)
- **Scheduler**: APScheduler 또는 Celery 기반 작업 스케줄러

## Requirements

### Requirement 1: GPU 특화 SKU 엔티티 확장

**User Story:** GPU 재고 관리자로서, GPU 제품의 고유 속성(칩셋, 브랜드, VRAM, OC 여부)을 시스템에 저장하고 싶습니다. 이를 통해 제품을 정확하게 식별하고 분류할 수 있습니다.

#### Acceptance Criteria

1. THE SKU_Entity SHALL include fields for chipset, brand, model_name, vram, and is_oc
2. WHEN a GPU product is created, THE SKU_Entity SHALL enforce category as "그래픽카드"
3. THE SKU_Entity SHALL store chipset as a string limited to RTX 4070 series variants: "RTX 4070", "RTX 4070 Super", "RTX 4070 Ti", "RTX 4070 Ti Super"
4. THE SKU_Entity SHALL store vram as a string with unit (e.g., "12GB")
5. THE SKU_Entity SHALL store is_oc as a boolean value

### Requirement 2: 제품명 정규화

**User Story:** 시스템 관리자로서, RTX 4070 시리즈 제품명을 자동으로 파싱하여 구조화된 데이터로 변환하고 싶습니다. 이를 통해 4070 시리즈 내 모델 간 제품 비교 및 검색이 용이해집니다.

#### Acceptance Criteria

1. WHEN a product name is provided, THE Product_Normalizer SHALL extract the brand name
2. WHEN a product name is provided, THE Product_Normalizer SHALL extract the chipset model from RTX 4070 series variants
3. WHEN a product name is provided, THE Product_Normalizer SHALL extract the VRAM capacity
4. WHEN a product name contains "OC" or "오버클럭", THE Product_Normalizer SHALL set is_oc to true
5. WHEN extraction fails for any field, THE Product_Normalizer SHALL return an error with the field name
6. WHEN a product name does not match RTX 4070 series, THE Product_Normalizer SHALL reject it with an error

### Requirement 3: 가격 데이터 크롤링

**User Story:** 가격 분석가로서, 다나와에서 RTX 4070 시리즈 GPU의 현재가와 최근 3개월 가격 추이를 자동으로 수집하고 싶습니다. 이를 통해 시장 가격 동향을 파악할 수 있습니다.

#### Acceptance Criteria

1. WHEN scheduled, THE Price_Crawler SHALL fetch current prices from 다나와 website
2. WHEN fetching prices, THE Price_Crawler SHALL retrieve price history for the last 3 months
3. WHEN price data is fetched, THE Price_Crawler SHALL include the source URL
4. WHEN a crawling error occurs, THE Price_Crawler SHALL log the error and continue with remaining products

### Requirement 4: Reddit 커뮤니티 신호 수집

**User Story:** 시장 분석가로서, Reddit의 GPU 관련 서브레딧에서 신제품 출시, 가격 하락, 이슈 등의 키워드를 모니터링하고 싶습니다. 이를 통해 시장 트렌드를 조기에 감지할 수 있습니다.

#### Acceptance Criteria

1. WHEN scheduled, THE Reddit_Collector SHALL fetch RSS feeds from r/nvidia
2. WHEN scheduled, THE Reddit_Collector SHALL fetch RSS feeds from r/pcmasterrace
3. WHEN processing posts, THE Reddit_Collector SHALL filter by keywords: "New Release", "Leak", "Issues", "Price Drop", "Used Market"
4. WHEN a matching post is found, THE Reddit_Collector SHALL extract the keyword, post title, and timestamp
5. WHEN Reddit API rate limit is reached, THE Reddit_Collector SHALL wait and retry after the limit resets

### Requirement 5: 가격 추이 분석

**User Story:** 재고 관리자로서, GPU 가격의 전주 대비 변동률을 자동으로 계산하고 싶습니다. 이를 통해 가격 하락 추세를 빠르게 파악할 수 있습니다.

#### Acceptance Criteria

1. WHEN new price data is loaded, THE ETL_System SHALL calculate the week-over-week price change percentage
2. WHEN calculating price change, THE ETL_System SHALL compare current price with the average price from 7 days ago
3. WHEN historical data is insufficient (less than 7 days), THE ETL_System SHALL skip the calculation and log a warning
4. THE ETL_System SHALL store the calculated price change percentage with the price record

### Requirement 6: 커뮤니티 감성 분석

**User Story:** 시장 분석가로서, Reddit 게시물에서 신제품 언급 빈도를 분석하고 싶습니다. 이를 통해 신제품 출시가 기존 재고에 미치는 영향을 예측할 수 있습니다.

#### Acceptance Criteria

1. WHEN processing Reddit posts, THE ETL_System SHALL count mentions of each target keyword per day
2. WHEN a keyword appears multiple times in a post, THE ETL_System SHALL count it as one mention
3. THE ETL_System SHALL calculate a sentiment score based on keyword frequency (higher frequency = higher score)
4. WHEN calculating sentiment score, THE ETL_System SHALL apply weights: "New Release" (3x), "Price Drop" (2x), others (1x)

### Requirement 7: 재고 위험 지수 계산

**User Story:** 재고 관리자로서, 가격 하락과 커뮤니티 신호를 종합한 재고 위험 지수를 확인하고 싶습니다. 이를 통해 재고 처분 시점을 결정할 수 있습니다.

#### Acceptance Criteria

1. WHEN price and sentiment data are available, THE Risk_Calculator SHALL compute a risk index
2. THE Risk_Calculator SHALL use the formula: risk_index = (current_price - last_week_avg_price) + (new_release_mentions × 0.3)
3. WHEN the risk index exceeds a threshold, THE Risk_Calculator SHALL flag the product as high-risk
4. THE Risk_Calculator SHALL store the risk index with a timestamp

### Requirement 8: 데이터 적재

**User Story:** 시스템 관리자로서, 수집 및 변환된 데이터를 PostgreSQL 데이터베이스에 저장하고 싶습니다. 이를 통해 프론트엔드에서 데이터를 조회하고 시각화할 수 있습니다.

#### Acceptance Criteria

1. WHEN a new GPU product is normalized, THE ETL_System SHALL insert it into the Products table
2. WHEN price data is fetched, THE ETL_System SHALL insert records into the Price_Logs table with sku_id, price, recorded_at, and source_url
3. WHEN Reddit signals are processed, THE ETL_System SHALL insert records into the Market_Signals table with keyword, sentiment_score, mention_count, and date
4. WHEN inserting duplicate records (same sku_id and recorded_at), THE ETL_System SHALL update the existing record instead of creating a new one
5. WHEN a database connection error occurs, THE ETL_System SHALL retry up to 3 times before logging a failure

### Requirement 9: 자동 스케줄링

**User Story:** 시스템 관리자로서, ETL 작업이 매일 자동으로 실행되기를 원합니다. 이를 통해 수동 개입 없이 최신 데이터를 유지할 수 있습니다.

#### Acceptance Criteria

1. THE Scheduler SHALL execute the price crawling task once per day at a configured time
2. THE Scheduler SHALL execute the Reddit collection task once per day at a configured time
3. WHEN a scheduled task fails, THE Scheduler SHALL log the error and continue with the next scheduled task
4. THE Scheduler SHALL allow manual triggering of any task through a CLI command

### Requirement 10: 가격 추이 시각화

**User Story:** 재고 관리자로서, 프론트엔드에서 GPU 가격 추이를 그래프로 확인하고 싶습니다. 이를 통해 가격 변동 패턴을 시각적으로 파악할 수 있습니다.

#### Acceptance Criteria

1. WHEN a user selects a GPU product, THE Frontend SHALL display a line chart of price history for the last 3 months
2. THE Frontend SHALL show prices from 다나와
3. WHEN hovering over a data point, THE Frontend SHALL display the exact price, date, and source
4. THE Frontend SHALL allow filtering by date range

### Requirement 11: 커뮤니티 트렌드 대시보드

**User Story:** 시장 분석가로서, Reddit 키워드 트렌드를 대시보드에서 확인하고 싶습니다. 이를 통해 시장 분위기를 한눈에 파악할 수 있습니다.

#### Acceptance Criteria

1. THE Frontend SHALL display a bar chart showing mention counts for each keyword over the last 30 days
2. THE Frontend SHALL highlight keywords with increasing trends (week-over-week growth > 50%)
3. WHEN a user clicks on a keyword, THE Frontend SHALL display the top 5 related Reddit posts
4. THE Frontend SHALL refresh the dashboard data every 24 hours

### Requirement 12: 재고 위험 알림

**User Story:** 재고 관리자로서, 재고 위험 지수가 임계값을 초과하는 제품에 대한 알림을 받고 싶습니다. 이를 통해 신속하게 대응할 수 있습니다.

#### Acceptance Criteria

1. WHEN a product's risk index exceeds the configured threshold, THE ETL_System SHALL generate an alert
2. THE ETL_System SHALL include the product name, current risk index, and contributing factors in the alert
3. THE Frontend SHALL display active alerts in a dedicated notification panel
4. WHEN a user dismisses an alert, THE Frontend SHALL mark it as acknowledged but keep it in the history

### Requirement 13: RTX 4070 시리즈 간 비교 분석

**User Story:** 재고 관리자로서, RTX 4070 시리즈 내 모델 간 가격 변동 및 재고 위험도를 비교하고 싶습니다. 이를 통해 신규 Super 모델 출시 시 기존 일반 모델의 재고 가치 변화를 분석할 수 있습니다.

#### Acceptance Criteria

1. THE Frontend SHALL display a comparison table showing all RTX 4070 series models side-by-side
2. THE Frontend SHALL show current price, week-over-week price change, and risk index for each model
3. WHEN a new Super model is released, THE Frontend SHALL highlight price drops in non-Super models
4. THE Frontend SHALL calculate and display the price gap between model variants (e.g., 4070 vs 4070 Super)
5. WHEN a user selects two models, THE Frontend SHALL display overlaid price trend charts for direct comparison
