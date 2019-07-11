'''
Python gesture implementation [on Github](https://github.com/mikaelho/pythonista-gestures/blob/master/pygestures.py) for those situations where you cannot or do not want to use the ObjC gestures.

Simple usage example:
  
    import pygestures
    
    class MyTouchableView(pygestures.GestureView):
      
      def on_swipe(self, data):
        if data.direction in (data.UP, data.DOWN):
          print('I was swiped vertically')
          
Run the file as-is to play around with the gestures. (Green circles track your touches, crosshairs show the centroid, red circle reflects pan, pinch and rotation.)

![Demo](https://raw.githubusercontent.com/mikaelho/pythonista-gestures/master/pygestures.jpeg)

In your subclass, implement any or all the methods below to handle gestures. All methods get an information object with attributes including:

* `state` - one of BEGAN, CHANGED, ENDED
* `location` - location of the touch, or the centroid of all touches, as a scene.Point
* `no_of_touches` - use this if you want to filter for e.g. only taps with 2 fingers

Methods:
  
* `on_tap`
* `on_long_press`
* `on_swipe` - data includes `direction`, one of UP, DOWN, LEFT, RIGHT. Note that any active swipe gesture will delay the detection of pan, pinch and rotate, until it is clear that you are not swiping.
* `on_swipe_up`, `on_swipe_down`, `on_swipe_left`, `on_swipe_right`
* `on_edge_swipe`, `on_edge_swipe_up`, `on_edge_swipe_down`, `on_edge_swipe_left`, `on_edge_swipe_right`
* `on_pan` - data includes `translation`, the distance from the start of the gesture, as a scene.Point. For most purposes this is better than `location`, as it does not jump around if you add more fingers.
* `on_pinch` - data includes `scale`
* `on_rotate` - data includes `rotation` in degrees, negative for counterclockwise rotation

There are also `prev_translation`, `prev_scale` and `prev_rotation`, if you need them.

If it is more convenient to you, you can inherit GestureMixin together with ui.View or some other custom view class. In that case, if you want to use e.g. rotate, you need to make sure you have set `multitouch_enabled = True`.

There is also a `ZoomPanView`, with built-in support for panning, pinching and rotating the view and all the subviews. It's constructor has the following optional parameters:
  
  * `pan=True`, `zoom=True`, `rotate=False`
  * `min_scale`, `max_scale`
  * `min_rotation`, `max_rotation`
'''

import time, math
from types import SimpleNamespace
import ui
from scene import Point


class GestureTouch:
    def __init__(self, location):
        self._location = location
        self.prev_location = location
        self.start_location = location

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, value):
        self.prev_location = self._location
        self._location = value

    @property
    def distance_from_start(self):
        return abs(Point(*self.location) - Point(*self.start_location))


