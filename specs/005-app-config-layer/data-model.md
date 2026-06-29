# Data Model: App Configuration Layer

**Feature**: 005-app-config-layer | **Date**: 2026-06-28

## Entita: AppConfig

Hlavný kontajner všetkých konfigurovateľných parametrov. Vždy platná hodnota — nikdy null. Immutable po načítaní.

```kotlin
// domain/model/AppConfig.kt
data class AppConfig(
    val weights: Map<String, Double>,                // 9 elementov, suma = 100
    val elementClassification: ElementClassification,
    val adaptation: AdaptationConfig,
    val asrs: AsrsConfig,
    val notification: NotificationConfig
)
```

**Validačné pravidlá**:
- `weights` — všetky hodnoty > 0; ak suma mimo (95, 105) → normalizovať; neznáme kľúče ignorovať; chýbajúce kľúče doplniť z `DefaultWeights`
- Nemôže byť null — `AppConfigLoader` vždy vráti platnú inštanciu

---

## Entita: ElementClassification

```kotlin
data class ElementClassification(
    val negativeKeys: Set<String>,   // elementy kde vyššia = horšie
    val positiveKeys: Set<String>    // odvodené: weights.keys - negativeKeys
)
```

**Odvodenie**: `positiveKeys` sa neserializuje samostatne — vypočíta sa pri načítaní ako `weights.keys - negativeKeys`.

**Fallback**: `negativeKeys = setOf("stress_work", "stress_personal", "alcohol", "caffeine")`

---

## Entita: AdaptationConfig

Parametre týždennej adaptácie váh.

```kotlin
data class AdaptationConfig(
    val alpha: Double,               // koeficient učenia; rozsah (0, 1]; default 0.2
    val clampMinFactor: Double,      // min váha = factor * defaultWeight; default 0.5
    val clampMaxFactor: Double,      // max váha = factor * defaultWeight; default 2.0
    val correlationThreshold: Double,// min |corr| pre zmenu váhy; default 0.1
    val minHistoryDays: Int,         // min zápisov v histórii; default 15
    val minSeriesSize: Int           // min počet hodnôt pre Pearson; default 5
)
```

**Validačné pravidlá**:
- `alpha`: musí byť v (0.0, 1.0]; inak → 0.2
- `clampMinFactor` < `clampMaxFactor`; inak obaja → 0.5, 2.0
- `correlationThreshold` > 0; inak → 0.1
- `minHistoryDays` ≥ 1; inak → 15
- `minSeriesSize` ≥ 1; inak → 5

---

## Entita: AsrsConfig

Parametre ASRS re-kalibrácie.

```kotlin
data class AsrsConfig(
    val deltaThreshold: Double,         // bodová odchýlka triggera; default 10.0
    val consecutiveMeasurements: Int,   // počet po sebe idúcich meraní; default 2
    val recalibrationAlpha: Double      // zvýšený alpha na 1 cyklus; default 0.3
)
```

**Validačné pravidlá**:
- `deltaThreshold` > 0; inak → 10.0
- `consecutiveMeasurements` ≥ 1; inak → 2
- `recalibrationAlpha` > 0 a ≤ 1; inak → 0.3

---

## Entita: NotificationConfig

Notifikačné prahy a tichý interval.

```kotlin
data class NotificationConfig(
    val quietStartHour: Int,         // hod; rozsah 0-23; default 22
    val quietStartMinute: Int,       // min; rozsah 0-59; default 0
    val quietEndHour: Int,           // hod; rozsah 0-23; default 8
    val quietEndMinute: Int,         // min; rozsah 0-59; default 0
    val stressThresholdScale: Int,   // min scale hodnota pre "vysoký stres"; default 4
    val neglectedAreaDays: Int,      // počet dní bez aktivity = "zanedbané"; default 3
    val stressRecoveryDays: Int      // počet po sebe idúcich dní stres+no-mindfulness; default 3
)
```

**Validačné pravidlá**:
- `quietStartHour`, `quietEndHour`: 0-23; inak → defaults
- `quietStartMinute`, `quietEndMinute`: 0-59; inak → 0
- `stressThresholdScale`: 1-5; inak → 4
- `neglectedAreaDays` ≥ 1; inak → 3
- `stressRecoveryDays` ≥ 1; inak → 3

---

## Trieda: AppConfigLoader

Načítava JSON a mapuje na `AppConfig`. Patrí do `data/` vrstvy (má Android dep na `AssetManager`).

```kotlin
// data/AppConfigLoader.kt
object AppConfigLoader {
    fun load(assetManager: AssetManager): AppConfig =
        load(runCatching { assetManager.open("app_config.json") }.getOrNull())

    fun load(stream: InputStream?): AppConfig {
        // parsuj JSON; aplikuj fallback; loguj audit
        // vracia vždy platnú AppConfig
    }
}
```

**State transitions**:
```
stream = null          → FALLBACK_ALL    → log: "config not found, using defaults"
stream, invalid JSON   → FALLBACK_ALL    → log: "config parse error: <msg>, using defaults"
stream, partial JSON   → MERGE           → log per param: "loaded from config" | "missing, using default"
stream, invalid value  → FALLBACK_PARAM  → log: "invalid value for X (<val>), using default <def>"
stream, valid JSON     → LOADED          → log: "config loaded successfully"
```

---

## Zmeny existujúcich tried (nie nové entity)

| Trieda | Zmena |
|--------|-------|
| `DefaultWeights` | Zostáva — stane sa zdrojom fallback konštánt; `weights` a `negativeKeys` sú `val` bez zmeny |
| `IndexCalculator.adaptWeights` | Parametre `alpha`, clamp limity, prahy presunúť z default args do explicitných parametrov; volajúci (Repository) dodá z `AppConfig` |
| `AsrsRecalibrator` | `shouldRecalibrate()` + `alphaForRecalibration()` prijmú `AsrsConfig` param namiesto hardcoded hodnôt |
| `NotificationRules` | `object` → `class(private val config: AppConfig.NotificationConfig)` + `elementKeys: Set<String>` parameter pre `neglectedArea()` namiesto `DefaultWeights.weights.keys` |
| `TrackerRepository` | Pridať `private val appConfig: AppConfig` konštruktor param; odstrániť priame referencie na `DefaultWeights.*` — použiť `appConfig.elementClassification` a `appConfig.adaptation` |
| `MainActivity.AppRoot` | Pridať `val appConfig = remember { AppConfigLoader.load(context.assets) }` pred `repository`; aktualizovať `TrackerRepository(db, appConfig)` |
