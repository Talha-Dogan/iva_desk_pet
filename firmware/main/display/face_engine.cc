#include "face_engine.h"

#include <esp_log.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>

#define TAG "FaceEngine"

namespace {

inline float Ease(float current, float target, float k) {
    return current + (target - current) * k;
}

inline float Clampf(float v, float lo, float hi) {
    return v < lo ? lo : (v > hi ? hi : v);
}

}  // namespace

void FaceEngine::Init(lv_obj_t* parent) {
    container_ = lv_obj_create(parent);
    lv_obj_set_size(container_, 128, 64);
    lv_obj_set_style_border_width(container_, 0, 0);
    lv_obj_set_style_bg_opa(container_, LV_OPA_TRANSP, 0);
    lv_obj_set_style_pad_all(container_, 0, 0);
    lv_obj_set_scrollbar_mode(container_, LV_SCROLLBAR_MODE_OFF);
    lv_obj_center(container_);

    left_eye_ = lv_obj_create(container_);
    right_eye_ = lv_obj_create(container_);
    left_cheek_ = lv_obj_create(container_);
    right_cheek_ = lv_obj_create(container_);
    left_brow_ = lv_obj_create(container_);
    right_brow_ = lv_obj_create(container_);
    mouth_ = lv_obj_create(container_);

    // On this monochrome OLED black is the LIT pixel, so the facial features
    // are black (glowing) and everything else stays white (pixels off).
    lv_obj_t* features[] = {left_eye_, right_eye_, mouth_};
    for (auto obj : features) {
        lv_obj_set_style_bg_color(obj, lv_color_black(), 0);
        lv_obj_set_style_border_width(obj, 0, 0);
        lv_obj_set_scrollbar_mode(obj, LV_SCROLLBAR_MODE_OFF);
    }

    // Cheeks and brows carve shapes out of the eyes, so they use the "off" color.
    lv_obj_t* carvers[] = {left_cheek_, right_cheek_, left_brow_, right_brow_};
    for (auto obj : carvers) {
        lv_obj_set_style_bg_color(obj, lv_color_white(), 0);
        lv_obj_set_style_border_width(obj, 0, 0);
        lv_obj_set_style_radius(obj, 8, 0);
        lv_obj_set_scrollbar_mode(obj, LV_SCROLLBAR_MODE_OFF);
        lv_obj_add_flag(obj, LV_OBJ_FLAG_HIDDEN);
    }

    zzz_label_ = lv_label_create(container_);
    lv_label_set_text(zzz_label_, "z");
    lv_obj_set_style_text_color(zzz_label_, lv_color_black(), 0);
    lv_obj_add_flag(zzz_label_, LV_OBJ_FLAG_HIDDEN);

    uint32_t now = lv_tick_get();
    next_saccade_ms_ = now + 1500;
    next_happy_ms_ = now + 6000;

    lv_timer_create(
        [](lv_timer_t* t) {
            auto face = static_cast<FaceEngine*>(lv_timer_get_user_data(t));
            face->Update();
        },
        40, this);
}

void FaceEngine::SetState(FaceState state) {
    if (state == FaceState::Sleeping) {
        Sleep();
        return;
    }
    if (sleeping_) {
        // Real sleep: no state change wakes the face. Not even the assistant's
        // own "ok, going to sleep" reply. Only the wake word (or the wake_up
        // tool) opens the eyes again.
        return;
    }
    if (state_ == FaceState::Idle && state == FaceState::Listening) {
        stretch_ = 0.45f;  // little surprise pop when the wake word lands
    }
    if (state_ != state && state == FaceState::Speaking) {
        speak_next_ms_ = 0;
    }
    state_ = state;
}

void FaceEngine::RequestSleep() {
    if (sleeping_) {
        return;
    }
    pending_sleep_ = true;
    pending_speech_seen_ = false;
    pending_sleep_ms_ = lv_tick_get();
    ESP_LOGI(TAG, "Sleep requested, waiting for the goodnight to finish");
}

void FaceEngine::Sleep() {
    pending_sleep_ = false;
    if (sleeping_) {
        return;
    }
    sleeping_ = true;
    state_ = FaceState::Sleeping;
    zzz_step_ = 0;
    zzz_next_ms_ = lv_tick_get() + 600;
    zzz_end_ms_ = lv_tick_get() + 6000;  // z z z only for the first ~6 seconds
    ESP_LOGI(TAG, "Face going to sleep");
}

