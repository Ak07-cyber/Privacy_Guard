# Collected Parameters Documentation

This document describes all environmental and behavioral parameters collected by PassiveGuard for bot detection.

## Environmental Parameters

### Browser Information

| Parameter | Description | Bot Indicator |
|-----------|-------------|---------------|
| `userAgent` | Browser user agent string | Headless browsers have distinct patterns |
| `language` | Browser language setting | Bots often have minimal language settings |
| `languages` | Array of accepted languages | Bots typically have single language |
| `platform` | Operating system platform | Unusual platforms may indicate bots |
| `vendor` | Browser vendor | Can identify headless browsers |
| `cookiesEnabled` | Cookie support | Disabled cookies may indicate bot |
| `doNotTrack` | DNT header value | Informational |
| `plugins` | Browser plugins list | Bots typically have no plugins |
| `mimeTypes` | Supported MIME types | Reduced in headless browsers |

### Screen Information

| Parameter | Description | Bot Indicator |
|-----------|-------------|---------------|
| `width` / `height` | Screen dimensions | Unusual dimensions indicate VM/headless |
| `availWidth` / `availHeight` | Available screen area | Should differ from full dimensions |
| `colorDepth` | Color bit depth | Usually 24 or 32 for normal browsers |
| `pixelDepth` | Pixel depth | Should match colorDepth |
| `devicePixelRatio` | Display scaling | Unusual values indicate emulation |
| `orientation` | Screen orientation | Usually present on mobile |

### Hardware Information

| Parameter | Description | Bot Indicator |
|-----------|-------------|---------------|
| `hardwareConcurrency` | CPU cores | Very low values indicate VM |
| `deviceMemory` | RAM in GB | Very low values indicate VM |
| `maxTouchPoints` | Touch support | Desktop bots lack touch |
| `hasTouch` | Touch event support | Desktop bots lack touch |
| `hasPointer` | Pointer event support | Usually true |

### WebGL Information

| Parameter | Description | Bot Indicator |
|-----------|-------------|---------------|
| `vendor` | GPU vendor | "Google SwiftShader" indicates headless |
| `renderer` | GPU renderer | Software renderers indicate headless |
| `version` | WebGL version | Should be present |
| `shadingLanguageVersion` | GLSL version | Should be present |
| `extensions` | WebGL extensions | Reduced in headless browsers |
| `hash` | Combined hash | Fingerprint for consistency |

### Fingerprints

| Parameter | Description | Bot Indicator |
|-----------|-------------|---------------|
| `canvasHash` | Canvas fingerprint hash | Missing indicates canvas blocking |
| `audioHash` | Audio context hash | Missing indicates audio blocking |
| `webglHash` | WebGL combined hash | Missing indicates WebGL issues |

### Timezone Information

| Parameter | Description | Bot Indicator |
|-----------|-------------|---------------|
| `offset` | UTC offset in minutes | Mismatched with IP geolocation |
| `timezone` | IANA timezone name | Should be consistent |
| `isDST` | Daylight saving status | Should match timezone |

### Feature Detection

| Parameter | Description | Bot Indicator |
|-----------|-------------|---------------|
| `webdriver` | Navigator.webdriver flag | **TRUE = BOT DETECTED** |
| `automationFlags` | Automation tool indicators | **ANY = HIGHLY SUSPICIOUS** |
| `localStorage` | Local storage support | Missing is suspicious |
| `sessionStorage` | Session storage support | Missing is suspicious |
| `indexedDB` | IndexedDB support | Missing is suspicious |
| `webSocket` | WebSocket support | Should be present |
| `webWorker` | Web Worker support | Should be present |
| `serviceWorker` | Service Worker support | Usually present in modern browsers |

---

## Behavioral Parameters

### Mouse Movement Data

| Parameter | Description | Bot Indicator |
|-----------|-------------|---------------|
| `movements` | Array of movement points | No movements = suspicious |
| `totalDistance` | Total pixels traveled | Very low = suspicious |
| `averageVelocity` | Average movement speed | Too consistent = bot |
| `maxVelocity` | Maximum movement speed | Very close to average = bot |
| `straightLineRatio` | Path efficiency | >0.95 = perfectly straight = bot |
| `directionChanges` | Number of direction changes | Very few = bot |
| `pauseCount` | Number of pauses | None = bot |
| `jitterScore` | Micro-movement score | Zero = unnaturally smooth = bot |

#### Velocity Analysis

Human mouse movements have:
- Variable velocity with acceleration/deceleration
- Natural curves and overshoots
- Micro-corrections and jitter
- Pauses for thinking

