import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ANDROID_CONFIG = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/domain/model/TimerConfig.kt"
ANDROID_REPOSITORY = ROOT / "native-android/app/src/main/java/com/iganapolsky/randomtimer/data/repository/TimerRepositoryImpl.kt"
IOS_MODELS = ROOT / "native-ios/SharedModels/TimerModels.swift"


def test_timer_defaults_match_across_mobile_platforms():
    android_config = ANDROID_CONFIG.read_text(encoding="utf-8")
    android_repository = ANDROID_REPOSITORY.read_text(encoding="utf-8")
    ios_models = IOS_MODELS.read_text(encoding="utf-8")

    assert "minSeconds = 0" in android_config
    assert "maxSeconds = 30" in android_config
    assert android_repository.count("maxSeconds = preferences[KEY_MAX_SECONDS] ?: 30") == 2
    assert re.search(r"minSeconds: Int = 0,\n\s*maxSeconds: Int = 30,", ios_models)
    assert "defaultValue: 30" in ios_models