void FaceEngine::WakeUp() {
    if (!sleeping_) {
        return;
    }
    sleeping_ = false;
    pending_sleep_ = false;
    state_ = FaceState::Idle;
    stretch_ = 1.0f;  // big stretch blink on wake-up
    ESP_LOGI(TAG, "Face waking up");
}

void FaceEngine::SetEmotion(const char* emotion) {
    if (emotion == nullptr) {
        return;
    }
    struct Map { const char* name; FaceEmotion value; };
    static const Map kMap[] = {
        {"happy", FaceEmotion::Happy},         {"laughing", FaceEmotion::Happy},
        {"funny", FaceEmotion::Happy},         {"delicious", FaceEmotion::Happy},
        {"confident", FaceEmotion::Happy},     {"cool", FaceEmotion::Happy},
        {"relaxed", FaceEmotion::Happy},       {"silly", FaceEmotion::Happy},
        {"sad", FaceEmotion::Sad},             {"crying", FaceEmotion::Sad},
        {"embarrassed", FaceEmotion::Sad},     {"angry", FaceEmotion::Angry},
        {"surprised", FaceEmotion::Surprised}, {"shocked", FaceEmotion::Surprised},
        {"thinking", FaceEmotion::Thinking},   {"sleepy", FaceEmotion::Sleepy},
        {"winking", FaceEmotion::Winking},     {"kissy", FaceEmotion::Winking},
        {"loving", FaceEmotion::Loving},       {"confused", FaceEmotion::Confused},
        {"neutral", FaceEmotion::Neutral},
    };

    FaceEmotion found = FaceEmotion::Neutral;
    for (const auto& m : kMap) {
        if (strcmp(emotion, m.name) == 0) {
            found = m.value;
            break;
        }
    }
    // Hemen uygulama: once sabitlenmesini bekle (gecici sinyalleri suz)
    pending_emotion_ = found;
    has_pending_emotion_ = true;
    pending_emotion_ms_ = lv_tick_get();
    ESP_LOGI(TAG, "Face emotion (beklemede): %s", emotion);
}

void FaceEngine::ApplyEmotion() {
    if (sleeping_) {
        return;
    }
    uint32_t now = lv_tick_get();
    if (emotion_ != FaceEmotion::Neutral && now > emotion_until_ms_) {
        emotion_ = FaceEmotion::Neutral;
    }

    switch (emotion_) {
        case FaceEmotion::Happy:
            t_cheek_ = 0.62f;
            t_eye_h_scale_ *= 1.05f;
            if (state_ != FaceState::Speaking) {
                t_mouth_w_ = 22;
                t_mouth_h_ = 8;
            }
            break;

        case FaceEmotion::Loving:
            t_cheek_ = 0.7f;
            t_eye_w_scale_ *= 1.12f;
            if (state_ != FaceState::Speaking) {
                t_mouth_w_ = 20;
                t_mouth_h_ = 10;
            }
            break;

        case FaceEmotion::Sad:
            t_brow_ = 0.55f;
            brow_dir_ = -1;  // carve the outer corners -> drooping look
            t_gaze_y_ = 3;  // mutlak deger: += kullanilirsa her karede birikip
                            // yuzu ekran disina kaydirir
            t_eye_h_scale_ *= 0.9f;
            if (state_ != FaceState::Speaking) {
                t_mouth_w_ = 10;
                t_mouth_h_ = 3;
            }
            break;

        case FaceEmotion::Angry:
            t_brow_ = 0.6f;
            brow_dir_ = 1;  // carve the inner corners -> frowning look
            t_eye_h_scale_ *= 0.85f;
            t_eye_w_scale_ *= 1.05f;
            mouth_shape_ = 1;
            if (state_ != FaceState::Speaking) {
                t_mouth_w_ = 20;
                t_mouth_h_ = 3;
            }
            break;

        case FaceEmotion::Surprised:
            t_eye_h_scale_ *= 1.35f;
            t_eye_w_scale_ *= 1.15f;
            mouth_shape_ = 2;
            if (state_ != FaceState::Speaking) {
                t_mouth_w_ = 14;
                t_mouth_h_ = 14;
            }
            break;

        case FaceEmotion::Thinking:
            t_gaze_x_ = -5;
            t_gaze_y_ = -4;
            t_brow_ = 0.3f;
            brow_dir_ = 1;
            if (state_ != FaceState::Speaking) {
                t_mouth_w_ = 10;
                t_mouth_h_ = 3;
            }
            break;

        case FaceEmotion::Confused:
            t_gaze_x_ = 4;
            t_eye_h_scale_ *= 1.1f;
            t_brow_ = 0.25f;
            brow_dir_ = -1;
            break;

        case FaceEmotion::Sleepy:
            t_lid_ = 0.55f;
            t_gaze_y_ = 2;  // mutlak deger (bkz. Sad)
            break;

        case FaceEmotion::Winking:
            t_wink_ = 1.0f;
            t_cheek_ = 0.5f;
            break;

        case FaceEmotion::Neutral:
        default:
            break;
    }
}

