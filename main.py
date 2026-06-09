"""
AQL 判定工具 - Android 移动版
ISO 2859-1 / GB/T 2828.1 正常检验一次抽样方案
"""
import sys
import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.core.window import Window
from kivy.utils import platform
from kivy.graphics import Color, RoundedRectangle
from functools import partial

from aql_engine import (
    AQLEngine, INSPECTION_LEVELS, AQL_DISPLAY, AQL_DISPLAY_MAP,
    CODE_SAMPLE_SIZES, DEFECT_KEYS, DEFECT_CATEGORIES
)

# ============================================================
# 颜色常量 (RGBA 0-1)
# ============================================================
C = {
    'bg_root':     (0.063, 0.063, 0.110, 1),   # #10101c
    'bg_card':     (0.110, 0.125, 0.200, 1),   # #1c2033
    'bg_input':    (0.157, 0.173, 0.251, 1),   # #282c40
    'bg_btn':      (0.212, 0.231, 0.349, 1),   # #363b59
    'bg_btn_press':(0.275, 0.298, 0.443, 1),   # #464c71
    'fg':          (0.878, 0.878, 0.878, 1),   # #e0e0e0
    'fg_header':   (1.0,   1.0,   1.0,   1),   # #ffffff
    'fg_dim':      (0.533, 0.533, 0.533, 1),   # #888888
    'green':       (0.298, 0.875, 0.502, 1),   # #4cdf80
    'green_bg':    (0.082, 0.216, 0.145, 1),   # #153725
    'red':         (1.0,   0.333, 0.400, 1),   # #ff5566
    'red_bg':      (0.196, 0.078, 0.078, 1),   # #321414
    'blue':        (0.357, 0.620, 1.0,   1),   # #5b9eff
    'orange':      (1.0,   0.549, 0.259, 1),   # #ff8c42
    'judge_btn':   (0.831, 0.220, 0.051, 1),   # #d4380d
    'judge_press': (1.0,   0.302, 0.180, 1),   # #ff4d2e
    'separator':   (0.176, 0.192, 0.282, 1),   # #2d3148
}


