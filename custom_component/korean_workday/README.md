# Korean Workday Binary Sensor

[![License][license-shield]](LICENSE.md)
![Project Maintenance][maintenance-shield1]


현재 날짜가 일하는날인지의 여부를 나타냅니다. \
파이썬의 holidays 모듈을 사용하는 HA의 workday 센서가 한국 휴일을 지원하지 않기 때문에, 공공데이터포털의 휴일 API를 이용하는 커스텀 컴포넌트를 만들었습니다.

## Inatallation

- HA 설치 경로 아래 custom_component 에 파일을 넣어줍니다. `<config directory>/custom_components/korean_workday/binary_sensor.py`
- configuration.yaml 파일에 설정을 추가합니다.
- Home-Assistant 를 재시작합니다.

## Usage

### OPEN API 이용하기 (옵션)
- 하루에 한 번 API 호출을 통해 휴일 목록을 가져옵니다.
- 공공데이터포털에서 서비스키를 발급받아야 합니다.\
[특일정보 활용신청](https://www.data.go.kr/dataset/15012690/openapi.do)
- 근로자의 날 5월 1일은 공휴일이 아니라고 합니다. add_holidays에 추가하세요.
- API 사용을 하지 않으려면 add_holidays 항목에 휴일 목록을 수작업으로 모두 넣어주면 됩니다.


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
**Configuration variables:**
key | description
:--- | :---
**platform** _(필수)_ | korean_workday
**name** _(옵션)_ | 센서 이름
**service_key** _(옵션)_ | data.go.kr 서비스키
**add_holidays** _(옵션)_ | 휴일로 추가할 날짜 리스트 <br>`- YYYYMMDD` 형식<br> **(주의) YYYY-MM-DD가 아님**
**workdays** _(옵션)_ | workday 요일 리스트 <br>_Default value: [mon, tue, wed, thu, fri]_
**excludes** _(옵션)_ | 휴일 리스트 <br>_Default value: [sat, sun, holiday]_
**days_offset** _(옵션)_ | Set days offset<br>_(e.g., -1 for yesterday, 1 for tomorrow)_


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

## 버그 또는 문의사항
네이버 카페 [SmartThings&IoT Home](https://cafe.naver.com/stsmarthome/) 에서 ID **그레고리하우스**를 찾아주세요.