void FaceEngine::ComputeTargets() {
    uint32_t now = lv_tick_get();
    // Emotion modifiers are re-applied every frame on top of the state values.
    t_brow_ = 0;
    t_wink_ = 0;
    mouth_shape_ = 0;

    switch (state_) {
        case FaceState::Sleeping:
            t_lid_ = 0.93f;
            t_gaze_x_ = 0;
            t_gaze_y_ = 3;
            t_eye_h_scale_ = 1.0f;
            t_eye_w_scale_ = 1.0f;
            t_mouth_h_ = 0;
            t_cheek_ = 0;
            break;

        case FaceState::Listening:
            t_lid_ = 0;
            t_eye_h_scale_ = 1.18f;
            t_eye_w_scale_ = 1.04f;
            t_gaze_x_ = 0;
            t_gaze_y_ = -2;
            t_mouth_w_ = 9;
            t_mouth_h_ = 3;
            t_cheek_ = 0;
            break;

        case FaceState::Speaking: {
            t_lid_ = 0;
            t_eye_h_scale_ = 1.0f;
            t_eye_w_scale_ = 1.0f;
            // Lip-sync: follow the real audio level. If no PCM reached the
            // speaker in the last 220 ms the mouth rests closed, so it never
            // starts moving before the sound actually comes out.
            bool audio_fresh = (now - audio_last_ms_) < 220;
            if (audio_fresh) {
                float level = audio_level_;
                // Agiz acilirken hafifce daralir (gercek agiz gibi): yuksek
                // hecede "o", sessizlikte yatay cizgi.
                t_mouth_h_ = 2.0f + level * 11.0f;
                t_mouth_w_ = 19.0f - level * 4.0f;
            } else {
                t_mouth_h_ = 2;
                t_mouth_w_ = 19;
            }
            t_gaze_y_ = -1 + mouth_h_ * 0.06f;
            if (now >= next_happy_ms_) {
                next_happy_ms_ = now + 8000 + (rand() % 12000);
                happy_until_ms_ = now + 900;
            }
            t_cheek_ = (now < happy_until_ms_) ? 0.55f : 0.0f;
            break;
        }

        case FaceState::Idle:
        default:
            t_lid_ = 0;
            t_eye_h_scale_ = 1.0f;
            t_eye_w_scale_ = 1.0f;
            t_mouth_w_ = 16;
            t_mouth_h_ = 5;
            if (now >= next_saccade_ms_) {
                next_saccade_ms_ = now + 1200 + (rand() % 2800);
                t_gaze_x_ = (float)((rand() % 13) - 6);
                t_gaze_y_ = (float)((rand() % 5) - 2);
                if (rand() % 4 == 0) {  // sometimes look back to center
                    t_gaze_x_ = 0;
                    t_gaze_y_ = 0;
                }
            }
            if (now >= next_happy_ms_) {
                next_happy_ms_ = now + 15000 + (rand() % 20000);
                happy_until_ms_ = now + 1100;
            }
            t_cheek_ = (now < happy_until_ms_) ? 0.5f : 0.0f;
            break;
    }

    ApplyEmotion();

    // Guvenlik siniri: hangi ifade gelirse gelsin yuz ekran disina cikamaz
    t_gaze_x_ = Clampf(t_gaze_x_, -8.0f, 8.0f);
    t_gaze_y_ = Clampf(t_gaze_y_, -6.0f, 6.0f);
}

