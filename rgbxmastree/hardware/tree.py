from __future__ import annotations

from gpiozero import SPIDevice, SourceMixin
from colorzero import Color
from statistics import mean


class Pixel:
    def __init__(self, parent: "RGBXmasTree", index: int):
        self.parent = parent
        self.index = index

    @property
    def value(self):
        return self.parent.value[self.index]

    @value.setter
    def value(self, value):
        r, g, b = value
        self.parent._set_pixel_value(self.index, (r, g, b))

    @property
    def color(self):
        return Color(*self.value)

    @color.setter
    def color(self, c):
        r, g, b = c
        self.value = (r, g, b)

    def on(self):
        self.value = (1, 1, 1)

    def off(self):
        self.value = (0, 0, 0)


class RGBXmasTree(SourceMixin, SPIDevice):
    """
    Low-level driver for the 3D RGB Xmas Tree.

    This is derived from the original `tree.py` example driver.
    """

    def __init__(
        self,
        pixels: int = 25,
        brightness: float = 0.5,
        mosi_pin: int = 12,
        clock_pin: int = 25,
        *args,
        **kwargs,
    ):
        super().__init__(mosi_pin=mosi_pin, clock_pin=clock_pin, *args, **kwargs)
        if pixels != 25:
            # The physical mapping for this product is 25 pixels (24 body + 1 star).
            # We keep this configurable for testing/mocking but discourage other values.
            pass

        self._all = [Pixel(parent=self, index=i) for i in range(pixels)]
        self._value: list[tuple[float, float, float]] = [(0.0, 0.0, 0.0)] * pixels

        # Persistent SPI frame buffer:
        # start_frame(4 bytes) + 25 * [brightness, blue, green, red] + end_frame(5 bytes)
        self._frame_header_len = 4
        self._frame_tail_len = 5
        self._spi_frame: list[int] = (
            [0] * self._frame_header_len
            + [0] * (pixels * 4)
            + [0] * self._frame_tail_len
        )

        # Batching control (default keeps current immediate update behavior)
        self.auto_show: bool = True

        # Brightness: keep backwards-compatible float API via `brightness`,
        # but implement two independent APA102 brightness channels (ints 0..31).
        # Defaults: body brightness from the legacy float, and star matches body.
        body_bits = self._brightness_arg_to_bits(brightness)
        self._body_brightness_bits: int = body_bits
        self._star_brightness_bits: int = body_bits

        # Initialize the frame to "off" with correct brightness bytes, then display.
        self._apply_brightness_bytes()
        self.off()

    def __len__(self):
        return len(self._all)

    def __getitem__(self, index):
        # Tuple indexing: tree[level, branch]
        if isinstance(index, tuple) and len(index) == 2:
            level, branch = index
            mapped = self._index_map[level][branch]
            return self._all[mapped]
        return self._all[index]

    def __iter__(self):
        return iter(self._all)

    # --- SPI frame helpers ---

    @staticmethod
    def _clamp_byte(x: float) -> int:
        # Accept floats in 0..1 (common), but clamp defensively.
        if x <= 0.0:
            return 0
        if x >= 1.0:
            return 255
        return int(255 * x)

    @staticmethod
    def _pack_brightness(bits: int) -> int:
        # APA102 per-LED "global brightness" byte: 0b111xxxxx
        return 0b11100000 | (int(bits) & 0b11111)

    @staticmethod
    def _unpack_brightness(packed: int) -> int:
        return int(packed) & 0b11111

    def _pixel_offset(self, index: int) -> int:
        return self._frame_header_len + (index * 4)

    def _apply_brightness_bytes(self) -> None:
        """
        Apply current body/star brightness bytes into the SPI frame.
        Does not call show().
        """
        body_byte = self._pack_brightness(self._body_brightness_bits)
        star_byte = self._pack_brightness(self._star_brightness_bits)
        for i in range(len(self._all)):
            s = self._pixel_offset(i)
            self._spi_frame[s] = star_byte if i == self._star_index else body_byte

    def show(self) -> None:
        """Send the current SPI frame down the bus."""
        self._spi.transfer(self._spi_frame)

    def _set_pixel_value(self, index: int, rgb: tuple[float, float, float]) -> None:
        r, g, b = rgb
        self._value[index] = (float(r), float(g), float(b))

        s = self._pixel_offset(index)
        # s+0 is brightness byte (already set by _apply_brightness_bytes)
        self._spi_frame[s + 1] = self._clamp_byte(b)
        self._spi_frame[s + 2] = self._clamp_byte(g)
        self._spi_frame[s + 3] = self._clamp_byte(r)

        if self.auto_show:
            self.show()

    @property
    def color(self):
        average_r = mean(pixel.color[0] for pixel in self)
        average_g = mean(pixel.color[1] for pixel in self)
        average_b = mean(pixel.color[2] for pixel in self)
        return Color(average_r, average_g, average_b)

    @color.setter
    def color(self, c):
        r, g, b = c
        self.value = ((r, g, b),) * len(self)

    @property
    def brightness(self):
        # Backwards-compatible float brightness view (0.0..1.0) for the body.
        return self._body_brightness_bits / 31.0

    @brightness.setter
    def brightness(self, brightness: float):
        # Accept legacy float 0..1 and map to APA102 0..31 bits.
        self.body_brightness = self._brightness_arg_to_bits(brightness)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        # Bulk set: update the cached view and in-place SPI frame payload.
        seq = list(value)
        if len(seq) != len(self._all):
            raise ValueError(f"value must have length {len(self._all)}")

        # Temporarily suppress auto_show and show once at the end
        prev = self.auto_show
        self.auto_show = False
        try:
            for i, (r, g, b) in enumerate(seq):
                self._set_pixel_value(i, (r, g, b))
        finally:
            self.auto_show = prev

        if self.auto_show:
            self.show()

    def on(self):
        self.value = ((1, 1, 1),) * len(self)

    def off(self):
        self.value = ((0, 0, 0),) * len(self)

    # --- physical mapping / convenience ---

    # level/branch mapping (3 x 8). Oriented with the Raspberry Pi facing you.
    _index_map: tuple[tuple[int, ...], ...] = (
        (24, 19, 7, 0, 16, 15, 6, 12),  # level 0
        (23, 20, 8, 1, 17, 14, 5, 11),  # level 1
        (22, 21, 9, 2, 18, 13, 4, 10),  # level 2
    )
    _star_index: int = 3

    @property
    def star(self) -> Pixel:
        return self._all[self._star_index]

    # --- brightness controls (two-channel) ---

    @staticmethod
    def _brightness_arg_to_bits(val: float | int) -> int:
        if isinstance(val, bool):
            # Avoid treating bools as ints for brightness.
            raise TypeError("brightness must be float 0..1 or int 0..31")
        if isinstance(val, int):
            bits = val
        else:
            # Legacy float in 0..1 range
            bits = int(float(val) * 31)
        return max(0, min(31, int(bits)))

    @property
    def body_brightness(self) -> int:
        return int(self._body_brightness_bits)

    @body_brightness.setter
    def body_brightness(self, bits: int) -> None:
        self._body_brightness_bits = self._brightness_arg_to_bits(bits)
        self._apply_brightness_bytes()
        if self.auto_show:
            self.show()

    @property
    def star_brightness(self) -> int:
        return int(self._star_brightness_bits)

    @star_brightness.setter
    def star_brightness(self, bits: int) -> None:
        self._star_brightness_bits = self._brightness_arg_to_bits(bits)
        self._apply_brightness_bytes()
        if self.auto_show:
            self.show()