# ============================================================
# KV 布局 (内嵌字符串，避免文件加载问题)
# ============================================================
KV = """
<Card>:
    orientation: 'vertical'
    padding: [dp(14), dp(12)]
    spacing: dp(8)
    canvas.before:
        Color:
            rgba: C['bg_card']
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(8)]

<TitleLabel@Label>:
    font_size: '16sp'
    bold: True
    color: C['fg_header']
    size_hint_y: None
    height: dp(32)
    text_size: self.width, None
    halign: 'left'
    valign: 'middle'
    padding: [0, 0]

<FieldLabel@Label>:
    font_size: '14sp'
    color: C['fg']
    size_hint_y: None
    height: dp(26)
    text_size: self.width, None
    halign: 'left'
    valign: 'middle'

<FieldRow@BoxLayout>:
    orientation: 'horizontal'
    size_hint_y: None
    height: dp(48)
    spacing: dp(8)
    padding: [dp(4), 0]

<NumInput@TextInput>:
    size_hint_y: None
    height: dp(48)
    font_size: '16sp'
    foreground_color: C['fg']
    background_color: C['bg_input']
    cursor_color: C['fg']
    padding: [dp(10), dp(12), dp(10), dp(12)]
    input_filter: 'int'
    multiline: False

<AQLSpinner@Spinner>:
    size_hint_y: None
    height: dp(48)
    font_size: '15sp'
    foreground_color: C['fg']
    background_color: C['bg_input']
    background_normal: ''
    background_down: C['bg_btn_press']
    color: C['fg']
    padding: [dp(10), dp(12)]

<ValueLabel@Label>:
    font_size: '17sp'
    bold: True
    size_hint_y: None
    height: dp(36)
    text_size: self.width, None
    halign: 'center'
    valign: 'middle'

<AQLRoot>:
    orientation: 'vertical'
    canvas.before:
        Color:
            rgba: C['bg_root']
        Rectangle:
            pos: self.pos
            size: self.size

    # ========== 标题栏 ==========
    BoxLayout:
        size_hint_y: None
        height: dp(54)
        padding: [dp(14), 0]
        canvas.before:
            Color:
                rgba: C['bg_card']
            Rectangle:
                pos: self.pos
                size: self.size

        Label:
            text: 'AQL 判定工具'
            font_size: '20sp'
            bold: True
            color: C['fg_header']
            size_hint_x: 0.7
            text_size: self.width, None
            halign: 'left'
            valign: 'middle'

        Label:
            text: 'ISO 2859-1'
            font_size: '12sp'
            color: C['fg_dim']
            size_hint_x: 0.3
            text_size: self.width, None
            halign: 'right'
            valign: 'middle'

    # ========== 可滚动内容 ==========
    ScrollView:
        id: scroll_view
        do_scroll_x: False
        do_scroll_y: True
        bar_width: dp(4)
        bar_color: C['bg_btn']

        BoxLayout:
            orientation: 'vertical'
            size_hint_y: None
            width: root.width - dp(4)
            padding: [dp(12), dp(8), dp(12), dp(12)]
            spacing: dp(8)

            # ========== 抽样标准设置 ==========
            Card:
                TitleLabel:
                    text: '抽样标准设置'
                    size_hint_y: None
                    height: dp(30)

                FieldRow:
                    FieldLabel:
                        text: '检验水平'
                        size_hint_x: 0.38
                    AQLSpinner:
                        id: level_spinner
                        text: app.default_level
                        values: app.inspection_levels
                        size_hint_x: 0.28
                        on_text: root.on_level_change()
                    FieldLabel:
                        text: '批量'
                        size_hint_x: 0.1
                        padding: [dp(4), 0]
                    NumInput:
                        id: lot_size_input
                        hint_text: '输入整数'
                        size_hint_x: 0.24
                        on_text: root.on_lot_size_change()

                FieldRow:
                    FieldLabel:
                        id: code_label
                        text: '字码: —'
                        color: C['blue']
                        bold: True
                    FieldLabel:
                        id: sample_label
                        text: '应抽: —'
                        color: C['orange']
                        bold: True

                BoxLayout:
                    orientation: 'horizontal'
                    size_hint_y: None
                    height: dp(4)
                    canvas:
                        Color:
                            rgba: C['separator']
                        Rectangle:
                            pos: self.pos
                            size: self.size

                # AQL 三行
                FieldRow:
                    FieldLabel:
                        text: '缺陷类别'
                        color: C['fg_dim']
                        font_size: '12sp'
                        size_hint_x: 0.4
                    FieldLabel:
                        text: 'AQL 值'
                        color: C['fg_dim']
                        font_size: '12sp'
                        size_hint_x: 0.3

                FieldRow:
                    FieldLabel:
                        text: '致命缺陷'
                        size_hint_x: 0.4
                    AQLSpinner:
                        id: aql_critical_spinner
                        text: '0.010'
                        values: app.aql_display
                        size_hint_x: 0.3
                        on_text: root.on_aql_change()

                FieldRow:
                    FieldLabel:
                        text: '严重缺陷'
                        size_hint_x: 0.4
                    AQLSpinner:
                        id: aql_major_spinner
                        text: '1.0'
                        values: app.aql_display
                        size_hint_x: 0.3
                        on_text: root.on_aql_change()

                FieldRow:
                    FieldLabel:
                        text: '次要缺陷'
                        size_hint_x: 0.4
                    AQLSpinner:
                        id: aql_minor_spinner
                        text: '2.5'
                        values: app.aql_display
                        size_hint_x: 0.3
                        on_text: root.on_aql_change()

            # ========== 标准值 ==========
            Card:
                TitleLabel:
                    text: '标准值 (Ac / Re)'
                    size_hint_y: None
                    height: dp(30)

                FieldRow:
                    FieldLabel:
                        text: ''
                        size_hint_x: 0.4
                    ValueLabel:
                        text: 'Ac'
                        color: C['fg_dim']
                        font_size: '14sp'
                        size_hint_x: 0.3
                    ValueLabel:
                        text: 'Re'
                        color: C['fg_dim']
                        font_size: '14sp'
                        size_hint_x: 0.3

                FieldRow:
                    FieldLabel:
                        text: '致命'
                        size_hint_x: 0.4
                    ValueLabel:
                        id: ac_critical
                        text: '—'
                        color: C['blue']
                        size_hint_x: 0.3
                    ValueLabel:
                        id: re_critical
                        text: '—'
                        color: C['blue']
                        size_hint_x: 0.3

                FieldRow:
                    FieldLabel:
                        text: '严重'
                        size_hint_x: 0.4
                    ValueLabel:
                        id: ac_major
                        text: '—'
                        color: C['blue']
                        size_hint_x: 0.3
                    ValueLabel:
                        id: re_major
                        text: '—'
                        color: C['blue']
                        size_hint_x: 0.3

                FieldRow:
                    FieldLabel:
                        text: '次要'
                        size_hint_x: 0.4
                    ValueLabel:
                        id: ac_minor
                        text: '—'
                        color: C['blue']
                        size_hint_x: 0.3
                    ValueLabel:
                        id: re_minor
                        text: '—'
                        color: C['blue']
                        size_hint_x: 0.3

            # ========== 批次判定 ==========
            Card:
                TitleLabel:
                    text: '批次判定'
                    size_hint_y: None
                    height: dp(30)

                FieldRow:
                    FieldLabel:
                        text: '实际抽样数'
                        size_hint_x: 0.4
                    NumInput:
                        id: actual_sample_input
                        hint_text: '默认等于应抽'
                        size_hint_x: 0.35
                    Label:
                        text: '件'
                        font_size: '13sp'
                        color: C['fg_dim']
                        size_hint_x: 0.1
                        text_size: self.width, None
                        halign: 'left'
                        valign: 'middle'

                FieldRow:
                    FieldLabel:
                        text: '致命缺陷数'
                        size_hint_x: 0.4
                    NumInput:
                        id: defect_critical
                        text: '0'
                        size_hint_x: 0.35
                    Label:
                        text: '个'
                        font_size: '13sp'
                        color: C['fg_dim']
                        size_hint_x: 0.1
                        text_size: self.width, None
                        halign: 'left'
                        valign: 'middle'

                FieldRow:
                    FieldLabel:
                        text: '严重缺陷数'
                        size_hint_x: 0.4
                    NumInput:
                        id: defect_major
                        text: '0'
                        size_hint_x: 0.35
                    Label:
                        text: '个'
                        font_size: '13sp'
                        color: C['fg_dim']
                        size_hint_x: 0.1
                        text_size: self.width, None
                        halign: 'left'
                        valign: 'middle'

                FieldRow:
                    FieldLabel:
                        text: '次要缺陷数'
                        size_hint_x: 0.4
                    NumInput:
                        id: defect_minor
                        text: '0'
                        size_hint_x: 0.35
                    Label:
                        text: '个'
                        font_size: '13sp'
                        color: C['fg_dim']
                        size_hint_x: 0.1
                        text_size: self.width, None
                        halign: 'left'
                        valign: 'middle'

                Label:
                    id: adjust_label
                    text: ''
                    font_size: '12sp'
                    color: C['orange']
                    size_hint_y: None
                    height: dp(20)
                    text_size: self.width, None
                    halign: 'left'
                    valign: 'middle'
                    padding: [dp(4), 0]

                Button:
                    id: judge_btn
                    text: '判  定'
                    font_size: '22sp'
                    bold: True
                    color: (1, 1, 1, 1)
                    background_color: C['judge_btn']
                    background_normal: ''
                    background_down: C['judge_press']
                    size_hint_y: None
                    height: dp(58)
                    on_release: root.on_judge()

            # ========== 判定结果 ==========
            Card:
                TitleLabel:
                    text: '判定结果'
                    size_hint_y: None
                    height: dp(30)

                Label:
                    id: result_critical
                    text: '致命缺陷: —'
                    font_size: '14sp'
                    color: C['fg']
                    size_hint_y: None
                    height: dp(28)
                    text_size: self.width, None
                    halign: 'left'
                    valign: 'middle'

                Label:
                    id: result_major
                    text: '严重缺陷: —'
                    font_size: '14sp'
                    color: C['fg']
                    size_hint_y: None
                    height: dp(28)
                    text_size: self.width, None
                    halign: 'left'
                    valign: 'middle'

                Label:
                    id: result_minor
                    text: '次要缺陷: —'
                    font_size: '14sp'
                    color: C['fg']
                    size_hint_y: None
                    height: dp(28)
                    text_size: self.width, None
                    halign: 'left'
                    valign: 'middle'

                BoxLayout:
                    orientation: 'horizontal'
                    size_hint_y: None
                    height: dp(2)
                    canvas:
                        Color:
                            rgba: C['separator']
                        Rectangle:
                            pos: self.pos
                            size: self.size

                Label:
                    id: final_label
                    text: '等待判定'
                    font_size: '26sp'
                    bold: True
                    color: C['fg_dim']
                    size_hint_y: None
                    height: dp(60)
                    text_size: self.width, None
                    halign: 'center'
                    valign: 'middle'
                    canvas.before:
                        Color:
                            rgba: C['bg_card']
                        RoundedRectangle:
                            pos: self.pos
                            size: self.size
                            radius: [dp(6)]
"""


