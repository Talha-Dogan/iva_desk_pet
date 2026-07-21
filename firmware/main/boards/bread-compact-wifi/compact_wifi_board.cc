#include "wifi_board.h"
#include "codecs/no_audio_codec.h"
#include "display/oled_display.h"
#include "display/face_engine.h"
#include "system_reset.h"
#include "application.h"
#include "button.h"
#include "config.h"
#include "mcp_server.h"
#include "lamp_controller.h"
#include "led/single_led.h"
#include "assets/lang_config.h"

#include <esp_log.h>
#include <esp_random.h>
#include <driver/i2c_master.h>
#include <esp_lcd_panel_ops.h>
#include <esp_lcd_panel_vendor.h>

#ifdef SH1106
#include <esp_lcd_panel_sh1106.h>
#endif

#define TAG "CompactWifiBoard"

class CompactWifiBoard : public WifiBoard {
private:
    i2c_master_bus_handle_t display_i2c_bus_;
    esp_lcd_panel_io_handle_t panel_io_ = nullptr;
    esp_lcd_panel_handle_t panel_ = nullptr;
    Display* display_ = nullptr;
    Button boot_button_;
    Button touch_button_;
    Button volume_up_button_;
    Button volume_down_button_;

    void InitializeDisplayI2c() {
        i2c_master_bus_config_t bus_config = {
            .i2c_port = (i2c_port_t)0,
            .sda_io_num = DISPLAY_SDA_PIN,
            .scl_io_num = DISPLAY_SCL_PIN,
            .clk_source = I2C_CLK_SRC_DEFAULT,
            .glitch_ignore_cnt = 7,
            .intr_priority = 0,
            .trans_queue_depth = 0,
            .flags = {
                .enable_internal_pullup = 1,
            },
        };
        ESP_ERROR_CHECK(i2c_new_master_bus(&bus_config, &display_i2c_bus_));
    }

    void InitializeSsd1306Display() {
        // SSD1306 config
        esp_lcd_panel_io_i2c_config_t io_config = {
            .dev_addr = 0x3C,
            .on_color_trans_done = nullptr,
            .user_ctx = nullptr,
            .control_phase_bytes = 1,
            .dc_bit_offset = 6,
            .lcd_cmd_bits = 8,
            .lcd_param_bits = 8,
            .flags = {
                .dc_low_on_data = 0,
                .disable_control_phase = 0,
            },
            .scl_speed_hz = 400 * 1000,
        };

        ESP_ERROR_CHECK(esp_lcd_new_panel_io_i2c_v2(display_i2c_bus_, &io_config, &panel_io_));

        ESP_LOGI(TAG, "Install SSD1306 driver");
        esp_lcd_panel_dev_config_t panel_config = {};
        panel_config.reset_gpio_num = -1;
        panel_config.bits_per_pixel = 1;

        esp_lcd_panel_ssd1306_config_t ssd1306_config = {
            .height = static_cast<uint8_t>(DISPLAY_HEIGHT),
        };
        panel_config.vendor_config = &ssd1306_config;

#ifdef SH1106
        ESP_ERROR_CHECK(esp_lcd_new_panel_sh1106(panel_io_, &panel_config, &panel_));
#else
        ESP_ERROR_CHECK(esp_lcd_new_panel_ssd1306(panel_io_, &panel_config, &panel_));
#endif
        ESP_LOGI(TAG, "SSD1306 driver installed");

        // Reset the display
        ESP_ERROR_CHECK(esp_lcd_panel_reset(panel_));
        if (esp_lcd_panel_init(panel_) != ESP_OK) {
            ESP_LOGE(TAG, "Failed to initialize display");
            display_ = new NoDisplay();
            return;
        }
        ESP_ERROR_CHECK(esp_lcd_panel_invert_color(panel_, false));

        // Set the display to on
        ESP_LOGI(TAG, "Turning display on");
        ESP_ERROR_CHECK(esp_lcd_panel_disp_on_off(panel_, true));

        display_ = new OledDisplay(panel_io_, panel_, DISPLAY_WIDTH, DISPLAY_HEIGHT, DISPLAY_MIRROR_X, DISPLAY_MIRROR_Y);
    }

    void InitializeButtons() {
        boot_button_.OnClick([this]() {
            auto& app = Application::GetInstance();
            if (app.GetDeviceState() == kDeviceStateStarting) {
                EnterWifiConfigMode();
                return;
            }
            app.ToggleChatState();
        });
        touch_button_.OnPressDown([this]() {
            Application::GetInstance().StartListening();
        });
        touch_button_.OnPressUp([this]() {
            Application::GetInstance().StopListening();
        });

        volume_up_button_.OnClick([this]() {
            auto codec = GetAudioCodec();
            auto volume = codec->output_volume() + 10;
            if (volume > 100) {
                volume = 100;
            }
            codec->SetOutputVolume(volume);
            GetDisplay()->ShowNotification(Lang::Strings::VOLUME + std::to_string(volume));
        });

        volume_up_button_.OnLongPress([this]() {
            GetAudioCodec()->SetOutputVolume(100);
            GetDisplay()->ShowNotification(Lang::Strings::MAX_VOLUME);
        });

        volume_down_button_.OnClick([this]() {
            auto codec = GetAudioCodec();
            auto volume = codec->output_volume() - 10;
            if (volume < 0) {
                volume = 0;
            }
            codec->SetOutputVolume(volume);
            GetDisplay()->ShowNotification(Lang::Strings::VOLUME + std::to_string(volume));
        });

        volume_down_button_.OnLongPress([this]() {
            GetAudioCodec()->SetOutputVolume(0);
            GetDisplay()->ShowNotification(Lang::Strings::MUTED);
        });
    }