void FaceEngine::ApplyGeometry() {
    uint32_t now = lv_tick_get();
    float tsec = now / 1000.0f;

    // Curiosity: the eye on the side we look toward opens slightly wider
    float lean = Clampf(gaze_x_ / 6.0f, -1.0f, 1.0f);
    float curiosity_l = 1.0f - lean * 0.10f;
    float curiosity_r = 1.0f + lean * 0.10f;

    // Wake-up stretch overshoot decays toward 0
    float stretch_boost = 1.0f + 0.28f * stretch_;

    float base_h = kEyeBaseH * t_eye_h_scale_ * stretch_boost;
    float base_w = kEyeBaseW * t_eye_w_scale_;

    eye_l_h_ = Ease(eye_l_h_, base_h * curiosity_l, 0.28f);
    eye_r_h_ = Ease(eye_r_h_, base_h * curiosity_r, 0.28f);
    eye_l_w_ = Ease(eye_l_w_, base_w, 0.28f);
    eye_r_w_ = Ease(eye_r_w_, base_w, 0.28f);

    // Attentive micro-pulse while listening, slow breathing while sleeping
    float pulse = 0;
    float breath = 0;
    if (state_ == FaceState::Listening) {
        pulse = 1.5f * sinf(tsec * 5.0f);
    } else if (state_ == FaceState::Sleeping) {
        breath = 1.8f * sinf(tsec * 2.2f);
    }

    // Eyelids: blink is fast-close / slower-open
    float lid_k = (t_lid_ > lid_) ? 0.55f : 0.30f;
    lid_ = Ease(lid_, t_lid_, lid_k);

    // Wink closes only the right eye (on top of the shared eyelid value)
    wink_ = Ease(wink_, t_wink_, 0.35f);

    float disp_l_h = Clampf((eye_l_h_ + pulse) * (1.0f - lid_), 2.0f, 40.0f);
    float disp_r_h = Clampf((eye_r_h_ + pulse) * (1.0f - lid_) * (1.0f - wink_ * 0.93f),
                            2.0f, 40.0f);

    int radius_l = (int)Clampf(disp_l_h * 0.34f, 2.0f, 9.0f);
    int radius_r = (int)Clampf(disp_r_h * 0.34f, 2.0f, 9.0f);

    // Squash & stretch: as an eye closes it widens slightly (volume feel)
    float squash_l = 1.0f + 0.16f * (1.0f - disp_l_h / Clampf(eye_l_h_, 1.0f, 40.0f));
    float squash_r = 1.0f + 0.16f * (1.0f - disp_r_h / Clampf(eye_r_h_, 1.0f, 40.0f));

    lv_obj_set_size(left_eye_, (int)(eye_l_w_ * squash_l), (int)disp_l_h);
    lv_obj_set_size(right_eye_, (int)(eye_r_w_ * squash_r), (int)disp_r_h);
    lv_obj_set_style_radius(left_eye_, radius_l, 0);
    lv_obj_set_style_radius(right_eye_, radius_r, 0);

    int eye_y = (int)(kEyeCenterY + gaze_y_ + breath);
    lv_obj_align(left_eye_, LV_ALIGN_CENTER, (int)(-kEyeCenterX + gaze_x_), eye_y);
    lv_obj_align(right_eye_, LV_ALIGN_CENTER, (int)(kEyeCenterX + gaze_x_), eye_y);

    // Happy cheeks: black rounded rects rising over the eye bottoms -> ^ ^ eyes
    cheek_ = Ease(cheek_, t_cheek_, 0.25f);
    if (cheek_ > 0.05f) {
        int cheek_h_l = (int)(disp_l_h * cheek_ * 0.6f);
        int cheek_h_r = (int)(disp_r_h * cheek_ * 0.6f);
        lv_obj_clear_flag(left_cheek_, LV_OBJ_FLAG_HIDDEN);
        lv_obj_clear_flag(right_cheek_, LV_OBJ_FLAG_HIDDEN);
        lv_obj_set_size(left_cheek_, (int)eye_l_w_ + 6, cheek_h_l + 2);
        lv_obj_set_size(right_cheek_, (int)eye_r_w_ + 6, cheek_h_r + 2);
        lv_obj_align(left_cheek_, LV_ALIGN_CENTER, (int)(-kEyeCenterX + gaze_x_),
                     eye_y + (int)(disp_l_h / 2) - cheek_h_l / 2 + 2);
        lv_obj_align(right_cheek_, LV_ALIGN_CENTER, (int)(kEyeCenterX + gaze_x_),
                     eye_y + (int)(disp_r_h / 2) - cheek_h_r / 2 + 2);
    } else {
        lv_obj_add_flag(left_cheek_, LV_OBJ_FLAG_HIDDEN);
        lv_obj_add_flag(right_cheek_, LV_OBJ_FLAG_HIDDEN);
    }

    // Brows: carve the top corners of the eyes.
    // brow_dir_ = +1 pulls the inner corners down (angry),
    // brow_dir_ = -1 pulls the outer corners down (sad).
    brow_ = Ease(brow_, t_brow_, 0.22f);
    if (brow_ > 0.05f) {
        int brow_h_l = (int)(disp_l_h * brow_ * 0.55f) + 2;
        int brow_h_r = (int)(disp_r_h * brow_ * 0.55f) + 2;
        int brow_w_l = (int)(eye_l_w_ * 0.75f);
        int brow_w_r = (int)(eye_r_w_ * 0.75f);
        // Shift each brow toward the inner or outer side of its eye
        int shift_l = (int)(eye_l_w_ * 0.35f) * brow_dir_;
        int shift_r = -(int)(eye_r_w_ * 0.35f) * brow_dir_;

        lv_obj_clear_flag(left_brow_, LV_OBJ_FLAG_HIDDEN);
        lv_obj_clear_flag(right_brow_, LV_OBJ_FLAG_HIDDEN);
        lv_obj_set_size(left_brow_, brow_w_l, brow_h_l);
        lv_obj_set_size(right_brow_, brow_w_r, brow_h_r);
        lv_obj_align(left_brow_, LV_ALIGN_CENTER,
                     (int)(-kEyeCenterX + gaze_x_) + shift_l,
                     eye_y - (int)(disp_l_h / 2) + brow_h_l / 2 - 2);
        lv_obj_align(right_brow_, LV_ALIGN_CENTER,
                     (int)(kEyeCenterX + gaze_x_) + shift_r,
                     eye_y - (int)(disp_r_h / 2) + brow_h_r / 2 - 2);
    } else {
        lv_obj_add_flag(left_brow_, LV_OBJ_FLAG_HIDDEN);
        lv_obj_add_flag(right_brow_, LV_OBJ_FLAG_HIDDEN);
    }

    // Mouth: konusurken ses seviyesi zaten yumusatildigi icin burada daha
    // hizli takip ederiz; diger durumlarda yumusak gecis korunur.
    float mouth_k = (state_ == FaceState::Speaking) ? 0.75f : 0.45f;
    mouth_w_ = Ease(mouth_w_, t_mouth_w_, mouth_k);
    mouth_h_ = Ease(mouth_h_, t_mouth_h_, mouth_k);
    if (mouth_h_ < 1.5f) {
        lv_obj_add_flag(mouth_, LV_OBJ_FLAG_HIDDEN);
    } else {
        lv_obj_clear_flag(mouth_, LV_OBJ_FLAG_HIDDEN);
        lv_obj_set_size(mouth_, (int)mouth_w_, (int)mouth_h_);
        int mouth_radius;
        if (mouth_shape_ == 1) {
            mouth_radius = 1;  // angry: flat straight line
        } else if (mouth_shape_ == 2) {
            mouth_radius = (int)Clampf(mouth_h_ * 0.5f, 3.0f, 10.0f);  // surprised: round
        } else {
            mouth_radius = (int)Clampf(mouth_h_ * 0.45f, 2.0f, 7.0f);
        }
        lv_obj_set_style_radius(mouth_, mouth_radius, 0);
        lv_obj_align(mouth_, LV_ALIGN_CENTER, (int)(gaze_x_ * 0.5f),
                     (int)(kMouthCenterY + gaze_y_ * 0.5f + breath));
    }

    // Floating z z z, only while drifting off to sleep
    if (state_ == FaceState::Sleeping && now < zzz_end_ms_) {
        lv_obj_clear_flag(zzz_label_, LV_OBJ_FLAG_HIDDEN);
        if (now >= zzz_next_ms_) {
            zzz_next_ms_ = now + 800;
            zzz_step_ = (zzz_step_ + 1) % 3;
            const char* texts[] = {"z", "z z", "z z z"};
            lv_label_set_text(zzz_label_, texts[zzz_step_]);
        }
        lv_obj_align(zzz_label_, LV_ALIGN_CENTER, 44, -20 - zzz_step_ * 2);
    } else {
        lv_obj_add_flag(zzz_label_, LV_OBJ_FLAG_HIDDEN);
    }

    stretch_ *= 0.90f;
    if (stretch_ < 0.02f) {
        stretch_ = 0;
    }
}