# ============================================================
# 自定义组件
# ============================================================

class Card(BoxLayout):
    """圆角卡片容器"""
    pass


# ============================================================
# 根控件
# ============================================================

class AQLRoot(BoxLayout):
    """主界面根控件"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.engine = AQLEngine()
        self._calc_timer = None
        self._judging = False

    # ---------- 输入变化处理 ----------

    def on_level_change(self):
        self._schedule_calc()

    def on_lot_size_change(self):
        self._schedule_calc()

    def on_aql_change(self):
        self._schedule_calc()

    def _schedule_calc(self):
        if self._calc_timer:
            self._calc_timer.cancel()
        self._calc_timer = Clock.schedule_once(lambda dt: self._do_calculate(), 0.15)

    # ---------- 核心计算 ----------

    def _get_text(self, widget_id):
        w = self.ids.get(widget_id)
        return w.text if w else ''

    def _set_text(self, widget_id, text):
        w = self.ids.get(widget_id)
        if w:
            w.text = str(text)

    def _do_calculate(self):
        """自动计算标准值"""
        # 读取批量
        lot_str = self._get_text('lot_size_input').strip()
        if not lot_str:
            self._clear_standards()
            return

        try:
            lot_size = int(lot_str)
        except ValueError:
            self._clear_standards()
            return

        if lot_size < 2:
            self._clear_standards()
            self._set_text('code_label', '字码: 无效批量')
            return

        # 检验水平
        level = self._get_text('level_spinner')
        if level not in INSPECTION_LEVELS:
            return

        code_letter = self.engine.get_code_letter(lot_size, level)
        if not code_letter:
            self._clear_standards()
            return

        # 更新字码和样本数
        self._set_text('code_label', f'字码: {code_letter}')
        sample_size = CODE_SAMPLE_SIZES.get(code_letter, 0)
        self._set_text('sample_label', f'应抽: {sample_size}')

        # 填充默认实际抽样数（如果为空）
        actual_text = self._get_text('actual_sample_input').strip()
        if not actual_text:
            self._set_text('actual_sample_input', str(sample_size))

        # 计算各类缺陷标准值
        for key in DEFECT_KEYS:
            spinner_id = f'aql_{key}_spinner'
            ac_id = f'ac_{key}'
            re_id = f're_{key}'

            aql_str = self._get_text(spinner_id)
            aql_val = AQL_DISPLAY_MAP.get(aql_str, 0)
            plan = self.engine.get_sampling_plan(code_letter, aql_val)
            if plan:
                n, ac, re = plan
                self._set_text(ac_id, str(ac))
                self._set_text(re_id, str(re))
            else:
                self._set_text(ac_id, '—')
                self._set_text(re_id, '—')

    def _clear_standards(self):
        for key in DEFECT_KEYS:
            self._set_text(f'ac_{key}', '—')
            self._set_text(f're_{key}', '—')
        self._set_text('code_label', '字码: —')
        self._set_text('sample_label', '应抽: —')

    # ---------- 判定 ----------

    def on_judge(self):
        if self._judging:
            return
        self._judging = True

        btn = self.ids.get('judge_btn')
        if btn:
            btn.disabled = True
            btn.text = '判定中...'

        # 先确保计算完成
        self._do_calculate()

        # 小延迟后执行判定（让 UI 刷新）
        Clock.schedule_once(lambda dt: self._do_judgment(), 0.1)

    def _do_judgment(self):
        """执行实际判定逻辑"""
        # 获取应抽样本数
        sample_str = self._get_text('sample_label')
        try:
            standard_n = int(sample_str.split(':')[1].strip())
        except (ValueError, IndexError):
            standard_n = 0

        if standard_n <= 0:
            self._show_error('请先输入批量以获取标准抽样数')
            return

        # 实际抽样数
        actual_str = self._get_text('actual_sample_input').strip()
        try:
            actual_n = int(actual_str)
        except ValueError:
            actual_n = standard_n

        if actual_n <= 0:
            self._show_error('实际抽样数必须大于 0')
            return

        # 调整状态
        adjusted_standards = None
        status_msg = ''
        status_color = C['orange']

        if actual_n == standard_n:
            pass
        elif actual_n < standard_n:
            # 少于标准值 - 警告并调整
            adjusted_standards = self._lookup_adjusted(actual_n)
            status_msg = f'⚠ 实际({actual_n})<标准({standard_n})，已调整标准'
            status_color = C['orange']
        else:
            adjusted_standards = self._lookup_adjusted(actual_n)
            status_msg = f'ℹ 实际({actual_n})>标准({standard_n})，已按实调整'
            status_color = C['blue']

        adjust_label = self.ids.get('adjust_label')
        if adjust_label:
            adjust_label.text = status_msg
            adjust_label.color = status_color

        # 逐类判定
        all_pass = True
        results = []

        for key, category in zip(DEFECT_KEYS, DEFECT_CATEGORIES):
            # 读取缺陷数
            defect_str = self._get_text(f'defect_{key}')
            try:
                defect_count = int(defect_str)
            except ValueError:
                defect_count = 0

            # Ac/Re
            if adjusted_standards and key in adjusted_standards:
                ac_val = adjusted_standards[key]['ac']
                re_val = adjusted_standards[key]['re']
            else:
                try:
                    ac_val = int(self._get_text(f'ac_{key}'))
                    re_val = int(self._get_text(f're_{key}'))
                except ValueError:
                    ac_val, re_val = 0, 1

            # 判定
            if defect_count <= ac_val:
                verdict = 'accept'
                verdict_text = '✅ 接收'
                v_color = C['green']
            else:
                verdict = 'reject'
                verdict_text = '❌ 拒收'
                v_color = C['red']
                all_pass = False

            detail = f'{category}: 发现 {defect_count} 个 (Ac≤{ac_val}, Re≥{re_val})  {verdict_text}'

            result_label = self.ids.get(f'result_{key}')
            if result_label:
                result_label.text = detail
                result_label.color = v_color

            results.append({
                'category': category, 'key': key,
                'defect_count': defect_count,
                'ac': ac_val, 're': re_val,
                'verdict': verdict,
            })

        # 整批结论
        final_label = self.ids.get('final_label')
        if all_pass:
            final_label.text = '◉ 整 批 接 收 ◉'
            final_label.color = C['green']
            self._set_final_bg(final_label, C['green_bg'])
        else:
            final_label.text = '◉ 整 批 拒 收 ◉'
            final_label.color = C['red']
            self._set_final_bg(final_label, C['red_bg'])

        # 解锁按钮
        Clock.schedule_once(lambda dt: self._unlock_judge(btn_orig_text='  判  定  '), 0.3)

    def _set_final_bg(self, label, color):
        """设置结论背景并绑定尺寸更新"""
        label.canvas.before.clear()
        with label.canvas.before:
            Color(*color)
            RoundedRectangle(pos=label.pos, size=label.size, radius=[dp(6)])
        label.bind(pos=lambda i, v: self._redraw_final_bg(i),
                   size=lambda i, v: self._redraw_final_bg(i))

    def _redraw_final_bg(self, instance):
        """更新结论背景尺寸"""
        instance.canvas.before.clear()
        with instance.canvas.before:
            color = C['green_bg'] if '接收' in instance.text else C['red_bg']
            Color(*color)
            RoundedRectangle(pos=instance.pos, size=instance.size, radius=[dp(6)])

    def _lookup_adjusted(self, actual_n):
        """根据实际抽样数向下靠档调整标准"""
        actual_code = self.engine.get_code_letter_by_sample_size(actual_n)
        adjusted = {}
        for key in DEFECT_KEYS:
            spinner_id = f'aql_{key}_spinner'
            aql_str = self._get_text(spinner_id)
            aql_val = AQL_DISPLAY_MAP.get(aql_str, 0)
            plan = self.engine.get_sampling_plan(actual_code, aql_val)
            if plan:
                n, ac, re = plan
                adjusted[key] = {'ac': ac, 're': re}
            else:
                adjusted[key] = {'ac': 0, 're': 1}
        return adjusted

    def _show_error(self, msg):
        self._unlock_judge(msg)
        Clock.schedule_once(lambda dt: self._unlock_judge(btn_orig_text='  判  定  '), 1.5)

    def _unlock_judge(self, btn_orig_text='  判  定  '):
        self._judging = False
        btn = self.ids.get('judge_btn')
        if btn:
            btn.disabled = False
            btn.text = btn_orig_text


# ============================================================
# 应用入口
# ============================================================

class AQLMobileApp(App):
    """AQL 判定工具移动版"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.engine = AQLEngine()
        # 供 KV 引用的类属性
        self.default_level = 'II'
        self.inspection_levels = INSPECTION_LEVELS
        self.aql_display = AQL_DISPLAY

    def build(self):
        # 移动端键盘适配
        if platform in ('android', 'ios'):
            Window.softinput_mode = 'pan'
        else:
            # 桌面开发时模拟手机竖屏
            Window.size = (420, 820)

        self.icon = ''
        Builder.load_string(KV)  # 注册 KV 规则
        return AQLRoot()          # 创建根实例

    def on_start(self):
        """启动后自动计算"""
        root = self.root
        if root:
            Clock.schedule_once(lambda dt: root._do_calculate(), 0.3)


if __name__ == '__main__':
    AQLMobileApp().run()
