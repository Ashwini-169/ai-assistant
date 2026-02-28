from duplex.interrupt_controller import InterruptController
from duplex.state_machine import AssistantState, AssistantStateController


def test_interrupt_controller_flag_cycle():
    controller = InterruptController()
    assert controller.is_triggered() is False
    controller.trigger()
    assert controller.is_triggered() is True
    controller.clear()
    assert controller.is_triggered() is False


def test_state_controller_transitions_and_visual_label():
    controller = AssistantStateController()
    assert controller.get_state() == AssistantState.IDLE

    controller.set_state(AssistantState.SPEAKING)
    assert controller.get_state() == AssistantState.SPEAKING
    assert "speaking" in controller.visual_label()