class GestureData:

    gestures = ('tap', 'long_press', 'swipe', 'swipe_up', 'swipe_left',
                'swipe_right', 'swipe_down', 'edge_swipe', 'edge_swipe_up',
                'edge_swipe_left', 'edge_swipe_right', 'edge_swipe_down',
                'pan', 'pinch', 'rotate')

    tap_threshold = 0.3  # seconds
    long_press_threshold = 0.5  # second
    move_threshold = 15  # pixels

    NOT_POSSIBLE = None
    CANCELLED = -2
    ENDED = -1
    POSSIBLE = 0
    BEGAN = 1
    CHANGED = 2
    FAILED = 3

    UP = 'up'
    DOWN = 'down'
    LEFT = 'left'
    RIGHT = 'right'

    def __init__(self, view):
        self.view = view

        self.gesture_states = {}
        self.reset(*self.gestures)

        self.touches = {}
        self.touches_in_order = []
        self.no_of_touches = 0
        self.state = None

        self.location = None
        self.prev_location = None

    def reset(self, *gestures):
        for gesture in gestures:
            self.gesture_states[gesture] = (self.POSSIBLE if hasattr(
                self.view, 'on_' + gesture) else self.NOT_POSSIBLE)
            if gesture == 'pan':
                self.start_translation = None
                self.translation = None
                self.prev_translation = None
            if gesture == 'pinch':
                self.start_pinch_distance = None
                self.pinch_distance = None
                self.prev_pinch_distance = None
                self.scale = None
                self.prev_scale = None
            if gesture == 'rotate':
                self.start_angle = None
                self.angle = None
                self.prev_angle = None
                self.rotation = None
                self.prev_rotation = None

    def is_possible(self, *gestures):
        return all((self.gesture_states[gesture] == self.POSSIBLE
                    for gesture in gestures))

    def is_active(self, *gestures):
        return all((self.gesture_states[gesture] in (self.POSSIBLE, self.BEGAN,
                                                     self.CHANGED)
                    for gesture in gestures))

    def has_begun(self, gesture):
        return self.gesture_states[gesture] == self.BEGAN

    def fail(self, *gestures):
        for gesture in gestures:
            self.gesture_states[gesture] = self.FAILED

    def none_possible(self, *gestures):
        return not any((self.gesture_states[gesture] == self.POSSIBLE
                        for gesture in gestures))

    def all_failed(self, *gestures):
        return all((self.gesture_states[gesture] == self.FAILED
                    for gesture in gestures))

    def check(self, *gestures):
        for gesture in gestures:
            if self.is_active(gesture):
                if self.is_possible(gesture):
                    self.begin(gesture)
                else:
                    self.change(gesture)

    def begin(self, gesture):
        self.gesture_states[gesture] = self.BEGAN
        self.state = self.BEGAN
        getattr(self.view, 'on_' + gesture)(self)

    def change(self, gesture):
        self.gesture_states[gesture] = self.CHANGED
        self.state = self.CHANGED
        getattr(self.view, 'on_' + gesture)(self)

    def end(self, gesture):
        self.gesture_states[gesture] = self.ENDED
        self.state = self.ENDED
        getattr(self.view, 'on_' + gesture)(self)

    def soft_end(self, gesture):
        self.end(gesture)
        self.reset(gesture)

    @property
    def began(self):
        return self.state == self.BEGAN

    @property
    def changed(self):
        return self.state == self.CHANGED

    @property
    def ended(self):
        return self.state == self.ENDED

    @property
    def out_of_business(self):
        return any((state is not None and state < self.POSSIBLE
                    for state in self.gesture_states.values()))

    def get_center_location(self):
        center_loc = Point(0, 0)
        for touch in self.touches.values():
            center_loc += Point(*touch.location)
        center_loc /= len(self.touches)
        return center_loc

    def get_pinch_distance(self):
        distance_vector = (self.touches_in_order[0].location -
                           self.touches_in_order[1].location)
        return abs(distance_vector)

    def get_angle(self, prev_angle=None):
        angle = self.degrees(self.touches_in_order[0].location -
                             self.touches_in_order[1].location)
        if prev_angle is not None and abs(prev_angle) > 90:
            if prev_angle > 0 and angle < 0:
                angle += 360
            if prev_angle < 0 and angle > 0:
                angle -= 360
        return angle

    def radians(self, vector):
        rad = math.atan2(vector.y, vector.x)
        return rad

    def degrees(self, vector):
        return math.degrees(self.radians(vector))


