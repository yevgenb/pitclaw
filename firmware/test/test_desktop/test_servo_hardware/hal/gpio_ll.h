#pragma once
using gpio_num_t = int;
struct FakeGpio {};
static FakeGpio GPIO;
inline void gpio_ll_input_enable(FakeGpio*, gpio_num_t pin) {
    inputEnabled[pin]=true; calls.push_back({'I',pin,1});
}
