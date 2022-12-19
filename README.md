![version](https://img.shields.io/badge/version-2.4-blue)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

# Korean Workday Binary Sensor

현재 날짜가 일하는날인지의 여부를 나타냅니다. \
파이썬의 holidays 모듈을 사용하는 HA의 workday 센서가 한국 휴일을 지원하지 ~~않기~~ 않았었기 때문에, \
공공데이터포털의 휴일 API를 이용하는 커스텀 컴포넌트를 만들었습니다.

<br>

2020년 중반 이후 HA 기본 Workday 센서에서 `KR` 을 지원합니다. \
기본 센서 대비 이 커스텀 컴포넌트의 장점은 `임시공휴일`을 지원하는 것에 있습니다.

<br>

## Screenshot
![screenshot_korean_workday](https://user-images.githubusercontent.com/49514473/79182222-44311080-7e49-11ea-8ccd-5d676027717c.png)\
\
![screenshot_holiday_card](https://user-images.githubusercontent.com/49514473/79179537-cff36e80-7e42-11ea-8214-f42edbbc5703.png)

<br>

## Version history
| Version | Date        |               |
| :-----: | :---------: | ------------- |
| v1.0    | 2019.04.15  | 최초 버전 |
| v2.0    | 2020.04.14  | 기능개선, lovelace 카드 추가 |
| v2.1    | 2020.05.28  | API 호출 비동기화 |
| v2.2    | 2020.05.28  | deprecated warning 관련 수정 |
| v2.2.1  | 2021.05.29  | added version to manifest.json |
| v2.2.2  | 2021.11.04  | xmltodict requirements 로 처리 - HA Core 2021.11 |
| v2.3    | 2021.11.08  | async_track_point_in_time, KST 로 변경 |
| v2.4    | 2022.12.19  | remove_holidays 옵션 추가 |

<br>


## Installation

### 직접 설치
- HA 설치 경로 아래 custom_component 에 파일을 넣어줍니다.
<br>`<config directory>/custom_components/korean_workday/binary_sensor.py`
<br>`<config directory>/custom_components/korean_workday/__init__.py`
<br>`<config directory>/custom_components/korean_workday/manifest.json`
- configuration.yaml 파일에 설정을 추가합니다.
- Home Assistant 를 재시작합니다.

### HACS로 설치
- HACS > Integrations 메뉴 선택
- 우측 상단 메뉴 버튼 클릭 후 Custom repositories 선택
- Add Custom Repository URL 에 `https://github.com/GrecHouse/korean_workday` 입력, \
  Category에 `Integration` 선택 후 ADD
- HACS > Integrations 메뉴에서 우측 하단 + 버튼 누르고 `[KR] Korean Workday Sensor` 검색하여 설치

### Lovelace 카드 설치
- [holiday lovelace card](https://github.com/GrecHouse/korean-workday-card)

<br>

## Usage

### 2.0 버전 수정사항
- 공공데이터포털 API 없이도 매일 휴일 목록을 업데이트합니다.\
API 키 발급이 필요없습니다.
- 1.0 버전의 장보기목록(Shopping List) 대신 사용할 수 있는 커스텀 카드를 만들었습니다.\
[holiday lovelace card](https://github.com/GrecHouse/korean-workday-card) 를 이용하세요.
- 휴일인 경우 속성값으로 `holiday name`이 추가됩니다.

<br>

### (옵션) 공공데이터포털 OPEN API 이용하기
- 안 해도 됩니다. 직접 API를 이용하고 싶은 분만 설정하면 됩니다.
- 하루에 한 번 API 호출을 통해 휴일 목록을 가져옵니다.
- 공공데이터포털에서 서비스키를 발급받아야 합니다.\
[특일정보 활용신청](https://www.data.go.kr/dataset/15012690/openapi.do)

<br>

### (옵션) 장보기목록(Shopping List) 이용하기
- 이 옵션보다는 [holiday lovelace card](https://github.com/GrecHouse/korean-workday-card) 사용을 권장합니다.
- shopping_list 옵션을 true 로 지정했을 경우에만 처리됩니다.
- 장보기목록에 `#YYYYMMDD` 형식으로 날짜를 넣으면 휴일로 추가됩니다.
- 장보기목록에서 완료처리(체크) 하면 휴일에서 제거됩니다.
- 당일 휴일 등록 또는 완료(체크)시 센서값 변경까지 최대 30분 정도 소요될 수 있습니다.
- (주의) 당일 휴일 삭제는 장보기목록에서 체크한 상태에서 센서값이 변경된 것을 확인한 다음 삭제하세요.

<br>

### 참고사항
- 근로자의 날 5월 1일은 공휴일이 아니라고 합니다. add_holidays에 추가하거나 lovelace 카드에 추가하세요.
- lovelace 카드를 사용하지 않으려면, add_holidays 항목에 휴일 목록을 수작업으로 모두 넣어주면 됩니다.

<br>


### configuration
- 기본적인 설정은 HA의 workday 센서 설정과 동일합니다.\
[https://www.home-assistant.io/components/workday/](https://www.home-assistant.io/components/workday/)
- country, province 는 빠지고 service_key 가 추가되었습니다.
- add_holidays 의 날짜 형식은 `YYYYMMDD` 형식으로 변경되었습니다.
- lovelace 카드를 함께 사용하려면 input_text 엔티티도 하나 추가해주세요.

**Example configuration.yaml:**
```yaml
binary_sensor:
  - platform: korean_workday
    service_key: 'data.go.kr api key'
    add_holidays:
      - 20190501
    remove_holidays:
      - 20221218

input_text:
  holiday:
    name: Holiday
    max: 255
```
<br>

**Configuration variables:**

|옵션|값|
|--|--|
|platform| (필수) korean_workday |
|name| (옵션) 센서 이름. 미설정시 기본값은 'korean_workday' |
|service_key| (옵션) data.go.kr 서비스키 |
|add_holidays| (옵션) 휴일로 추가할 날짜 리스트 'YYYMMDD' 형식<br>주의! YYYY-MM-DD가 아님 |
|remove_holidays| (옵션) 휴일에서 제거할 날짜 리스트 'YYYMMDD' 형식<br>주의! YYYY-MM-DD가 아님 |
|workdays| (옵션) 근무일 리스트. 미설정시 기본값은 [mon, tue, wed, thu, fri] |
|excludes| (옵션) 휴일 리스트. 미설정시 기본값은 [sat, sun, holiday] |
|days_offset| (옵션) Set days offset (e.g., -1 for yesterday, 1 for tomorrow) |
|shopping_list| (옵션) 장보기목록 사용여부. 기본값은 false |

<br>

## Full example

기본 설정으로 사용하기 (주말과 공휴일만 쉴 경우)
```yaml
# Example configuration.yaml entry
binary_sensor:
  - platform: korean_workday
```
<br>

월화수목 주4일 근무(부럽..)하고 custom 휴일을 추가한 예

```yaml
# Example configuration.yaml entry
binary_sensor:
  - platform: korean_workday
    service_key: 'i1FinzgGkT7FPB...'
    workdays: [mon, tue, wed, thu]
    excludes: [fri, sat, sun, holiday]
    add_holidays:
      - '20190501'
      - '20190607'
      - '20190610'
```
<br>

## Automation example
자동화 예제

```yaml
automation:
  alias: Turn on heater on workdays
  trigger:
    platform: time
    at: '08:00:00'
  condition:
    condition: state
    entity_id: 'binary_sensor.korean_workday'
    state: 'on'
  action:
    service: switch.turn_on
    entity_id: switch.heater
```
<br>

## 버그 또는 문의사항
네이버 카페 [HomeAssistant](https://cafe.naver.com/koreassistant/) `그렉하우스` \
네이버 카페 [모두의 스마트홈](https://cafe.naver.com/stsmarthome/) `그렉하우스`