    // 物联网初始化，逐步迁移到 MCP 协议
    void InitializeTools() {
        static LampController lamp(LAMP_GPIO);

        auto& mcp_server = McpServer::GetInstance();
        mcp_server.AddTool("self.face.sleep",
            "Close the robot's eyes and put its face to sleep (nap mode). "
            "Call this when the user tells the assistant to sleep or take a nap "
            "(e.g. 'uyu', 'uyu bakalim', 'go to sleep', 'sleep now').",
            PropertyList(),
            [](const PropertyList& properties) -> ReturnValue {
                auto face = GetOledFaceEngine();
                if (face == nullptr) {
                    return false;
                }
                // Once veda cumlesi soylensin, gozler en son kapansin
                face->RequestSleep();
                return true;
            });
        mcp_server.AddTool("self.face.wake_up",
            "Open the robot's eyes and wake its face up from sleep. "
            "Call this when the user tells the assistant to wake up (e.g. 'uyan', 'wake up').",
            PropertyList(),
            [](const PropertyList& properties) -> ReturnValue {
                auto face = GetOledFaceEngine();
                if (face == nullptr) {
                    return false;
                }
                face->WakeUp();
                return true;
            });
        mcp_server.AddTool("self.screen.show_status",
            "Switch the OLED screen from the animated face to the classic status/info screen. "
            "It shows the status text, network state, notifications and chat subtitles. "
            "Call this when the user asks for the status or info screen "
            "(e.g. 'durum', 'durum ekrani', 'bilgi ekranini goster', 'show status screen').",
            PropertyList(),
            [this](const PropertyList& properties) -> ReturnValue {
                auto oled = static_cast<OledDisplay*>(display_);
                if (oled == nullptr) {
                    return false;
                }
                oled->SetFaceMode(false);
                return true;
            });
        mcp_server.AddTool("self.screen.show_face",
            "Switch the OLED screen back to the animated robot face. "
            "Call this when the user asks to see the face again "
            "(e.g. 'yuzunu goster', 'yuz ekranina don', 'show your face').",
            PropertyList(),
            [this](const PropertyList& properties) -> ReturnValue {
                auto oled = static_cast<OledDisplay*>(display_);
                if (oled == nullptr) {
                    return false;
                }
                oled->SetFaceMode(true);
                return true;
            });

        mcp_server.AddTool("self.trivia_wheel",
            "Trivia Crack carkini cevirir: ekranda kategoriler (Bilim, Sanat, "
            "Spor, Tarih, Cografya, Eglence) slot-makinesi gibi doner, bir "
            "kategoride durur ve cark sesi calar. Kullanici Trivia oynarken "
            "'cark cevir', 'cark' dediginde cagir. Donen kategori adini "
            "dondurur; sen o kategoriden bir soru sorarsin.",
            PropertyList(),
            [this](const PropertyList& properties) -> ReturnValue {
                auto oled = static_cast<OledDisplay*>(display_);
                auto face = GetOledFaceEngine();
                if (oled == nullptr || face == nullptr) {
                    return std::string("Eglence");
                }
                oled->SetFaceMode(true);
                int target = esp_random() % FaceEngine::kWheelCount;
                std::string category = face->WheelCategory(target);
                face->SpinWheel(target);
                // Tek kisa "cark basladi" sesi; animasyon arka planda kendi
                // doner (araci BLOKLAMIYORUZ ki MCP zaman asimina ugramasin).
                Application::GetInstance().PlaySound(Lang::Sounds::OGG_POPUP);
                return std::string("Cikan kategori: ") + category;
            });
    }

public:
    CompactWifiBoard() :
        boot_button_(BOOT_BUTTON_GPIO),
        touch_button_(TOUCH_BUTTON_GPIO),
        volume_up_button_(VOLUME_UP_BUTTON_GPIO),
        volume_down_button_(VOLUME_DOWN_BUTTON_GPIO) {
        InitializeDisplayI2c();
        InitializeSsd1306Display();
        InitializeButtons();
        InitializeTools();
    }

    virtual Led* GetLed() override {
        static SingleLed led(BUILTIN_LED_GPIO);
        return &led;
    }

    virtual AudioCodec* GetAudioCodec() override {
#ifdef AUDIO_I2S_METHOD_SIMPLEX
        static NoAudioCodecSimplex audio_codec(AUDIO_INPUT_SAMPLE_RATE, AUDIO_OUTPUT_SAMPLE_RATE,
            AUDIO_I2S_SPK_GPIO_BCLK, AUDIO_I2S_SPK_GPIO_LRCK, AUDIO_I2S_SPK_GPIO_DOUT, AUDIO_I2S_MIC_GPIO_SCK, AUDIO_I2S_MIC_GPIO_WS, AUDIO_I2S_MIC_GPIO_DIN);
#else
        static NoAudioCodecDuplex audio_codec(AUDIO_INPUT_SAMPLE_RATE, AUDIO_OUTPUT_SAMPLE_RATE,
            AUDIO_I2S_GPIO_BCLK, AUDIO_I2S_GPIO_WS, AUDIO_I2S_GPIO_DOUT, AUDIO_I2S_GPIO_DIN);
#endif
        return &audio_codec;
    }

    virtual Display* GetDisplay() override {
        return display_;
    }
};

DECLARE_BOARD(CompactWifiBoard);
