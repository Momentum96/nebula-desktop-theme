# nebula-desktop-theme

Herdr 앱과 Discord(Vencord)를 같은 네뷸라 배경, 보라 포인트, Monoplex KR Nerd Font 서체로 맞추는 개인 테마입니다.
다른 PC에서는 아래 "AI 에이전트 적용 절차"를 에이전트에게 그대로 시키면 됩니다.

## 들어 있는 것

| 경로 | 내용 |
|---|---|
| `herdr/layouts/main-nebula.json` | Herdr 레이아웃. 기본 `main`(0.1.16)을 복제해 창 전체에 배경 이미지를 `cover`로 깔고 터미널 배경을 투명(`terminal_opacity: 0`)하게 둠 |
| `herdr/backgrounds/nebula-1536x1024.png` | 배경 이미지 원본 |
| `herdr/themes/dracula.json` | Herdr 색 테마(Herdr에 이미 있으면 건드리지 않음) |
| `herdr/settings.theme.json` | Herdr `settings.json`에 합칠 항목: 서체, 크기, dark, dracula |
| `discord/theme.src.css` | Discord 테마 원본. 배경 자리는 `__NEBULA_BG_DATA_URI__` |
| `discord/nebula-bg.jpg` | Discord용 배경(원본 PNG를 JPEG로 줄인 것) |
| `discord/nowaywork.theme.css` | 실제로 넣는 완성본(배경이 data URI로 들어 있음). 파일 이름은 처음 만들 때 이름을 그대로 씀 |
| `scripts/apply.py` | 적용 스크립트(파이썬 표준 라이브러리만 사용) |
| `scripts/build_discord_theme.py` | `theme.src.css` + `nebula-bg.jpg` → `nowaywork.theme.css` |

Discord 테마 요약: 배경은 네뷸라 이미지 위에 검정 30%, 포인트는 보라 `#A97BFF`(호버 `#BC97FF`, 누름 `#9161F0`, 버튼 글자 흰색), 상태색(온라인, 성공)은 초록 `#57D98B`, 경고 `#FFD75D`, 오류 `#FF5D5D`, 서체는 전부 Monoplex KR Nerd Font, 글자에 옅은 그림자.

## 사전 조건

- Python 3.9 이상
- 서체 **Monoplex KR Nerd Font**: https://github.com/y-kim/monoplex 릴리스 `monoplex-kr-nerd-font-1.3.0`(Latest인 CJK판이 아님)의 `MonoplexKRNerdFont_v1.3.0.zip` 안에 있는 `MonoplexKRNerdFont-*.ttf`를 설치합니다.
  - 패밀리 이름은 `Monoplex KR Nerd Font`입니다. 예전 버전(0.0.x, 패밀리 `Monoplex KR Nerd`)이 깔려 있으면 지우고, 그 이름을 쓰는 다른 앱 설정도 새 이름으로 바꿉니다.
  - macOS: `~/Library/Fonts/`에 복사
  - Linux: `~/.local/share/fonts/`에 복사 후 `fc-cache -f`
  - Windows: 각 ttf를 "모든 사용자용으로 설치" 또는 `%LOCALAPPDATA%\Microsoft\Windows\Fonts`에 설치
  - 확인: macOS `system_profiler SPFontsDataType | grep "Family: Monoplex KR Nerd" | sort -u`, Linux `fc-list : family | grep "Monoplex KR Nerd" | sort -u`
- Herdr 앱: 한 번 실행해서 `~/.config/herdr-app`(또는 `HERDR_APP_HOME`)이 있어야 합니다.
- Discord + Vencord: Vencord가 설치되어 있고 Discord를 한 번 실행했어야 합니다. 설정 폴더는
  - macOS `~/Library/Application Support/Vencord`
  - Linux `~/.config/Vencord`(`XDG_CONFIG_HOME` 반영)
  - Windows `%APPDATA%\Vencord`
  - Vesktop은 폴더 구조가 다르므로 이 스크립트 대상이 아닙니다.

## AI 에이전트 적용 절차

에이전트는 이 순서를 지키고, 각 단계의 확인 결과를 사람에게 보고합니다.