class GestureMixin():
    def touch_began(self, touch):

        if not hasattr(self, '_gestures') or len(self._gestures.touches) == 0:
            self._gestures = GestureData(self)
        g = self._gestures

        if g.out_of_business:
            return

        if len(g.touches) == 0:
            g.start_time = time.time()

        t = GestureTouch(touch.location)
        g.touches[touch.touch_id] = t
        g.touches_in_order.append(t)

        g.no_of_touches = max(g.no_of_touches, len(g.touches))

        g.prev_location = g.location
        g.location = g.get_center_location()

        x, y, w, h = self.bounds

        if touch.location.x > x + 20:
            g.fail('edge_swipe_right')
        if touch.location.x < x + w - 20:
            g.fail('edge_swipe_left')
        if touch.location.y > y + 20:
            g.fail('edge_swipe_down')
        if touch.location.y < y + h - 20:
            g.fail('edge_swipe_up')
        if g.all_failed('edge_swipe_up', 'edge_swipe_left', 'edge_swipe_right',
                        'edge_swipe_down'):
            g.fail('edge_swipe')

        if g.start_translation is None:
            g.start_translation = touch.location
        else:
            g.start_translation += g.location - g.prev_location

        if len(g.touches) >= 2:
            g.prev_pinch_distance = g.pinch_distance
            g.pinch_distance = g.get_pinch_distance()

            g.prev_angle = g.angle
            g.angle = g.get_angle(g.prev_angle)

            if g.start_pinch_distance is None:
                g.start_pinch_distance = g.pinch_distance
            else:
                g.start_pinch_distance += g.pinch_distance - g.prev_pinch_distance

            if g.start_angle is None:
                g.start_angle = g.angle
            else:
                g.start_angle += g.angle - g.prev_angle

    def touch_moved(self, touch):
        g = self._gestures
        if g.out_of_business:
            return

        t = g.touches[touch.touch_id]
        g.duration = time.time() - g.start_time
        t.location = touch.location
        g.prev_location = g.location
        g.location = g.get_center_location()
        g.prev_translation = g.translation
        g.translation = g.location - g.start_translation

        if t.distance_from_start > g.move_threshold:
            g.fail('tap', 'long_press')

        if g.duration > g.tap_threshold:
            g.fail(
                'tap',
                'swipe',
                'swipe_left',
                'swipe_right',
                'swipe_up',
                'swipe_down',
                'edge_swipe',
                'edge_swipe_up',
                'edge_swipe_left',
                'edge_swipe_right',
                'edge_swipe_down', )

        if g.is_possible('long_press') and g.duration > g.long_press_threshold:
            g.end('long_press')
            return

        if g.none_possible(
                'tap',
                'long_press',
                'swipe',
                'swipe_left',
                'swipe_right',
                'swipe_up',
                'swipe_down',
                'edge_swipe',
                'edge_swipe_up',
                'edge_swipe_left',
                'edge_swipe_right',
                'edge_swipe_down', ):
            g.check('pan')
            if len(g.touches) >= 2:

                g.prev_pinch_distance = g.pinch_distance
                g.pinch_distance = g.get_pinch_distance()
                g.prev_scale = g.scale
                g.scale = g.pinch_distance / g.start_pinch_distance
                g.check('pinch')

                g.prev_angle = g.angle
                g.angle = g.get_angle(g.prev_angle)
                g.prev_rotation = g.rotation
                g.rotation = g.angle - g.start_angle
                g.check('rotate')

    def touch_ended(self, touch):
        g = self._gestures

        del g.touches[touch.touch_id]
        if g.out_of_business:
            return

        if len(g.touches) > 0:
            g.prev_location = g.location
            g.location = g.get_center_location()
            if g.is_active('pan'):
                g.start_translation += g.location - g.prev_location

            g.prev_pinch_distance = g.pinch_distance
            g.pinch_distance = g.get_pinch_distance()
            if g.is_active('pinch'):
                if len(g.touches) > 1:
                    g.start_pinch_distance += g.pinch_distance - g.prev_pinch_distance
                else:
                    g.soft_end('pinch')

            g.prev_angle = g.angle
            g.angle = g.get_angle(g.prev_angle)
            if g.is_active('rotate'):
                if len(g.touches) > 1:
                    g.start_angle += g.angle - g.prev_angle
                else:
                    g.soft_end('rotate')

        if len(g.touches) == 0:
            g.end_time = time.time()
            g.duration = g.end_time - g.start_time

            if g.is_possible('tap'):
                g.end('tap')
                return

            delta = g.translation
            if delta is not None:
                if abs(delta.x) > abs(delta.y):
                    g.direction = g.RIGHT if delta.x > 0 else g.LEFT
                else:
                    g.direction = g.DOWN if delta.y > 0 else g.UP
                swiped = False
                gesture = 'edge_swipe_' + g.direction
                if g.is_possible(gesture):
                    g.end(gesture)
                    swiped = True
                else:
                    gesture = 'swipe_' + g.direction
                    if g.is_possible(gesture):
                        g.end(gesture)
                        swiped = True
                if g.is_possible('edge_swipe'):
                    g.end('edge_swipe')
                    swiped = True
                elif g.is_possible('swipe'):
                    g.end('swipe')
                    swiped = True
                if swiped:
                    return


class GestureView(ui.View, GestureMixin):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.multitouch_enabled = True


class TouchRelayMixin:
    def touch_began(self, touch):
        self.relay_touch(touch, 'touch_began')

    def touch_moved(self, touch):
        self.relay_touch(touch, 'touch_moved')

    def touch_ended(self, touch):
        self.relay_touch(touch, 'touch_ended')

    def relay_touch(self, touch, func_name):
        v = self.superview
        while v:
            f = getattr(v, func_name, None)
            if f:
                t = SimpleNamespace(
                    touch_id=touch.touch_id,
                    prev_location=ui.convert_point(touch.prev_location, self,
                                                   v),
                    location=ui.convert_point(touch.location, self, v),
                    phase=touch.phase,
                    timestamp=touch.timestamp)
                f(t)
                break
            v = self.superview


