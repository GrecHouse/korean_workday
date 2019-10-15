# Korean Workday Binary Sensor



현재 날짜가 일하는날인지의 여부를 나타냅니다. \
파이썬의 holidays 모듈을 사용하는 HA의 workday 센서가 한국 휴일을 지원하지 않기 때문에, 공공데이터포털의 휴일 API를 이용하는 커스텀 컴포넌트를 만들었습니다.

<br>

## Installation

- HA 설치 경로 아래 custom_component 에 파일을 넣어줍니다.
<br>`<config directory>/custom_components/korean_workday/binary_sensor.py`
<br>`<config directory>/custom_components/korean_workday/__init__.py`
<br>`<config directory>/custom_components/korean_workday/manifest.json`
- configuration.yaml 파일에 설정을 추가합니다.
- Home Assistant 를 재시작합니다.

<br>

## Usage

### OPEN API 이용하기 (옵션)
- 하루에 한 번 API 호출을 통해 휴일 목록을 가져옵니다.
- 공공데이터포털에서 서비스키를 발급받아야 합니다.\
[특일정보 활용신청](https://www.data.go.kr/dataset/15012690/openapi.do)
- 근로자의 날 5월 1일은 공휴일이 아니라고 합니다. add_holidays에 추가하세요.
- API 사용을 하지 않으려면 add_holidays 항목에 휴일 목록을 수작업으로 모두 넣어주면 됩니다.

<br>

### 장보기목록(Shopping List) 이용하기
- 갑작스런 휴가 등으로 인해 휴일 추가가 필요한 경우 HA 의 장보기목록 기능을 이용할 수 있습니다.
- 설정 변경 후 재시작할 필요가 없습니다!
- 장보기목록에 `#YYYYMMDD` 형식으로 날짜를 넣으면 휴일로 추가됩니다.
- 장보기목록에서 완료처리(체크) 하면 휴일에서 제거됩니다.
- 당일 휴일 등록 또는 완료(체크)시 센서값 변경까지 최대 30분 정도 소요될 수 있습니다.
- (주의) 당일 휴일 삭제는 장보기목록에서 체크한 상태에서 센서값이 변경된 것을 확인한 다음 삭제하세요.

<br>

### configuration
- 기본적인 설정은 HA의 workday 센서 설정과 동일합니다.\
[https://www.home-assistant.io/components/workday/](https://www.home-assistant.io/components/workday/)
- country, province 는 빠지고 service_key 가 추가되었습니다.
- add_holidays 의 날짜 형식은 `YYYYMMDD` 형식으로 변경되었습니다.

**Example configuration.yaml:**
```yaml
binary_sensor:
  - platform: korean_workday
    service_key: 'data.go.kr api key'
    add_holidays:
      - '20190501'
```
<br>

**Configuration variables:**

|옵션|값|
|--|--|
|platform| (필수) korean_workday |
|name| (옵션) 센서 이름. 미설정시 기본값은 'korean_workday' |
|service_key| (옵션) data.go.kr 서비스키 |
|add_holidays| (옵션) 휴일로 추가할 날짜 리스트 'YYYMMDD' 형식<br>주의! YYYY-MM-DD가 아님 |
|workdays| (옵션) 근무일 리스트. 미설정시 기본값은 [mon, tue, wed, thu, fri] |
|excludes| (옵션) 휴일 리스트. 미설정시 기본값은 [sat, sun, holiday] |
|days_offset| (옵션) Set days offset (e.g., -1 for yesterday, 1 for tomorrow) |

<br>

## Full example
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
네이버 카페 [SmartThings&IoT Home](https://cafe.naver.com/stsmarthome/) ID **그레고리하우스**