1. 이 저장소를 클론하고 루트로 이동합니다.
2. 서체가 설치되어 있는지 확인하고, 없으면 위 "사전 조건"대로 설치합니다.
3. 바꿀 내용을 먼저 확인합니다: `python3 scripts/apply.py --dry-run`
   - Herdr나 Vencord 폴더를 못 찾으면 여기서 멈추고 사람에게 알립니다.
4. Herdr 적용: `python3 scripts/apply.py --only herdr`
   - 레이아웃, 배경, 설정은 Herdr가 바로 다시 읽습니다(재시작 불필요).
   - `herdr-app`가 PATH에 있으면 스크립트가 `herdr-app do layout.switch '{"name":"main-nebula"}'`로 레이아웃을 바꿉니다. 없으면 앱에서 `ctrl-shift-l`로 `main-nebula`를 고르라고 사람에게 안내합니다.
   - 확인: `herdr-app shot herdr.png`로 창을 캡처해 배경 이미지가 보이는지 봅니다(화면 녹화 권한 불필요).
5. Discord 적용: **Discord를 완전히 종료한 뒤**(macOS는 Cmd+Q) `python3 scripts/apply.py --only discord`를 실행하고 Discord를 다시 켭니다.
   - Vencord는 설정을 메모리에 들고 있어서, Discord가 켜진 채로 설정 파일을 고치면 반영되지 않고 나중에 덮어써질 수 있습니다.
   - 사람이 Discord를 쓰고 있으면 종료 전에 반드시 허락을 받습니다.
   - 확인: Discord 설정 → Vencord → Themes에서 `NOWAYWORK`가 켜져 있는지, 채팅 화면에 네뷸라 배경과 보라 멘션이 보이는지 봅니다.
6. 바꾼 파일은 모두 같은 폴더에 `*.bak-<시각>`으로 백업되어 있습니다. 되돌릴 때는 그 파일을 원래 이름으로 복사합니다.

`apply.py`는 여러 번 실행해도 안전합니다. 같은 파일은 `same`으로 건너뛰고, `settings.json`은 덮어쓰지 않고 테마 항목만 합칩니다(줌, 소리, 기기별 값은 유지).

## 운영체제별 차이

- macOS: Vencord `transparent: true`, `macosVibrancyStyle: fullscreen-ui`(원래 맥북과 같은 값). 배경 이미지가 창을 덮으므로 블러는 사실상 보이지 않습니다. 시험해 본 재질 중 `sidebar`, `hud`는 탁한 회색, `under-page`, `window`는 불투명해서 쓰지 않습니다.
- Windows, Linux: `transparent: true`만 설정합니다. 배경 이미지가 창을 덮으므로 결과는 같습니다. Windows 블러(`windowsMaterial`)는 설정하지 않습니다.

## 수정하는 법

- Discord 색, 투명도: `discord/theme.src.css`를 고친 뒤 `python3 scripts/build_discord_theme.py`로 완성본을 다시 만들고 커밋합니다. 검정 농도는 `--nww-glass`(현재 `rgba(5, 5, 5, 0.3)`)입니다.
- 배경 이미지 교체: `herdr/backgrounds/`에 새 이미지를 넣고 `main-nebula.json`의 `background.image`를 바꿉니다. Discord용은 같은 이미지를 JPEG(가로 1536px 안팎, 100KB 이하 권장)로 줄여 `discord/nebula-bg.jpg`에 덮어쓴 뒤 빌드합니다. Vencord는 외부 URL 이미지를 막으므로 data URI로 넣는 이 방식을 유지합니다.
- Vencord 테마 페이지의 성능 경고대로 `:has()` 선택자는 쓰지 않습니다.

## 알려진 점

- `main-nebula`는 Herdr 0.1.16의 `main`을 복제한 것입니다. Herdr가 크게 바뀌어 레이아웃이 깨지면, 최신 `main`을 `herdr-app do layout.clone '{"name":"main","as":"main-nebula"}'`로 다시 복제한 뒤 이 파일의 `background`, `terminal_opacity`, `terminal_padding`, `divider`, `titlebar`, `traffic_lights`, `work-body`의 `pane` 값을 옮깁니다.
- Discord 화면 확인용으로 창만 따로 캡처하면(macOS Cmd+Shift+4 → 스페이스) 창 뒤가 빠져서 실제와 다르게 보일 수 있습니다. 영역이나 전체 화면 캡처로 확인합니다.