class TouchRelayView(ui.View, TouchRelayMixin):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.multitouch_enabled = True


class ZoomPanView(GestureView):
    def __init__(self,
                 pan=True,
                 zoom=True,
                 rotate=False,
                 min_scale=None,
                 max_scale=None,
                 min_rotation=None,
                 max_rotation=None,
                 **kwargs):
        self.pan = pan
        self.zoom = zoom
        self.rotate = rotate
        self.min_scale = min_scale
        self.max_scale = max_scale
        self.min_rotation = min_rotation
        self.max_rotation = max_rotation
        self.background_color = 'black'
        self.name = 'ZoomPanView'
        super().__init__(**kwargs)
        self.zoomer = TouchRelayView(frame=self.bounds, flex='WH')
        super().add_subview(self.zoomer)
        self.zoomer.objc_instance.setClipsToBounds_(False)

        self.scale = 1
        self.rotation = 0

    def add_subview(self, view):
        self.zoomer.add_subview(view)

    def on_pan(self, data):
        if not self.pan: return
        # Use translation instead of location to
        # not be sensitive to additional touches
        if data.changed:
            self.zoomer.center += data.translation - data.prev_translation

    def on_pinch(self, data):
        if not self.zoom: return
        if data.began:
            self.start_scale = self.scale
        if data.changed:
            focus_pos = ui.convert_point(data.location, self, self.zoomer)
            self.scale = self.start_scale * data.scale
            if self.min_scale is not None:
                self.scale = max(self.scale, self.min_scale)
            if self.max_scale is not None:
                self.scale = min(self.scale, self.max_scale)
            #self.zoomer.transform = ui.Transform.scale(*(self.scale,)*2)
            self._set_transforms()
            focus_location = ui.convert_point(focus_pos, self.zoomer, self)
            self.zoomer.center -= focus_location - data.location

    def on_rotate(self, data):
        if not self.rotate: return
        if data.began:
            self.start_rotation = self.rotation
        if data.changed:
            focus_pos = ui.convert_point(data.location, self, self.zoomer)
            self.rotation = self.start_rotation + data.rotation
            if self.min_rotation is not None:
                self.rotation = max(self.rotation, self.min_rotation)
            if self.max_rotation is not None:
                self.rotation = min(self.rotation, self.max_rotation)
            #self.zoomer.transform = ui.Transform.rotation(math.radians(self.rotation))
            self._set_transforms()
            focus_location = ui.convert_point(focus_pos, self.zoomer, self)
            self.zoomer.center -= focus_location - data.location

    def reset(self):
        self.scale = 1
        self.rotation = 0
        self._set_transforms()
        self.zoomer.center = self.bounds.center()

    def _set_transforms(self):
        self.zoomer.transform = ui.Transform.scale(*(self.scale, ) * 2).concat(
            ui.Transform.rotation(math.radians(self.rotation)))