void FaceEngine::FeedAudioLevel(float level) {
    // Agiz hizli acilir, yavas kapanir (gercek agiz boyle hareket eder).
    // Tek kademe yumusatma: geometri tarafinda ikinci bir filtre yok ki
    // sesle goruntu arasinda gecikme olusmasin.
    float prev = audio_level_;
    float k = (level > prev) ? 0.70f : 0.22f;
    audio_level_ = Clampf(prev + (level - prev) * k, 0.0f, 1.0f);
    audio_last_ms_ = lv_tick_get();
}

void FaceOnAudioOutput(const int16_t* pcm, size_t samples) {
    auto face = GetOledFaceEngine();
    if (face == nullptr || pcm == nullptr || samples == 0) {
        return;
    }

    // RMS (ortalama guc) kullaniyoruz: tepe degeri konusmada surekli tavana
    // vurdugu icin agzi hep acik gosteriyordu. RMS konusmanin gercek
    // yogunlugunu izler.
    int64_t sum_sq = 0;
    size_t count = 0;
    size_t step = samples > 512 ? samples / 256 : 1;
    for (size_t i = 0; i < samples; i += step) {
        int32_t v = pcm[i];
        sum_sq += (int64_t)v * v;
        count++;
    }
    if (count == 0) {
        return;
    }
    float rms = sqrtf((float)sum_sq / (float)count);

    // Logaritmik olcek: kulak sesi boyle duyar. -46 dBFS ile 0 dBFS arasini
    // 0..1'e esler; boylece kisik heceler de agzi biraz aciar, yuksek heceler
    // tavana yapismaz.
    float level = 0.0f;
    if (rms > 1.0f) {
        float db = 20.0f * log10f(rms / 32768.0f);
        level = (db + 46.0f) / 46.0f;
    }
    face->FeedAudioLevel(Clampf(level, 0.0f, 1.0f));
}

