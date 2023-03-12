#pragma once

#include "esphome/core/component.h"
#include "esphome/core/automation.h"
#include "esphome/components/output/float_output.h"

namespace esphome {
namespace rtttl {

class Rtttl : public Component {
 public:
  void set_output(output::FloatOutput *output) { output_ = output; }
  void play(std::string rtttl, float level);
  void stop() {
    note_duration_ = 0;
    output_->set_level(0.0);
  }
  void dump_config() override;

  bool is_playing() { return note_duration_ != 0; }
  void loop() override;

  void add_on_finished_playback_callback(std::function<void()> callback) {
    this->on_finished_playback_callback_.add(std::move(callback));
  }

 protected:
  inline uint8_t get_integer_() {
    uint8_t ret = 0;
    while (isdigit(rtttl_[position_])) {
      ret = (ret * 10) + (rtttl_[position_++] - '0');
    }
    return ret;
  }

  std::string rtttl_;
  size_t position_;
  uint16_t wholenote_;
  uint16_t default_duration_;
  uint16_t default_octave_;
  uint32_t last_note_;
  uint16_t note_duration_;


  TemplatableValue<float> default_volume_level_{};
 public:
  template<typename V> void set_default_volume_level(V level) { this->default_volume_level_ = level; }
  float default_volume_level() { return default_volume_level_.value(); }
 protected:
  float volume_level_;
  uint32_t output_freq_;
  output::FloatOutput *output_;

  CallbackManager<void()> on_finished_playback_callback_;
};

template<typename... Ts> class PlayAction : public Action<Ts...> {
 public:
  PlayAction(Rtttl *rtttl) : rtttl_(rtttl) {}
  TEMPLATABLE_VALUE(std::string, value)
  TEMPLATABLE_VALUE(float, level)

  void play(Ts... x) override {
    this->rtttl_->play(
        this->value_.value(x...),
        this->level_.value_or(x..., this->rtttl_->default_volume_level())
    );
  }

 protected:
  Rtttl *rtttl_;
};

template<typename... Ts> class StopAction : public Action<Ts...>, public Parented<Rtttl> {
 public:
  void play(Ts... x) override { this->parent_->stop(); }
};

template<typename... Ts> class IsPlayingCondition : public Condition<Ts...>, public Parented<Rtttl> {
 public:
  bool check(Ts... x) override { return this->parent_->is_playing(); }
};

class FinishedPlaybackTrigger : public Trigger<> {
 public:
  explicit FinishedPlaybackTrigger(Rtttl *parent) {
    parent->add_on_finished_playback_callback([this]() { this->trigger(); });
  }
};

}  // namespace rtttl
}  // namespace esphome