if __name__ == '__main__':

    import copy

    class TestView(GestureView):
        def __init__(self, **kwargs):
            self.background_color = 'black'
            super().__init__(**kwargs)
            self.data = None
            self.labels = {}
            self.translate_track = []

            self.hint = ui.Label(
                text='Play with gestures or swipe from this edge',
                alignment=ui.ALIGN_CENTER,
                text_color=(1, 1, 1, 0.5),
                flex='TLB')
            self.hint.size_to_fit()
            self.hint.center = (self.width - self.hint.height, self.height / 2)
            self.hint.transform = ui.Transform.rotation(math.radians(-90))
            self.add_subview(self.hint)

            self.zpd = ZoomPanDemo(frame=self.bounds, flex='WH')
            self.add_subview(self.zpd)

        def layout(self):
            self.zpd.x = self.width
            self.zpd.bring_to_front()

        def create_labels(self):
            labels = ('Tap', 'Long press', 'Swipe', 'Edge swipe', 'Pan',
                      'Pinch', 'Rotate')
            for i, label in enumerate(labels):
                l = ui.Label(
                    name=label,
                    x=0,
                    flex='TBRW',
                    alignment=ui.ALIGN_CENTER,
                    number_of_lines=0,
                    text_color=(1, 1, 1, 0.5))
                l.y = i * self.height / (len(labels) + 1)
                l.width = self.width
                self.add_subview(l)

        def show_status(self, data, gesture_name, data_string=None):
            l = self[gesture_name]
            if data_string is None:
                data_string = f'Loc: {data.location}, Touches: {data.no_of_touches}'
            l.text = f'{gesture_name}\n{data_string}'
            self.data = data
            self.set_needs_display()

        def on_edge_swipe_left(self, data):
            def anim():
                self.zpd.x = 0

            ui.animate(anim, 0.2)

        def on_tap(self, data):
            self.show_status(data, 'Tap')

        def on_long_press(self, data):
            self.show_status(data, 'Long press')

        def on_swipe(self, data):
            self.show_status(data, 'Swipe', data.direction)

        def on_edge_swipe(self, data):
            self.show_status(data, 'Edge swipe', data.direction)

        def on_pan(self, data):
            self.show_status(data, 'Pan', f'Translation: {data.translation}')
            if data.began:
                self.translate_track = [data.translation]
            else:
                self.translate_track.append(data.translation)
            self.translate_track = self.translate_track[-20:]

        def on_pinch(self, data):
            self.show_status(data, 'Pinch', f'Scale: {data.scale}')

        def on_rotate(self, data):
            self.show_status(data, 'Rotate', f'Rotation: {data.rotation:.2f}')

        def on_debug(self, data):
            self.data = copy.deepcopy(data)
            self.set_needs_display()

        def draw(self):
            if self.data is None or len(self.data.touches) == 0:
                return
            c = self.bounds.center()
            if self.data.translation is not None:
                c += self.data.translation
            for touch in self.data.touches.values():
                (x, y) = touch.location
                p = ui.Path.oval(x - 40, y - 40, 80, 80)
                ui.set_color('white')
                p.stroke()
                ui.set_color((0, 1, 0, 0.5))
                p.fill()
            (x, y) = self.data.location
            p = ui.Path()
            p.move_to(x - 40, y)
            p.line_to(x + 40, y)
            p.move_to(x, y - 40)
            p.line_to(x, y + 40)
            ui.set_color('darkgreen')
            p.stroke()

            if len(self.translate_track) > 1:
                p = ui.Path()
                p.move_to(*(self.bounds.center() + self.translate_track[0]))
                for pos in self.translate_track[1:]:
                    p.line_to(*(self.bounds.center() + pos))
                ui.set_color((1, 0, 0, 0.5))
                p.stroke()

            if self.data.translation is not None:
                radius = 40 * self.data.scale if self.data.scale is not None else 1
                p = ui.Path.oval(c.x - radius, c.y - radius, 2 * radius,
                                 2 * radius)
                ui.set_color('red')
                p.stroke()
                if self.data.rotation is not None:
                    p = ui.Path()
                    p.move_to(c.x, c.y)
                    p.line_to(c.x + radius, c.y)
                    clockwise = self.data.rotation >= 0
                    p.add_arc(c.x, c.y, radius, 0,
                              math.radians(self.data.rotation), clockwise)
                    p.line_to(c.x, c.y)
                    ui.set_color((1, 0, 0, 0.5))
                    p.fill()
                    ui.set_color('red')
                    p.stroke()

    class ZoomPanDemo(ZoomPanView):
        def __init__(self, **kwargs):
            super().__init__(
                rotate=True,
                min_scale=.5,
                max_scale=2,
                min_rotation=-45,
                max_rotation=45,
                **kwargs)

            w, h = self.bounds[2], self.bounds[3]
            iv = ui.ImageView(
                image=ui.Image('test:Peppers'),
                flex='WHRTLB',
                frame=(w / 4, h / 4, w / 2, h / 2))
            iv.content_mode = ui.CONTENT_SCALE_ASPECT_FILL
            self.add_subview(iv)

            def action(sender):
                self.reset()

            b = ui.Button(
                title='Reset',
                tint_color='white',
                background_color='blue',
                action=action,
                flex='RTLB')
            b.size_to_fit()
            b.width += 16
            b.center = self.bounds.center()
            self.add_subview(b)

            self.hint = ui.Label(
                text='Pan, zoom, rotate'
                '\nSwipe from left to return',
                text_color=(1, 1, 1, 0.5),
                alignment=ui.ALIGN_CENTER,
                flex='LBR')
            self.hint.size_to_fit()
            self.hint.number_of_lines = 0
            self.hint.size_to_fit()
            self.hint.center = (self.width / 2, self.hint.height)
            self.add_subview(self.hint)

        def on_edge_swipe_right(self, data):
            def anim():
                self.x = ui.get_screen_size()[0]

            ui.animate(anim, 0.2)

    v = TestView()
    v.present(title_bar_color='black')
    v.create_labels()