void FaceEngine::Update() {
    if (!container_) {
        return;
    }

    // Bekleyen duygu: sabitlendiyse uygula (gecici sinyaller boylece elenir)
    if (has_pending_emotion_ &&
        (lv_tick_get() - pending_emotion_ms_) >= kEmotionSettleMs) {
        has_pending_emotion_ = false;
        emotion_ = pending_emotion_;
        emotion_until_ms_ = lv_tick_get() +
                            (pending_emotion_ == FaceEmotion::Neutral ? 0 : 12000);
    }

    // Bekleyen uyku: once veda cumlesinin bitmesini bekle, sonra gozleri kapat
    if (pending_sleep_ && !sleeping_) {
        uint32_t now = lv_tick_get();
        bool audio_fresh = (now - audio_last_ms_) < 300;
        if (state_ == FaceState::Speaking || audio_fresh) {
            pending_speech_seen_ = true;
        }
        bool speech_done = pending_speech_seen_ &&
                           state_ != FaceState::Speaking &&
                           (now - audio_last_ms_) > 900;
        // Hic konusma gelmezse de sonsuza kadar bekleme
        bool timed_out = !pending_speech_seen_ && (now - pending_sleep_ms_) > 8000;
        if (speech_done || timed_out) {
            Sleep();
        }
    }

    // Blink state machine (suppressed while sleeping)
    if (!sleeping_) {
        switch (blink_phase_) {
            case 0:
                if (rand() % 75 == 0) {
                    blink_phase_ = 1;
                    double_blink_ = (rand() % 4 == 0);
                }
                break;
            case 1:
                t_lid_ = 1.0f;
                if (lid_ > 0.8f) {
                    blink_phase_ = 2;
                }
                break;
            case 2:
                t_lid_ = 0.0f;
                if (lid_ < 0.1f) {
                    if (double_blink_) {
                        double_blink_ = false;
                        blink_phase_ = 1;
                    } else {
                        blink_phase_ = 0;
                    }
                }
                break;
        }
    }

    ComputeTargets();

    // Blink overrides the state's lid target while active
    if (!sleeping_ && blink_phase_ == 1) {
        t_lid_ = 1.0f;
    }

    // Ease gaze
    gaze_x_ = Ease(gaze_x_, t_gaze_x_, 0.20f);
    gaze_y_ = Ease(gaze_y_, t_gaze_y_, 0.20f);

    ApplyGeometry();
}
