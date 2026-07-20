#pragma once

#include <lvgl.h>
#include <stdint.h>
#include <stddef.h>

enum class FaceState { Idle, Listening, Speaking, Sleeping };

enum class FaceEmotion {
    Neutral,
    Happy,      // happy, laughing, funny, delicious, confident, cool, relaxed, silly
    Sad,        // sad, crying, embarrassed
    Angry,      // angry
    Surprised,  // surprised, shocked
    Thinking,   // thinking
    Sleepy,     // sleepy
    Winking,    // winking, kissy
    Loving,     // loving
    Confused,   // confused
};

class FaceEngine {
public:
    void Init(lv_obj_t* parent);
    void SetState(FaceState state);
    void SetEmotion(const char* emotion);
    // Uykuya "hemen" degil, konusma bitince gecer: Iva once iyi geceler der,
    // sesi bittikten sonra gozlerini kapatir.
    void RequestSleep();
    void Sleep();
    void WakeUp();
    bool IsSleeping() const { return sleeping_; }
    void Update();
    // Called from the audio output task with the level (0..1) of the PCM chunk
    // that is being pushed to the speaker right now.
    void FeedAudioLevel(float level);

private:
    void ComputeTargets();
    void ApplyEmotion();
    void ApplyGeometry();

    lv_obj_t* container_ = nullptr;
    lv_obj_t* left_eye_ = nullptr;
    lv_obj_t* right_eye_ = nullptr;
    lv_obj_t* left_cheek_ = nullptr;
    lv_obj_t* right_cheek_ = nullptr;
    lv_obj_t* left_brow_ = nullptr;
    lv_obj_t* right_brow_ = nullptr;
    lv_obj_t* mouth_ = nullptr;
    lv_obj_t* zzz_label_ = nullptr;

    FaceState state_ = FaceState::Idle;
    FaceEmotion emotion_ = FaceEmotion::Neutral;

    // Bekleyen uyku istegi (konusma bitince uygulanir)
    bool pending_sleep_ = false;
    bool pending_speech_seen_ = false;
    uint32_t pending_sleep_ms_ = 0;
    uint32_t emotion_until_ms_ = 0;
    bool sleeping_ = false;

    // Sunucu cevap uretirken gecici duygular gonderiyor (olcum: gercek
    // duygudan ~1 sn once kisa bir "sad"). Yeni duyguyu hemen uygulamak
    // yerine sabitlenmesini bekleriz; bu sure icinde yenisi gelirse eskisi
    // hic gosterilmeden atilir.
    static constexpr uint32_t kEmotionSettleMs = 1400;
    FaceEmotion pending_emotion_ = FaceEmotion::Neutral;
    bool has_pending_emotion_ = false;
    uint32_t pending_emotion_ms_ = 0;

    // Layout constants
    static constexpr float kEyeBaseW = 26.0f;
    static constexpr float kEyeBaseH = 30.0f;
    static constexpr int kEyeCenterX = 30;   // distance from screen center
    static constexpr int kEyeCenterY = -8;
    static constexpr int kMouthCenterY = 20;

    // Eased current values
    float eye_l_w_ = kEyeBaseW, eye_l_h_ = kEyeBaseH;
    float eye_r_w_ = kEyeBaseW, eye_r_h_ = kEyeBaseH;
    float gaze_x_ = 0, gaze_y_ = 0;
    float mouth_w_ = 16, mouth_h_ = 5;
    float cheek_ = 0;      // 0..1 happy squint (bottom of eyes covered)
    float brow_ = 0;       // 0..1 brow carve depth (top of eyes covered)
    float wink_ = 0;       // 0..1 right eye closed on its own
    float lid_ = 0;        // 0..1 eyelids closed (blink + sleep share this)
    float stretch_ = 0;    // wake-up overshoot

    // Targets
    float t_eye_h_scale_ = 1.0f;
    float t_eye_w_scale_ = 1.0f;
    float t_gaze_x_ = 0, t_gaze_y_ = 0;
    float t_mouth_w_ = 16, t_mouth_h_ = 5;
    float t_cheek_ = 0;
    float t_brow_ = 0;
    float t_wink_ = 0;
    float t_lid_ = 0;
    // +1 = brows carve the inner corners (angry), -1 = outer corners (sad)
    int brow_dir_ = 1;
    // Mouth shape hint: 0 normal, 1 flat/wide (angry), 2 round (surprised)
    int mouth_shape_ = 0;

    // Blink state machine: 0 idle, 1 closing, 2 opening
    int blink_phase_ = 0;
    bool double_blink_ = false;

    // Saccade / happy moment timers
    uint32_t next_saccade_ms_ = 0;
    uint32_t happy_until_ms_ = 0;
    uint32_t next_happy_ms_ = 0;

    // Speaking mouth rhythm
    uint32_t speak_next_ms_ = 0;

    // Real lip-sync driven by the audio output task
    volatile float audio_level_ = 0;
    volatile uint32_t audio_last_ms_ = 0;

    // Sleep visuals: the z z z only plays while drifting off, then fades out
    uint32_t zzz_next_ms_ = 0;
    uint32_t zzz_end_ms_ = 0;
    int zzz_step_ = 0;
};

// Access to the face engine owned by the OLED display (nullptr if no face UI).
FaceEngine* GetOledFaceEngine();

// Hook called by the audio service right before PCM data reaches the speaker,
// so the mouth moves with the actual sound instead of the TTS "start" message.
void FaceOnAudioOutput(const int16_t* pcm, size_t samples);