Bot mouse movements have:
- Constant velocity
- Perfectly straight paths
- No micro-movements
- No hesitation

### Click Data

| Parameter | Description | Bot Indicator |
|-----------|-------------|---------------|
| `x`, `y` | Click coordinates | All same location = bot |
| `timestamp` | Click timing | Perfect intervals = bot |
| `button` | Mouse button used | Always 0 = suspicious |
| `target` | Clicked element | Missing = suspicious |

### Keyboard Data

| Parameter | Description | Bot Indicator |
|-----------|-------------|---------------|
| `keyPresses` | Key event count | None with form = suspicious |
| `averageDwellTime` | Key hold duration | Too consistent = bot |
| `averageFlightTime` | Time between keys | Too consistent = bot |
| `typingSpeed` | Keys per minute | Extremely fast = bot |
| `errorRate` | Backspace/delete ratio | Zero errors = suspicious |
| `rhythmConsistency` | Timing variance | >0.99 = perfectly consistent = bot |

#### Keystroke Dynamics

Human typing has:
- Variable dwell times (how long keys are pressed)
- Variable flight times (time between key presses)
- Occasional errors and corrections
- Varying rhythm based on key combinations

Bot typing has:
- Perfect consistency
- No errors
- Mechanical timing
- Unrealistic speed

### Scroll Data

| Parameter | Description | Bot Indicator |
|-----------|-------------|---------------|
| `events` | Scroll event count | Very few = suspicious |
| `totalScroll` | Total scroll distance | None with long page = suspicious |
| `averageVelocity` | Scroll speed | Too consistent = bot |
| `smoothness` | Velocity consistency | >0.99 = mechanical = bot |
| `directionChanges` | Up/down switches | None = suspicious |

### Touch Data (Mobile)

| Parameter | Description | Bot Indicator |
|-----------|-------------|---------------|
| `gestures` | Touch gesture count | None on mobile = suspicious |
| `multiTouchEvents` | Pinch/zoom count | None on mobile = suspicious |
| `averagePressure` | Touch pressure | Zero or constant = suspicious |

### Focus Data

| Parameter | Description | Bot Indicator |
|-----------|-------------|---------------|
| `focusEvents` | Focus change count | None = suspicious |
| `totalFocusTime` | Time page was focused | Very short = suspicious |
| `blurCount` | Times page lost focus | Always zero = unusual |
| `visibilityChanges` | Tab switches | None for long session = unusual |

### Timing Data

| Parameter | Description | Bot Indicator |
|-----------|-------------|---------------|
| `pageLoadTime` | Page load duration | Very fast = cached/local |
| `timeToFirstInteraction` | Time until first action | <100ms = suspicious |
| `totalInteractionTime` | Total session duration | Very short = suspicious |
| `idlePeriods` | Gaps in activity | None for long session = suspicious |
| `interactionGaps` | Time between actions | Too consistent = bot |

---

## Bot Detection Heuristics

### High Confidence Bot Indicators

1. **Webdriver flag is true** - Definitive bot indicator
2. **Automation flags present** - Tools like Selenium, Puppeteer detected
3. **No mouse movement** - Programmatic form filling
4. **Perfect straight-line mouse paths** - Non-human movement
5. **Instant first interaction** (<100ms) - Impossible for humans
6. **Zero typing errors with long text** - Unnatural
7. **Perfect rhythm consistency** (>99%) - Mechanical typing

### Medium Confidence Bot Indicators

1. **Very few plugins** - Headless browsers
2. **Missing fingerprints** - Privacy tools or headless
3. **Unusual screen dimensions** - VM or emulation
4. **Low hardware concurrency** - VM
5. **No storage support** - Incognito or headless
6. **SwiftShader WebGL** - Headless Chrome
7. **Very short session time** - Automated submission

### Low Confidence Indicators (Context Dependent)

1. **Single language** - Could be legitimate
2. **No touch support** - Could be desktop
3. **No scroll events** - Could be short page
4. **No keyboard events** - Could be click-only form

---

## Privacy Considerations

### Data Minimization

- Key content is never captured, only timing patterns
- Mouse movements are sampled, not continuous
- All fingerprints are hashed before transmission
- No PII is ever collected

### Data Anonymization

- Hashed values cannot be reversed
- No cross-site tracking
- Session data is temporary
- No permanent identifiers stored

### User Transparency

- All collection is passive
- No interaction required
- Collection can be disabled
- Privacy mode available for minimal collection
